"""
track_mac.py (웹소켓 + 내장 트래커 버전)

이 스크립트는 웹소켓 서버에 연결하여 'track' 명령을 대기합니다.
명령을 수신하면, 별도의 프로세스를 실행하는 대신 이 스크립트 내에서
직접 BLE 스캔을 시작하고 rssi_tracker.py 알고리즘을 구동하여 추적을 수행합니다.
"""
#윈도우 시연용

import asyncio
import websockets
import json
import time
from typing import Optional

from bleak import BleakScanner, BleakError
from drone.main.rssi_tracker import RSSITracker, Config, ControlCmd

# --- 설정 ---
SERVER_URI = "ws://52.79.236.231:8765"
DRONE_ID = "drone01"

# --- 전역 변수 ---
# 현재 실행 중인 추적 작업을 관리하기 위한 변수
tracking_task = None

# --- 추적 로직 (원래 track_mac.py의 핵심 기능) ---

def norm_mac(m: str) -> str:
    """MAC 주소 형식을 표준화합니다 (예: 'AA-BB-CC' -> 'AA:BB:CC')."""
    return m.replace("-", ":").upper()

class MacRssiFeeder:
    """BLE 광고 콜백을 통해 특정 MAC의 최신 RSSI 값을 유지하는 클래스."""
    def __init__(self, target_mac: str):
        self.target_mac = norm_mac(target_mac)
        self._last_rssi: Optional[int] = None
        self._last_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def on_detect(self, device, adv_data):
        if norm_mac(getattr(device, "address", "")) != self.target_mac:
            return
        rssi = getattr(adv_data, "rssi", None)
        if rssi is None:
            return
        async with self._lock:
            self._last_rssi = int(rssi)
            self._last_time = time.time()

    async def take_latest(self) -> Optional[int]:
        async with self._lock:
            return self._last_rssi


async def tracker_loop(target_mac: str):
    """
    지정된 MAC 주소를 추적하는 실제 작업을 수행하는 워커 함수.
    이 함수는 내장된 RSSITracker 알고리즘을 직접 사용합니다.
    """
    print(f"✅ 추적 루프 시작: 대상 MAC = {target_mac}")
    feeder = MacRssiFeeder(target_mac)
    
    # 추적 알고리즘 설정
    cfg = Config(
        ema_alpha=0.25, der_alpha=0.35, scan_period=0.3,
        found_threshold_db=-65.0, close_threshold_db=-40.0,
        lost_timeout_s=3.0
    )
    tracker = RSSITracker(cfg)

    scanner = BleakScanner(detection_callback=feeder.on_detect)
    
    print("📡 BLE 스캔 시작...")
    await scanner.start()
    try:
        while True:
            rssi = await feeder.take_latest()
            cmd: ControlCmd = tracker.step(rssi, now=time.time())
            
            # 콘솔에 현재 상태 및 제어 명령 출력
            print(f"RSSI={str(rssi):>4} dBm | 상태={tracker.state.name:<10} "
                  f"| 전진={cmd.forward:>5.2f} m/s | 회전={cmd.yaw_rate:>5.2f} rad/s | {cmd.note}")
            
            await asyncio.sleep(cfg.scan_period)
            
    except asyncio.CancelledError:
        print("🟡 추적 루프가 외부 명령에 의해 취소되었습니다.")
    except Exception as e:
        print(f"❌ 추적 루프에서 오류 발생: {e}")
    finally:
        print("🧹 정리 작업 시작...")
        await scanner.stop()
        print("...BLE 스캐너 중지됨.")
        print("🛑 추적 루프가 완전히 중단되었습니다.")


# --- 통신 로직 ---

async def main_loop():
    """
    메인 루프: 서버에 연결하고, 메시지를 수신하여 추적 작업을 관리합니다.
    """
    global tracking_task
    while True:
        try:
            async with websockets.connect(SERVER_URI) as websocket:
                print(f"✅ 서버({SERVER_URI})에 연결되었습니다.")
                await websocket.send(json.dumps({"type": "drone_id", "drone_id": DRONE_ID}))

                print("📡 주변 BLE 장치 스캔 중 (5초)...")
                try:
                    devices = await BleakScanner.discover(timeout=5.0)
                    for d in devices:
                        await websocket.send(json.dumps({
                            "type": "ble", "mac": d.address, "name": d.name or "Unknown"
                        }))
                    print(f"📡 BLE 스캔 완료. {len(devices)}개의 장치를 서버에 전송했습니다.")
                except BleakError as e:
                    print(f"❌ 초기 BLE 스캔 실패: {e}. 스캐너를 사용할 수 없는 환경일 수 있습니다.")
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get("type") == "track":
                            target_mac = data["mac"]
                            print(f"🎯 서버로부터 추적 명령 수신: {target_mac}")
                            
                            if tracking_task and not tracking_task.done():
                                print("...기존 추적 작업을 중단합니다...")
                                tracking_task.cancel()
                                await tracking_task
                            
                            # tracking.py 프로세스 대신, 내장된 tracker_loop 함수를 직접 실행
                            tracking_task = asyncio.create_task(tracker_loop(target_mac))

                    except Exception as e:
                        print(f"❌ 메시지 처리 중 오류: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            print("🔌 서버와 연결이 끊겼습니다. 5초 후 재연결을 시도합니다.")
        except ConnectionRefusedError:
            print("❌ 서버에 연결할 수 없습니다. 5초 후 재연결을 시도합니다.")
        except Exception as e:
            print(f"❌ 예기치 않은 오류 발생: {e}. 5초 후 재연결을 시도합니다.")
        
        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
