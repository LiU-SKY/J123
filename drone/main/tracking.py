import sys
import time
import asyncio

# rssi_tracker.py에서 핵심 추적 알고리즘을 가져옵니다.
from rssi_tracker import RSSITracker, Config, ControlCmd

# ============ 설정 ============ #
# 실제 드론과 통신하기 위한 시리얼 포트 정보 (현재는 사용되지 않음)
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 57600

# ============ 전역 변수 ============ #
# 시리얼 포트 객체 (현재는 사용되지 않음)
drone_serial = None

# ============ 드론 연결 (시뮬레이션용) ============ #
def connect_to_drone():
    """
    실제 드론과의 시리얼 연결을 시도하는 함수
    현재는 시뮬레이션을 위해 비활성화
    """
    global drone_serial
    try:
        # drone_serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("✅ (시뮬레이션) 드론 시리얼 포트가 준비되었습니다.")
    except Exception as e:
        print(f"❌ (시뮬레이션) 드론 연결 실패: {e}")

# ============ 드론 명령 전송 (시뮬레이션용) ============ #
def send_drone_command(cmd: ControlCmd):
    """
    계산된 제어 명령을 실제 드론에 전송하는 함수.
    현재는 명령 내용을 화면에 출력
    """
    # 여기에 forward와 yaw_rate 값을 실제 드론이 이해할 수 있는
    # MAVLink나 PWM 신호로 변환하는 코드가 들어갑니다.
    # 예: mavlink_msg = vehicle.message_factory.set_position_target_local_ned_encode(...)
    
    # --- 실제 드론 제어 코드 (현재 주석 처리) ---
    # if drone_serial and drone_serial.is_open:
    #     # 예시: "FORWARD:0.5,YAW:0.2" 형태의 문자열 전송
    #     command_str = f"FORWARD:{cmd.forward},YAW:{cmd.yaw_rate}
    #     drone_serial.write(command_str.encode())
    # -----------------------------------------
    
    # 현재는 화면에 제어 명령을 출력하는 것으로 대체합니다.
    print(f"🛸 드론 명령: [상태: {cmd.note:<20}] | [전진: {cmd.forward:5.2f} m/s] | [회전: {cmd.yaw_rate:5.2f} rad/s]")


# ============ 메인 로직 ============ #
async def main():
    if len(sys.argv) < 2:
        print("❗ 사용법: python3 tracking.py <TARGET_MAC>")
        return

    target_mac = sys.argv[1]
    print(f"🎯 추적 대상 MAC: {target_mac}")

    # 드론 연결 시도 (현재는 시뮬레이션 모드)
    connect_to_drone()

    # RSSI 추적기 초기화
    # Config 클래스를 통해 알고리즘의 세부 파라미터를 조정할 수 있습니다.
    cfg = Config(
        ema_alpha=0.25,
        der_alpha=0.35,
        found_threshold_db=-65.0,
        close_threshold_db=-40.0,
        lost_timeout_s=3.0
    )
    tracker = RSSITracker(cfg)

    print("👂 drone_client.py로부터 RSSI 입력을 기다립니다...")

    try:
        # drone_client.py가 보내는 RSSI 값을 표준 입력(stdin)으로 계속 읽어옵니다.
        loop = asyncio.get_event_loop()
        while True:
            # 표준 입력은 블로킹(blocking) 작업이므로, 비동기 이벤트 루프에서 직접 호출하지 않고
            # 별도의 스레드에서 실행하여 비동기 흐름을 방해하지 않도록 합니다.
            rssi_line = await loop.run_in_executor(None, sys.stdin.readline)
            
            if not rssi_line: # 입력 스트림이 닫히면 루프 종료
                print("...입력 스트림이 닫혔습니다. tracking.py를 종료합니다.")
                break

            try:
                # 입력받은 문자열을 float으로 변환
                rssi = float(rssi_line.strip())
                print(f"📶 RSSI 수신: {rssi:.2f} dBm")
            except (ValueError, TypeError):
                # 숫자로 변환할 수 없는 값이 들어오면 무시
                print(f"⚠️ 잘못된 RSSI 값 수신: '{rssi_line.strip()}'")
                continue

            # 추적 알고리즘 실행 및 제어 명령 생성
            # tracker.step() 함수가 모든 복잡한 계산을 수행합니다.
            control_command = tracker.step(rssi, now=time.time())

            # 생성된 제어 명령을 드론에 전송 (현재는 화면 출력)
            send_drone_command(control_command)

    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예기치 않은 오류 발생: {e}")
    finally:
        print("...프로그램 종료.")


if __name__ == "__main__":
    asyncio.run(main())
