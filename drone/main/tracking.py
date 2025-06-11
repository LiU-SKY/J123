import sys
import time
import serial
import asyncio

# ============ 설정 ============ #
RSSI_THRESHOLD = -15
EMA_ALPHA = 0.2
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 57600

# ============ 전역 상태 ============ #
smoothed_rssi = None
drone_serial = None

# ============ 드론 연결 ============ #
def connect_to_drone():
    global drone_serial
    try:
        drone_serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("✅ 드론 시리얼 연결 완료")
    except Exception as e:
        print(f"❌ 드론 연결 실패: {e}")

# ============ 드론 명령 시뮬레이션 ============ #
def send_drone_command(action):
    print(f"🛸 드론 명령: {action}")
    # drone_serial.write(f"{action}\n".encode())  # 실제 사용시
    time.sleep(1)

# ============ 방향 결정 ============ #
def determine_direction(last_rssi, current_rssi):
    if current_rssi > last_rssi + 2:
        return "forward"
    elif current_rssi < last_rssi - 2:
        return "backward"
    else:
        return "rotate"

def move_drone(direction):
    if direction == "forward":
        send_drone_command("앞으로 이동")
    elif direction == "backward":
        send_drone_command("뒤로 이동")
    elif direction == "rotate":
        send_drone_command("왼쪽으로 회전")

# ============ 메인 ============ #
async def main():
    global smoothed_rssi
    if len(sys.argv) < 2:
        print("❗ 사용법: python3 tracking.py <TARGET_MAC>")
        return

    connect_to_drone()
    target_mac = sys.argv[1].lower()
    last_rssi = -100
    send_drone_command("시동")

    try:
        while True:
            # stdin에서 RSSI 읽음
            rssi_line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            try:
                current_rssi = int(rssi_line.strip())
            except ValueError:
                continue

            if smoothed_rssi is None:
                smoothed_rssi = current_rssi
            else:
                smoothed_rssi = EMA_ALPHA * current_rssi + (1 - EMA_ALPHA) * smoothed_rssi

            print(f"📶 RSSI 입력: {current_rssi} → 필터: {smoothed_rssi:.2f}")

            if smoothed_rssi >= RSSI_THRESHOLD:
                send_drone_command("착륙")
                print("🎯 목표 도달, 착륙 완료")
                break

            direction = determine_direction(last_rssi, smoothed_rssi)
            move_drone(direction)
            last_rssi = smoothed_rssi

    except KeyboardInterrupt:
        send_drone_command("비상 착륙")

if __name__ == "__main__":
    asyncio.run(main())
