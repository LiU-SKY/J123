from pymongo import MongoClient
import datetime
import asyncio
from websockets.legacy.server import serve
import websockets
import json

# MongoDB 연결
client = MongoClient("mongodb://localhost:27017")
db = client["DroneDB"]
ble_logs = db["ble_logs"]
drone_status = db["drones"]

async def handler(websocket, path):
    drone_id = None
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                print("❌ 잘못된 JSON 수신:", message)
                continue

            if data.get("type") == "drone_id":
                drone_id = data.get("drone_id")
                print(f"✅ 드론 등록됨: {drone_id}")
                drone_status.update_one(
                    {"drone_id": drone_id},
                    {"$set": {"status": "online", "last_seen": datetime.datetime.utcnow()}},
                    upsert=True
                )

            elif data.get("type") == "ble":
                mac = data.get("mac")
                name = data.get("name")
                ble_logs.update_one(
                    {"drone_id": drone_id, "mac_address": mac},
                    {"$set": {
                        "device_name": name,
                        "timestamp": datetime.datetime.utcnow()
                    }},
                    upsert=True
                )
                print(f"📡 BLE 갱신: {mac} - {name}")

    except websockets.exceptions.ConnectionClosed:
        print(f"❌ {drone_id} 연결 종료됨")
        drone_status.delete_one({"drone_id": drone_id})
        ble_logs.delete_many({"drone_id": drone_id})
        print(f"🗑️ {drone_id} 관련 기록 삭제 완료")

async def start_websocket_server():
    async with serve(handler, "0.0.0.0", 8765):
        print("🚀 WebSocket 서버 시작됨")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(start_websocket_server())
