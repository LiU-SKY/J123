from flask import Flask, request, render_template, redirect, url_for, flash
import db
import asyncio
import json  # ✅ JSON 모듈 추가
from server import connected_drones  # WebSocket 연결된 드론 목록

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route('/')
def index():
    return redirect(url_for('logging'))

# BLE 기기 목록 페이지
@app.route('/logging')
def logging():
    ble_data, _ = db.get_recent_ble_logs()
    return render_template("logging.html", ble_data=ble_data)

# 사용자가 특정 BLE 기기를 선택해 드론에 추적 명령을 보냄
@app.route('/submit/track', methods=['POST'])
def track_device():
    drone_id = request.form.get('drone_id')
    mac_address = request.form.get('mac_address')

    if not drone_id or not mac_address:
        flash("드론 또는 MAC 주소가 선택되지 않았습니다.", "error")
        return redirect(url_for('logging'))

    if drone_id in connected_drones:
        asyncio.run(send_tracking_command(drone_id, mac_address))
        flash(f"{drone_id}에게 {mac_address} 추적 명령 전송 완료", "success")
    else:
        flash(f"{drone_id}가 현재 연결되어 있지 않습니다.", "error")

    return redirect(url_for('logging'))

# BLE 목록 API (JS에서 사용)
@app.route("/api/ble_list")
def ble_list_api():
    ble_data, _ = db.get_recent_ble_logs()
    return ble_data

# ✅ JSON 형식으로 WebSocket 명령 전송
async def send_tracking_command(drone_id, mac_address):
    ws = connected_drones[drone_id]
    message = {
        "type": "track",
        "mac": mac_address
    }
    await ws.send(json.dumps(message))  # JSON 형식으로 전송

if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
