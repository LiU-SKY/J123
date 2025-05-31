from flask import Flask, request, flash, render_template, redirect, url_for
import db

app = Flask(__name__)
app.secret_key = "your_secret_key" 

@app.route('/')
def index():
   result, statusCode = db.get_all_tags()
   return render_template('index.html', data = result["tags"])

@app.route('/logging/')
def logging():
   result, statusCode = db.get_all_tags()
   return render_template('logging.html', data = result["tags"])

@app.route('/register/')
def register():
   result, statusCode = db.get_all_tags()
   return render_template('register.html', data = result["tags"])

'''
 # 드론 등록
@app.route('/submit/register/drone/', methods=['POST'])
def registerDrone():
   return redirect(url_for('register'))
'''
'''
# 드론 삭제
@app.route('/submit/delete/drone/', methods=['POST'])
def deleteDrone():
   droneName = request.form.get('deleteDrone')
   collection.delete_one({"name": droneName})
   return redirect(url_for('register'))
'''

# 태그 등록
@app.route('/submit/register/tag/', methods=['POST'])
def registerTag():
   macAddress = request.form.get('macAddress')
   tagName = request.form.get('tagName')
   location = request.form.get('location')
   result, statusCode = db.register_tag(macAddress, tagName, location)
   if statusCode != 201:
      flash(result["error"], "error")
   else:
      flash(result["message"], "success")
   return redirect(url_for('register'))

# 태그 삭제
@app.route('/submit/delete/tag/', methods=['POST'])
def deleteTag():
   macAddress = request.form.get('deleteTag')
   result, statusCode = db.delete_tag(macAddress)
   if statusCode != 200:
      flash(result["error"], "error")
   else:
      flash(result["message"], "success")
   return redirect(url_for('register'))

# 태그 수정
@app.route('/submit/edit/tag/', methods=['POST'])
def editTag():
   macAddress = request.form.get('macAddress')
   tagName = request.form.get('tagName')
   result, statusCode = db.update_tag(macAddress, tagName)
   if statusCode != 200:
      flash(result["error"], "error")
   else:
      flash(result["message"], "success")
   return redirect(url_for('register'))

if __name__ == '__main__':  
   app.run('0.0.0.0', port=5000, debug=True)
