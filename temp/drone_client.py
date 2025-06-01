import asyncio
import websockets
import json
from bleak import BleakScanner

DRONE_ID = "drone01"
SERVER_URI = "ws://52.79.236.231:8765"  # 서버 IP로 수정

async def start_tracking(target_mac):
    print(f"🔍 추적 시작: {target_mac}")
    while True:
        devices = await BleakScanner.discover()
        for d in devices:
            if d.address.lower() == target_mac.lower():
                print(f"📡 {target_mac} RSSI: {d.rssi}")
        await asyncio.sleep(2)

async def connect():
    async with websockets.connect(SERVER_URI) as websocket:
        await websocket.send(json.dumps({
            "type": "drone_id",
            "drone_id": DRONE_ID
        }))

        async def scan_ble():
            while True:
                devices = await BleakScanner.discover()
                for d in devices:
                    await websocket.send(json.dumps({
                        "type": "ble",
                        "mac": d.address,
                        "name": d.name or "Unknown"
                    }))
                await asyncio.sleep(5)

        async def receive_command():
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "track":
                        await start_tracking(data["mac"])
                except Exception as e:
                    print("❌ 명령 처리 중 오류:", e)

        await asyncio.gather(scan_ble(), receive_command())

asyncio.run(connect())
