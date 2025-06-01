# app.py
from flask import Flask, request, render_template, redirect, url_for, flash
import db
import asyncio
from server import connected_drones  # WebSocket 연결된 드론 목록을 import

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 보안을 위해 실제 배포 시 환경 변수로 관리하세요.

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

# 비동기 WebSocket 전송
async def send_tracking_command(drone_id, mac_address):
    ws = connected_drones[drone_id]
    await ws.send(f"track:{mac_address}")

if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
