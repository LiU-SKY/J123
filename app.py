from flask import Flask, request, jsonify, render_template, redirect, url_for
import db

app = Flask(__name__)

@app.route('/')
def index():

   return render_template('index.html', data = db.get_all_tags())

@app.route('/logging/')
def logging():
   return render_template('logging.html', data = db.get_all_tags())

@app.route('/register/')
def register():
   data=db.get_all_tags()
   return render_template('register.html', data=data)

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
   macAddress = request.form.get('macAddress')
   tagName = request.form.get('tagName')
   location = request.form.get('location')
   db.register_tag(macAddress, tagName, location)
   return redirect(url_for('register'))

@app.route('/position/')
def get_data():
    return jsonify(data_storage)

if __name__ == '__main__':  
   app.run('0.0.0.0', port=5000, debug=True)
