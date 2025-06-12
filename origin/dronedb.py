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
def get_all_drones_status(timeout=10):
    now = datetime.utcnow()
    drones = []

    cursor = drone_status.find({}, {"_id": 0, "drone_id": 1, "last_seen": 1})
    for doc in cursor:
        last_seen = doc.get("last_seen")
        # last_seen이 없으면 offline 처리
        if last_seen is None:
            status = "offline"
            last_seen_str = ""
        else:
            diff = (now - last_seen).total_seconds()
            status = "online" if diff <= timeout else "offline"
            last_seen_str = last_seen.isoformat()

        drones.append({
            "drone_id": doc.get("drone_id"),
            "status": status,
            "last_seen": last_seen_str
        })

    return drones
