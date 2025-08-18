from pymongo import MongoClient
import datetime
import asyncio
from websockets.legacy.server import serve
import websockets
import json

client = MongoClient("mongodb://localhost:27017")
db = client["DroneDB"]
ble_logs = db["ble_logs"]
drone_status = db["drones"]

# ✅ 드론 연결 저장소 추가
connected_clients = {}

async def handler(websocket, path):
    drone_id = None
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                print("❌ 잘못된 JSON 수신:", message)
                continue

            msg_type = data.get("type")

            if msg_type == "drone_id":
                drone_id = data.get("drone_id")
                connected_clients[drone_id] = websocket  # 드론 소켓 저장
                print(f"✅ 드론 등록됨: {drone_id}")
                drone_status.update_one(
                    {"drone_id": drone_id},
                    {"$set": {"status": "online", "last_seen": datetime.datetime.utcnow()}},
                    upsert=True
                )

            elif msg_type == "ble":
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

            elif msg_type == "track":
                print(f"🚀 track 명령 수신: {data}")
                target_drone = data.get("drone_id")
                if target_drone in connected_clients:
                    await connected_clients[target_drone].send(json.dumps({
                        "type": "track",
                        "mac": data.get("mac")
                    }))
                    print(f"📡 track 명령 전달 완료 → {target_drone}")
                else:
                    print(f"❌ 드론 {target_drone} 연결되지 않음")

            elif msg_type == "stop":
                print(f"🚀 track 명령 수신: {data}")
                target_drone = data.get("drone_id")
                if target_drone in connected_clients:
                    await connected_clients[target_drone].send(json.dumps({
                        "type": "stop",
                        "mac": data.get("mac")
                    }))
                    print(f"📡 stop 명령 전달 완료 → {target_drone}")
                else:
                    print(f"❌ 드론 {target_drone} 연결되지 않음")

    except websockets.exceptions.ConnectionClosed:
        print(f"❌ {drone_id} 연결 종료됨")
        if drone_id in connected_clients:
            del connected_clients[drone_id]
        drone_status.delete_one({"drone_id": drone_id})
        ble_logs.delete_many({"drone_id": drone_id})
        print(f"🗑️ {drone_id} 관련 기록 삭제 완료")

async def start_websocket_server():
    async with serve(handler, "0.0.0.0", 8765):
        print("🚀 WebSocket 서버 시작됨")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(start_websocket_server())
