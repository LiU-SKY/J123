import asyncio
import websockets
import json
import subprocess
from bleak import BleakScanner

DRONE_ID = "drone01"
SERVER_URI = "ws://52.79.236.231:8765"
tracking_process = None

async def start_tracking(target_mac):
    global tracking_process
    print(f"🔍 추적 시작: {target_mac}")

    # tracking.py 실행 및 MAC 주소 인자 전달
    tracking_process = await asyncio.create_subprocess_exec(
        "python3", "tracking.py", target_mac,
        stdin=asyncio.subprocess.PIPE
    )

    try:
        while True:
            devices = await BleakScanner.discover()
            for d in devices:
                if d.address.lower() == target_mac.lower():
                    rssi = d.rssi
                    print(f"📡 RSSI: {rssi}")
                    # tracking.py에 RSSI 값 전달
                    if tracking_process.stdin:
                        tracking_process.stdin.write(f"{rssi}\n".encode())
                        await tracking_process.stdin.drain()
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("🛑 추적 중단")
        tracking_process.kill()

async def connect():
    async with websockets.connect(SERVER_URI) as websocket:
        await websocket.send(json.dumps({
            "type": "drone_id",
            "drone_id": DRONE_ID
        }))

        devices = await BleakScanner.discover()
        for d in devices:
            await websocket.send(json.dumps({
                "type": "ble",
                "mac": d.address,
                "name": d.name or "Unknown"
            }))
        print("📡 BLE 스캔 전송 완료")

        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "track":
                    await start_tracking(data["mac"])
            except Exception as e:
                print("❌ 명령 처리 중 오류:", e)

if __name__ == "__main__":
    asyncio.run(connect())
