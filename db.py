from pymongo import MongoClient
from bson import ObjectId

# MongoDB 연결
client = MongoClient('mongodb://localhost:27017')
db = client['DroneDB']
tags_collection = db['tags']

# 태그 등록
def register_tag(mac_address, tag_name, location):
    if tags_collection.find_one({"mac_address": mac_address}):
        return {"error": "이미 등록된 MAC 주소입니다"}, 409

    tags_collection.insert_one({
        "mac_address": mac_address,
        "tag_name": tag_name,
        "location": location
    })
    return {"message": "태그 등록 성공"}, 201

# 태그 전체 조회
def get_all_tags():
    tags = list(tags_collection.find({}, {'_id': 0}))  # ObjectId 제외
    return {"tags": tags}, 200

# 태그 수정 (mac_address 기준)
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

# 태그 삭제 (mac_address 기준)
def delete_tag(mac_address):
    result = tags_collection.delete_one({"mac_address": mac_address})
    if result.deleted_count == 0:
        return {"error": "삭제할 태그를 찾을 수 없습니다."}, 404

    return {"message": "태그 삭제 성공"}, 200
