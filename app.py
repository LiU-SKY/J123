from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['DroneDB']  # 데이터베이스 이름
collection = db['drones']  # 컬렉션 이름

@app.route('/')
def index():
   return render_template('index.html', data=list(collection.find({}, {'_id': False})))

@app.route('/logging/')
def logging():
   return render_template('logging.html', data=list(collection.find({}, {'_id': False})))

@app.route('/register/')
def register():
   data=list(collection.find({}, {'_id': False}))
   cursor = collection.find({}, {"name": 1, "_id": 0})
   droneList = [doc['name'] for doc in cursor]
   return render_template('register.html', data=data, droneList=droneList)

 # 드론 등록
@app.route('/submit/register/drone/', methods=['POST'])
def registerDrone():
   #data = request.json
   #collection.insert_one(data)
   droneName = request.form.get('droneName')
   doc = {
      "name": droneName,
      "status": None,
      "location": None,
      "tag": {"mac_address": None,
              "tag_name": None,
              "location": None
            }
   }
   collection.insert_one(doc)
   return redirect(url_for('register'))

# 드론 삭제
@app.route('/submit/delete/drone/', methods=['POST'])
def deleteDrone():
   droneName = request.form.get('deleteDrone')
   collection.delete_one({"name": droneName})
   return redirect(url_for('register'))

# 태그 등록
@app.route('/submit/register/tag/', methods=['POST'])
def registerTag():
   selectDrone = request.form.get('selectDrone')
   tagName = request.form.get('tagName')
   collection.update_one(
      {"name": selectDrone},
      {"$set": {"tag,tag_name": tagName}}
   )
   return redirect(url_for('register'))


'''
collection.update_one(
   {"name": "Drone A"},
   {"$set": {"name": f"{droneName}"}}
)
'''

@app.route('/position/')
def get_data():
    return jsonify(data_storage)

if __name__ == '__main__':  
   app.run('0.0.0.0', port=5000, debug=True)