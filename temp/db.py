# db.py
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["DroneDB"]

# BLE 로그 컬렉션
ble_logs = db["ble_logs"]

# BLE 로그 최근 50개 가져오기
def get_recent_ble_logs():
    logs = list(ble_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(50))
    return logs, 200

# --- (선택 사항) 태그 관련 기능이 이미 있다면 여기에 추가로 포함해도 됨 ---
tags_collection = db["tags"]

def register_tag(mac_address, tag_name, location):
    if tags_collection.find_one({"mac_address": mac_address}):
        return {"error": "이미 등록된 MAC 주소입니다"}, 409
    tags_collection.insert_one({
        "mac_address": mac_address,
        "tag_name": tag_name,
        "location": location
    })
    return {"message": "태그 등록 성공"}, 201

def get_all_tags():
    tags = list(tags_collection.find({}, {"_id": 0}))
    return {"tags": tags}, 200

def update_tag(mac_address, new_tag_name=None, new_location=None):
    update_fields = {}
    if new_tag_name:
        update_fields['tag_name'] = new_tag_name
    if new_location:
        update_fields['location'] = new_location

    if not update_fields:
        return {"error": "변경할 내용이 없습니다."}, 400

    result = tags_collection.update_one(
        {"mac_address": mac_address},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        return {"error": "해당 MAC 주소를 찾을 수 없습니다."}, 404

    return {"message": "태그 수정 성공"}, 200

def delete_tag(mac_address):
    result = tags_collection.delete_one({"mac_address": mac_address})
    if result.deleted_count == 0:
        return {"error": "삭제할 태그를 찾을 수 없습니다."}, 404
    return {"message": "태그 삭제 성공"}, 200
