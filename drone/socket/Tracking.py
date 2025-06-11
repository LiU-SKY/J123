import asyncio
from bleak import BleakScanner

TARGET_MAC = "20:AF:1B:06:2F:7D".lower()
alpha = 0.2  # EMA 보정 계수

# 8방향 정의
DIRECTIONS = [
    "forward", "backward", "left", "right",
    "forward-left", "forward-right", "backward-left", "backward-right"
]

rssi_direction_map = {}
smoothed_rssi = None  # 전역 변수로 보정된 RSSI 저장

async def move_drone_simulated(direction):
    """실제 드론 이동 대신 사용자 승인을 받아 이동 시뮬레이션"""
    print(f"\n🛰 '{direction}' 방향으로 이동할까요?")
    input("▶️ 엔터를 눌러 이동을 시뮬레이션합니다...")
    await asyncio.sleep(1)  # 이동 시간

async def get_rssi_for_direction(scanner, direction):
    global smoothed_rssi
    smoothed_rssi = None

    await move_drone_simulated(direction)
    await scanner.start()
    await asyncio.sleep(2)  # RSSI 수집 시간
    await scanner.stop()

    return smoothed_rssi if smoothed_rssi is not None else -999

def detection_callback(device, advertisement_data):
    global smoothed_rssi
    if device.address.lower() == TARGET_MAC:
        current_rssi = advertisement_data.rssi
        if smoothed_rssi is None:
            smoothed_rssi = current_rssi
        else:
            smoothed_rssi = alpha * current_rssi + (1 - alpha) * smoothed_rssi
        print(f"📶 RSSI 측정 중... 원본: {current_rssi} dBm → 보정: {smoothed_rssi:.2f} dBm")

async def find_best_direction(scanner):
    best_direction = None
    best_rssi = -999

    print(f"\n📡 [{TARGET_MAC.upper()}] 신호를 기반으로 방향을 탐색합니다...")

    for direction in DIRECTIONS:
        rssi = await get_rssi_for_direction(scanner, direction)
        rssi_direction_map[direction] = rssi
        print(f"🧭 {direction.upper()} 방향 RSSI: {rssi:.2f} dBm")

        if rssi > best_rssi:
            best_rssi = rssi
            best_direction = direction

    print(f"\n✅ 최적 방향: {best_direction.upper()} (RSSI: {best_rssi:.2f} dBm)")
    return best_direction, best_rssi

async def rssi_tracking_loop():
    scanner = BleakScanner(detection_callback)
    attempt = 1
    while True:
        print(f"\n🔄 RSSI 추적 반복 {attempt}회차...")
        direction, rssi = await find_best_direction(scanner)

        if abs(rssi) < 10:
            print(f"🎯 RSSI가 {rssi:.2f} dBm으로 매우 강합니다. 추적 종료합니다.")
            break

        print(f"➡️ '{direction}' 방향으로 이동합니다. RSSI: {rssi:.2f} dBm")
        attempt += 1

if __name__ == "__main__":
    asyncio.run(rssi_tracking_loop())
