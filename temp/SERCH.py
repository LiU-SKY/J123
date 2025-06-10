import asyncio
from bleak import BleakScanner
from datetime import datetime

TARGET_MAC = "18:04:ED:FA:B9:82".lower()  # 추적할 기기 MAC 주소

def detection_callback(device, advertisement_data):
    if device.address.lower() == TARGET_MAC:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] RSSI: {advertisement_data.rssi} dBm")

async def scan_target():
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    print(f"🎯 '{TARGET_MAC.upper()}' 기기 추적 시작 (Ctrl+C로 종료)")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 추적 중단됨")
    finally:
        await scanner.stop()

if __name__ == "__main__":
    asyncio.run(scan_target())
