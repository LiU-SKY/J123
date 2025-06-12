from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient("mongodb://localhost:27017")
db = client["DroneDB"]
drone_status = db["drones"]

# 드론론 전체 조회
def get_all_drones():
    drones = list(drone_status.find({}, {'_id': 0}))  # ObjectId 제외
    return {"drones": drones}, 200

# 드론 상태만 조회 + 상태 판단
def get_all_drones_status():
    cursor = drone_status.find({}, {"_id": 0, "drone_id": 1, "status": 1, "last_seen": 1})
    drones = []

    for doc in cursor:
        # status는 a.py에서 저장된 값 그대로 사용
        status = str(doc.get("status", "offline")).strip().lower()

        # last_seen은 ISO 문자열로 변환 (없으면 공백)
        last_seen = doc.get("last_seen")
        last_seen_str = last_seen.isoformat() if last_seen else ""

        drones.append({
            "drone_id": doc.get("drone_id"),
            "status": status,
            "last_seen": last_seen_str
        })

    return drones