from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['DroneDB']  # 데이터베이스 이름
collection = db['drones']  # 컬렉션 이름

# 임시 저장소 (DB 대신 메모리 사용)
data_storage = list(collection.find({}, {'_id': False}))  # _id 제외

@app.route('/')
def index():
   return render_template('index.html', data=data_storage)

@app.route('/logging/')
def logging():
   return render_template('logging.html', data=data_storage)

@app.route('/register/')
def register():
   return render_template('register.html', data=data_storage)
   
@app.route('/submit/', methods=['GET', 'POST'])
def submit():
   #data = request.json
   #collection.insert_one(data)
   droneName = dict(request.form.get('droneName'))
   collection.find({'name'}) = droneName
   return list(collection.find({}, {'_id': False}))

'''
new_data = request.form.get('value') # 예: HTML form에서 value 전송
if new_data:
   data_storage.append(new_data)
return redirect(url_for('register'))'''

'''
@app.route('/all')
def get_all():
    all_data = list(collection.find({}, {'_id': False}))  # _id 제외
    return jsonify(all_data)'''

@app.route('/position/')
def get_data():
    return jsonify(data_storage)

if __name__ == '__main__':  
   app.run('0.0.0.0', port=5000, debug=True)
