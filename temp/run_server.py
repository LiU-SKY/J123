# run_server.py
import threading
import asyncio
from app import app
from server import start_websocket_server  # 함수화 필요

def run_flask():
    app.run("0.0.0.0", port=5000)

def run_ws():
    asyncio.run(start_websocket_server())

if __name__ == "__main__":
    threading.Thread(target=run_ws).start()
    run_flask()
