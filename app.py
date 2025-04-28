from flask import Flask, request, jsonify, render_template
app = Flask(__name__)

# 임시 저장소 (DB 대신 메모리 사용)
data_storage = []

@app.route('/')
def index():
   return render_template('index.html', data=data_storage)

@app.route('/logging/')
def logging():
   return render_template('logging.html', data=data_storage)

@app.route('/register/')
def register():
   return render_template('register.html')
   
@app.route('/submit/', methods=['POST'])
def submit():
    new_data = request.form.get('value') # 예: HTML form에서 value 전송
    if new_data:
        data_storage.append(new_data)
    return "Data received!", 200

@app.route('/position/')
def get_data():
    return jsonify(data_storage)

if __name__ == '__main__':  
   app.run('0.0.0.0', port=5000, debug=True)
