from pymongo import MongoClient
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017")
db = client["DroneDB"]
drone_status = db["drones"]

# 드론론 전체 조회
def get_all_drones():
    drones = list(drone_status.find({}, {'_id': 0}))  # ObjectId 제외
    return {"drones": drones}, 200