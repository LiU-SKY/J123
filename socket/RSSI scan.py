import asyncio
from bleak import BleakScanner

TARGET_MAC = "20:AF:1B:06:2F:7D".lower()
alpha = 0.1  # 알파값: 0.1 ~ 0.5 사이 권장
smoothed_rssi = None  # 초기값 없음

def detection_callback(device, advertisement_data):
    global smoothed_rssi

    if device.address.lower() == TARGET_MAC:
        current_rssi = advertisement_data.rssi
        if smoothed_rssi is None:
            smoothed_rssi = current_rssi
        else:
            smoothed_rssi = alpha * current_rssi + (1 - alpha) * smoothed_rssi

        print(f"[{device.address}] RSSI (원본): {current_rssi} dBm  →  (보정): {smoothed_rssi:.2f} dBm")

async def scan_ble_devices():
    print(f"📡 {TARGET_MAC.upper()} 장치의 RSSI (EMA 방식 보정 중)... (Ctrl+C 종료)")
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⛔ 종료")
    finally:
        await scanner.stop()

if __name__ == "__main__":
    asyncio.run(scan_ble_devices())
