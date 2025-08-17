import asyncio
import websockets
import json
from bleak import BleakScanner

DRONE_ID = "drone01"
SERVER_URI = "ws://52.79.236.231:8765"
tracking_task = None  # 실행 중인 추적 작업을 저장할 변수

async def log_stream(stream, prefix):
    """Subprocess의 출력 스트림을 실시간으로 읽어 화면에 출력하는 헬퍼 함수"""
    while True:
        line = await stream.readline()
        if line:
            # tracking.py가 출력하는 모든 메시지 앞에 [TRACKING] 또는 [ERROR]를 붙여줍니다.
            print(f"{prefix} {line.decode(errors='ignore').strip()}")
        else:
            break

async def tracking_worker(target_mac):
    """백그라운드에서 실제 추적 로직을 수행하는 워커 함수"""
    print(f"🔍 추적 시작: {target_mac}")
    tracking_process = None
    scanner = None
    log_tasks = []
    try:
        # tracking.py 실행 시 stdout과 stderr를 PIPE로 연결하여 출력을 가로챌 수 있도록 함
        tracking_process = await asyncio.create_subprocess_exec(
            "python3", "tracking.py", target_mac,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # tracking.py의 출력을 실시간으로 감시하는 백그라운드 작업 시작
        stdout_task = asyncio.create_task(log_stream(tracking_process.stdout, "[TRACKING]"))
        stderr_task = asyncio.create_task(log_stream(tracking_process.stderr, "[TRACKING_ERROR]"))
        log_tasks = [stdout_task, stderr_task]

        rssi_queue = asyncio.Queue()

        def detection_callback(device, advertisement_data):
            if device.address.lower() == target_mac.lower():
                rssi_queue.put_nowait(advertisement_data.rssi)

        scanner = BleakScanner(detection_callback=detection_callback)
        await scanner.start()

        while True:
            rssi = await rssi_queue.get()
            print(f"📡 RSSI: {rssi}")
            if tracking_process and tracking_process.stdin and not tracking_process.stdin.is_closing():
                tracking_process.stdin.write(f"{rssi}\n".encode())
                await tracking_process.stdin.drain()
    except asyncio.CancelledError:
        print("🛑 추적 작업 취소됨")
    except Exception as e:
        print(f"❌ 추적 워커 오류: {e}")
    finally:
        if scanner:
            await scanner.stop()
        
        # 로그 감시 작업들도 함께 취소
        for task in log_tasks:
            if not task.done():
                task.cancel()
        
        if tracking_process:
            print("...tracking.py 프로세스 종료 중...")
            try:
                tracking_process.terminate()
                await tracking_process.wait()
            except ProcessLookupError:
                pass
        print("🛑 추적 완전 중단")


async def connect():
    global tracking_task
    async with websockets.connect(SERVER_URI) as websocket:
        print("✅ 서버에 연결되었습니다.")
        await websocket.send(json.dumps({
            "type": "drone_id",
            "drone_id": DRONE_ID
        }))

        print("📡 주변 BLE 장치 스캔 중...")
        devices = await BleakScanner.discover(timeout=5.0)
        for d in devices:
            await websocket.send(json.dumps({
                "type": "ble",
                "mac": d.address,
                "name": d.name or "Unknown"
            }))
        print("📡 BLE 스캔 전송 완료")

        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "track":
                    target_mac = data["mac"]
                    
                    if tracking_task and not tracking_task.done():
                        print("...기존 추적 작업을 중단합니다...")
                        tracking_task.cancel()
                        await tracking_task
                    
                    tracking_task = asyncio.create_task(tracking_worker(target_mac))

            except Exception as e:
                print(f"❌ 명령 처리 중 오류: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(connect())
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
    except ConnectionRefusedError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
