from pymongo import MongoClient
import datetime
import asyncio
from websockets.legacy.server import serve  # ✅ websockets 12.x 대응
import websockets

connected_drones = {}  # {"drone01": websocket}

# MongoDB 연결
client = MongoClient("mongodb://localhost:27017")
db = client["DroneDB"]
ble_logs = db["ble_logs"]

# WebSocket 핸들러
async def handler(websocket, path):
    drone_id = None
    try:
        async for message in websocket:
            if message.startswith("drone_id:"):
                drone_id = message.split(":", 1)[1]
                connected_drones[drone_id] = websocket
                print(f"✅ {drone_id} 연결됨")

            elif message.startswith("ble:"):
                _, mac, name = message.split(":", 2)
                # ✅ MAC 주소 중복 시 덮어쓰기 (upsert 사용)

                ble_logs.update_one(
                    {"drone_id": drone_id, "mac_address": mac},  # 조건: 드론+MAC
                    {"$set": {
                        "device_name": name,
                        "timestamp": datetime.datetime.utcnow()
                    }},
                    upsert=True
                )
                print(f"📡 BLE 기기 갱신됨: {mac} - {name}")



    except websockets.exceptions.ConnectionClosed:
        print(f"❌ {drone_id} 연결 종료됨")
        # WebSocket 연결 목록에서 제거
        if drone_id in connected_drones:
            del connected_drones[drone_id]
        # ✅ 드론 정보 삭제 (예: drones 컬렉션 사용 시)
        db["drones"].delete_one({"drone_id": drone_id})
        # ✅ 해당 드론의 BLE 로그 삭제
        ble_logs.delete_many({"drone_id": drone_id})
        print(f"🗑️ 드론 '{drone_id}' 관련 정보 삭제 완료")

# WebSocket 서버 시작
async def start_websocket_server():
    async with serve(handler, "0.0.0.0", 8765):
        print("🚀 WebSocket 서버 시작됨: ws://0.0.0.0:8765")
        await asyncio.Future()  # 무한 대기

# 단독 실행 시
if __name__ == "__main__":
    asyncio.run(start_websocket_server())
