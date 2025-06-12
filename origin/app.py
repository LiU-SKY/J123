from flask import Flask, request, flash, render_template, redirect, url_for, jsonify
import db
import dronedb
import asyncio
import json  # ✅ JSON 모듈 추가
import websockets

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route('/')
def index():
   result, statusCode = db.get_all_tags()
   drones, statusCode = dronedb.get_all_drones()
   return render_template('index.html', data = result["tags"], drones = drones["drones"])

@app.route('/logging/')
def logging():
   result, statusCode = db.get_all_tags()
   resultDrone, statusCode = dronedb.get_all_drones()
   return render_template('logging.html', data = result["tags"], droneData = resultDrone["drones"])

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

@app.route('/submit/track', methods=['POST'])
def track_device():
    drone_id = 'drone01'
    mac_address = request.form.get('mac_address')

    if not drone_id or not mac_address:
        flash("드론 또는 MAC 주소가 선택되지 않았습니다.", "error")
        return redirect(url_for('index'))

    try:
        asyncio.run(send_tracking_command(drone_id, mac_address))
        flash(f"{drone_id}에게 {mac_address} 추적 명령 전송 완료", "success")
    except Exception as e:
        flash(f"{drone_id} 명령 전송 실패: {e}", "error")

    return redirect(url_for('index'))

@app.route('/drones/status', methods=['GET'])
def drones_status():
    return jsonify(dronedb.get_all_drones_status())  # [{'drone_id': ..., 'status': ...}, ...]


# JSON 형식으로 WebSocket 명령 전송
async def send_tracking_command(drone_id, mac_address):
    try:
        async with websockets.connect("ws://52.79.236.231:8765") as ws:
            await ws.send(json.dumps({
                "type": "track",
                "drone_id": drone_id,
                "mac": mac_address
            }))
    except Exception as e:
        raise RuntimeError(f"WebSocket 전송 실패: {e}")

if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)