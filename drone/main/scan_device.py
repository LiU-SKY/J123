# scan_ble_devices.py
import asyncio
from bleak import BleakScanner

async def scan_ble():
    print("🔍 BLE 기기 스캔 시작 (Ctrl+C로 종료)")
    while True:
        devices = await BleakScanner.discover(timeout=3.0)  # 3초간 스캔
        print(f"--- 발견된 기기 {len(devices)}개 ---")
        for d in devices:
            # 일부 OS에서는 address가 MAC이 아니라 UUID일 수 있음
            print(f"MAC/주소: {d.address} | 이름: {d.name}")
        print()
        await asyncio.sleep(2)  # 다음 스캔 전 잠시 대기

if __name__ == "__main__":
    try:
        asyncio.run(scan_ble())
    except KeyboardInterrupt:
        print("\n스캔 종료")