# drone_client.py
import asyncio
import websockets
from bleak import BleakScanner

DRONE_ID = "drone01"
SERVER_URI = "ws://<서버IP>:8765"

async def start_tracking(target_mac):
    alpha = 0.3
    smoothed_rssi = None
    while True:
        devices = await BleakScanner.discover()
        for d in devices:
            if d.address.lower() == target_mac.lower():
                current_rssi = d.rssi
                if smoothed_rssi is None:
                    smoothed_rssi = current_rssi
                else:
                    smoothed_rssi = alpha * current_rssi + (1 - alpha) * smoothed_rssi
                print(f"📡 추적 중: {target_mac} RSSI: {smoothed_rssi}")
        await asyncio.sleep(2)

async def connect():
    async with websockets.connect(SERVER_URI) as websocket:
        await websocket.send(f"drone_id:{DRONE_ID}")
        print("드론 연결됨")

        async def scan_ble():
            while True:
                devices = await BleakScanner.discover()
                for d in devices:
                    await websocket.send(f"ble:{d.address}:{d.name}")
                await asyncio.sleep(5)

        async def receive_command():
            async for message in websocket:
                if message.startswith("track:"):
                    target_mac = message.split(":", 1)[1]
                    print(f"🔍 추적 시작: {target_mac}")
                    await start_tracking(target_mac)

        await asyncio.gather(scan_ble(), receive_command())

asyncio.run(connect())
