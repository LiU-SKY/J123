from pymongo import MongoClient

# MongoDB에 연결
client = MongoClient("mongodb://localhost:27017")  
# MongoDB URI (로컬 또는 Atlas)

# 사용할 데이터베이스 선택
db = client["DroneDB"]

# 사용할 컬렉션 선택
collection = db["drones"]

# 데이터 삽입 함수
def insert_data(data):
    collection.insert_one(data)

# 데이터 조회 함수
def get_all_data():
    return list(collection.find())
# 데이터 검색
def search_by_name(name):
    return list(collection.find({"name": name}))

# 조회와 검색은 다른것 조회는 데이터 조회, 검색은 이름 검색

# 데이터 수정
def update_by_id(document_id, new_data):
    result = collection.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": new_data}
    )
    return result.modified_count

# 데이터 삭제
def delete_by_id(document_id):
    result = collection.delete_one({"_id": ObjectId(document_id)})
    return result.deleted_count
