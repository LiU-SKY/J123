# rssi_tracker.py
# 알고리즘 파일
"""
Windows에서 테스트 가능한 RSSI 추적 프로토타입 (알고리즘만).

- 드론 제어는 "제어 출력"(전진 속도, 요잉 속도)으로 추상화됩니다.
- 시리얼/MAVLink 코드는 의도적으로 실행되지 않으며, 비계(scaffolding) 클래스가 제공되고 주석 처리됩니다.
- 전략: SEARCH (탐색) + APPROACH (접근, dRSSI/dt 기반) + HOLD (유지) + LOST (손실).
- 단일 안테나, GPS/앵커 없음.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Deque, Tuple
from collections import deque
import time

# ---------------------------- 필터 및 헬퍼 클래스 ----------------------------

class EMA:
    """지수이동평균(Exponential Moving Average) 필터."""
    def __init__(self, alpha: float, init: Optional[float] = None):
        self.alpha = alpha  # 평활 계수 (0 < alpha <= 1)
        self.value = init   # 필터의 현재 값

    def update(self, x: float) -> float:
        """새로운 값 x로 필터를 업데이트합니다."""
        if self.value is None:
            self.value = x
        else:
            # EMA 공식: 새로운 값 = alpha * 현재 입력 + (1 - alpha) * 이전 값
            self.value = self.alpha * x + (1 - self.alpha) * self.value
        return self.value

@dataclass
class ControlCmd:
    """드론에 보낼 제어 명령을 나타내는 데이터 클래스."""
    forward: float  # 전진 속도 (m/s, 부호 있음)
    yaw_rate: float # 요잉(회전) 속도 (rad/s, 부호 있음)
    note: str = ""  # 디버깅을 위한 메모

class State(Enum):
    """추적기의 현재 상태를 나타내는 열거형."""
    SEARCH = auto()     # 목표물을 탐색 중
    APPROACH = auto()   # 목표물에 접근 중
    HOLD = auto()       # 목표물 근처에서 위치 유지 중
    LOST = auto()       # 목표물 신호를 잃음

@dataclass
class Config:
    """추적 알고리즘의 설정을 위한 데이터 클래스."""
    ema_alpha: float = 0.2              # RSSI 값에 대한 EMA 필터의 alpha 값
    der_alpha: float = 0.3              # RSSI 변화율(derivative)에 대한 EMA 필터의 alpha 값
    scan_period: float = 0.2            # 제어 루프 주기 (초)
    deadband_db: float = 2.0            # 무시할 작은 RSSI 변화의 크기 (dB)
    found_threshold_db: float = -60.0   # 이 값보다 강한 RSSI를 감지하면 목표물을 '찾음'으로 간주
    close_threshold_db: float = -30.0   # 이 값보다 강한 RSSI를 감지하면 '매우 가까움'으로 간주하여 HOLD 상태로 전환
    lost_timeout_s: float = 2.0         # 이 시간(초) 동안 패킷 수신이 없으면 LOST 상태로 전환
    approach_speed: float = 0.8         # 접근 시 기본 전진 속도 (m/s)
    min_speed: float = 0.2              # 최소 속도 제한
    max_speed: float = 1.5              # 최대 속도 제한
    yaw_sweep_rate: float = 0.8         # SEARCH 상태에서 좌우로 회전하는 속도 (rad/s)
    yaw_nudge_rate: float = 0.3         # APPROACH 상태에서 미세하게 방향을 수정하는 회전 속도
    der_gain: float = 6.0               # RSSI 변화율이 속도에 미치는 영향의 크기 (단위: ~dB/s)
    probe_window: int = 10              # 변화율 계산을 위해 기억할 샘플의 수
    hold_hover_speed: float = 0.0       # HOLD 상태에서의 전진 속도 (호버링)

class RSSITracker:
    """RSSI 신호를 기반으로 목표물을 추적하는 메인 클래스."""
    def __init__(self, cfg: Config = Config()):
        self.cfg = cfg
        self.state = State.SEARCH  # 초기 상태는 SEARCH
        self.rssi_ema = EMA(cfg.ema_alpha)
        self.der_ema = EMA(cfg.der_alpha)
        self.last_rx_time: Optional[float] = None  # 마지막으로 패킷을 수신한 시간
        self.probe_buf: Deque[Tuple[float, float]] = deque(maxlen=cfg.probe_window)  # (시간, rssi) 저장 버퍼
        self._yaw_sign = 1.0  # 탐색 시 회전 방향을 바꾸기 위한 변수

    def _update_signal(self, rssi_raw: Optional[float], now: float) -> Tuple[Optional[float], Optional[float]]:
        """신호 값을 업데이트하고, 평활화된 RSSI와 그 변화율을 반환합니다."""
        if rssi_raw is None:
            # 이번 루프에서 패킷 수신이 없는 경우
            if self.last_rx_time is not None and (now - self.last_rx_time) > self.cfg.lost_timeout_s:
                self.state = State.LOST  # 타임아웃되면 LOST 상태로 전환
            return self.rssi_ema.value, self.der_ema.value

        # 패킷을 수신한 경우
        self.last_rx_time = now
        rssi_s = self.rssi_ema.update(rssi_raw)  # RSSI 값 평활화

        # 이전 샘플과의 시간 차이를 이용한 변화율(dRSSI/dt) 추정
        if self.probe_buf:
            t_prev, r_prev = self.probe_buf[-1]
            dt = max(1e-3, now - t_prev)  # 0으로 나누는 것을 방지
            der = (rssi_s - r_prev) / dt
            der_s = self.der_ema.update(der)  # 변화율 값 평활화
        else:
            der_s = self.der_ema.update(0.0)

        self.probe_buf.append((now, rssi_s))  # 현재 값을 버퍼에 추가
        return rssi_s, der_s

    def _decide_state(self, rssi_s: Optional[float]) -> None:
        """평활화된 RSSI 값을 기반으로 현재 상태를 결정합니다."""
        if rssi_s is None:
            # 신호가 없으면 현재 상태 유지 (LOST 상태는 타임아웃으로 처리)
            return
        if rssi_s >= self.cfg.close_threshold_db:
            self.state = State.HOLD  # 매우 가까우면 HOLD
        elif rssi_s >= self.cfg.found_threshold_db:
            self.state = State.APPROACH  # 찾았으면 APPROACH
        else:
            # 신호가 약하면 이전 상태에 따라 SEARCH 또는 APPROACH 유지
            if self.state not in (State.APPROACH, State.HOLD):
                self.state = State.SEARCH

    def _cmd_search(self, now: float) -> ControlCmd:
        """SEARCH 상태일 때의 제어 명령을 생성합니다."""
        # 작은 전진과 함께 좌우로 회전하며 신호 탐색
        # 약 1.5초마다 회전 방향을 바꿔 양쪽을 모두 탐색
        if int(now * (1/1.5)) % 2 == 0:
            self._yaw_sign = 1.0
        else:
            self._yaw_sign = -1.0

        yaw = self._yaw_sign * self.cfg.yaw_sweep_rate
        forward = 0.3  # 느린 속도로 전진
        return ControlCmd(forward, yaw, note="SEARCH:sweep")

    def _cmd_approach(self, rssi_s: float, der_s: Optional[float]) -> ControlCmd:
        """APPROACH 상태일 때의 제어 명령을 생성합니다."""
        # 경사 상승법: RSSI 변화율에 따라 속도를 조절하고, RSSI가 계속 증가하도록 방향을 미세 조정
        der_s = der_s or 0.0

        # 변화율에 데드밴드를 적용하여 작은 변화에 의한 떨림 방지
        if abs(der_s) < 0.05:
            der_s_eff = 0.0
        else:
            der_s_eff = der_s

        base = self.cfg.approach_speed
        v = base + self.cfg.der_gain * der_s_eff  # 변화율에 따라 속도 조절
        v = max(self.cfg.min_speed, min(self.cfg.max_speed, v))  # 속도 제한

        # 방향 수정: 변화율이 음수이면 방향을 약간 틀어줌
        yaw = 0.0
        if der_s_eff < 0:
            yaw = self.cfg.yaw_nudge_rate * (-1 if self._yaw_sign > 0 else 1)
        elif der_s_eff > 0:
            # 변화율이 양수일 때도 약간의 방향 조정을 통해 최적 경로 탐색
            yaw = self.cfg.yaw_nudge_rate * (1 if self._yaw_sign > 0 else -1)

        return ControlCmd(v, yaw, note=f"APPROACH:der={der_s:.3f}")

    def _cmd_hold(self) -> ControlCmd:
        """HOLD 상태일 때의 제어 명령을 생성합니다."""
        return ControlCmd(self.cfg.hold_hover_speed, 0.0, note="HOLD")

    def _cmd_lost(self) -> ControlCmd:
        """LOST 상태일 때의 제어 명령을 생성합니다."""
        # 다시 탐색을 시작하되, 더 넓은 범위로 회전하여 신호를 다시 찾음
        self.state = State.SEARCH
        return ControlCmd(0.2, self.cfg.yaw_sweep_rate * 1.2, note="LOST->SEARCH")

    def step(self, rssi_raw: Optional[float], now: Optional[float] = None) -> ControlCmd:
        """한 번의 제어 사이클을 실행합니다.
        :param rssi_raw: 최신 RSSI 값 (dBm, 음수). None이면 이번 사이클에 패킷 없음.
        :param now: 타임스탬프 (초). None이면 time.time() 사용.
        """
        now = now if now is not None else time.time()
        rssi_s, der_s = self._update_signal(rssi_raw, now)
        self._decide_state(rssi_s)

        if self.state == State.SEARCH:
            return self._cmd_search(now)
        if self.state == State.APPROACH and rssi_s is not None:
            return self._cmd_approach(rssi_s, der_s)
        if self.state == State.HOLD:
            return self._cmd_hold()
        if self.state == State.LOST:
            return self._cmd_lost()
        # 예외 상황 처리
        return ControlCmd(0.0, 0.0, note="IDLE")

# ---------------------- 시리얼 통신 비계 (주석 처리됨) ----------------------

class SerialController:
    """
    드론 시리얼 제어를 위한 플레이스홀더 클래스. Windows 테스트에서는 실행하지 마세요.
    드론에 통합할 때, `send()` 메서드의 내용을 실제 시리얼/MAVLink 코드로 교체하세요.
    """
    def __init__(self, port: str = "/dev/ttyACM0", baud: int = 57600):
        self.port = port
        self.baud = baud
        # 예시 (주석 처리됨):
        # import serial
        # self.ser = serial.Serial(port, baud, timeout=0.1)

    def send(self, cmd: ControlCmd):
        # 예시 매핑 (주석 처리됨):
        # forward_to_pwm = int(1500 + 400 * cmd.forward)  # 속도를 PWM 신호로 변환
        # yaw_to_pwm     = int(1500 + 200 * cmd.yaw_rate) # 요잉 속도를 PWM 신호로 변환
        # packet = f"{forward_to_pwm},{yaw_to_pwm}\n".encode()
        # self.ser.write(packet)
        # 현재는 Windows 테스트를 위해 아무 작업도 하지 않음.
        pass