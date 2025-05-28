import asyncio
from bleak import BleakScanner
import websockets

# 🔧 설정값
TARGET_MAC = "20:AF:1B:06:2F:7D".lower()
SERVER_URI = "ws://52.79.236.231:8765"  # 웹소켓 서버 주소
ALPHA = 0.1  # EMA 보정용 알파값

smoothed_rssi = None  # 초기값 없음
websocket = None  # 웹소켓 전역 참조


def detection_callback(device, advertisement_data):
    global smoothed_rssi

    if device.address.lower() == TARGET_MAC:
        current_rssi = advertisement_data.rssi

        # EMA 방식 보정
        if smoothed_rssi is None:
            smoothed_rssi = current_rssi
        else:
            smoothed_rssi = ALPHA * current_rssi + (1 - ALPHA) * smoothed_rssi

        print(f"[{device.address}] RSSI (원본): {current_rssi} dBm  →  (보정): {smoothed_rssi:.2f} dBm")

        # 웹소켓 통해 서버에 전송
        asyncio.create_task(send_to_server(smoothed_rssi))


async def send_to_server(rssi):
    global websocket
    if websocket:
        try:
            await websocket.send(f"RSSI: {rssi:.2f} dBm")
            print("📤 서버로 RSSI 전송 완료")
        except Exception as e:
            print(f"🚨 서버 전송 실패: {e}")


async def start_ble_scanner():
    print(f"📡 {TARGET_MAC.upper()} 장치의 RSSI 스캔 시작 중... (Ctrl+C 종료)")
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("🛑 BLE 스캔 종료")
    finally:
        await scanner.stop()


async def main():
    global websocket
    try:
        websocket = await websockets.connect(SERVER_URI)
        print("🔌 서버에 연결됨")

        # BLE 스캔 시작
        await start_ble_scanner()

    except websockets.exceptions.ConnectionClosedError:
        print("❌ 서버와의 연결 끊김")
    except Exception as e:
        print(f"🚨 예외 발생: {e}")
    finally:
        if websocket:
            await websocket.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ 사용자 중단")
