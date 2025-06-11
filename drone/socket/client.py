# client.py
# 재료가 아직 도착하지 않음
# 통신만 구현


# 주변 블루투스 기기를 검색
# 검색한 기기ID를 서버로 전송
# 서버에서 기기ID를 받으면 코드에 저장 후 추적
# 받은 기기ID가 검색 목록에 없으면 에러 출력
# RSSI 강도를 드론 컨트롤러로 전송


import asyncio
import websockets

SERVER_URI = "ws://52.79.236.231:8765"  # 서버 주소


async def communicate_with_server():
    try:
        async with websockets.connect(SERVER_URI) as websocket:
            print("🔌 서버에 연결됨")

            # 예: 서버에 초기 메시지 전송
            await websocket.send("클라이언트 접속: 준비 완료")

            # 통신 루프
            while True:
                try:
                    # 서버로부터 메시지 수신
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    print(f"📥 서버로부터 메시지 수신: {message}")

                    # 서버에 응답 메시지 전송
                    await websocket.send("메시지 확인 완료")
                except asyncio.TimeoutError:
                    print("⏱ 서버 응답 없음, 대기 중...")

                await asyncio.sleep(1)

    except websockets.exceptions.ConnectionClosedError:
        print("❌ 서버와의 연결이 끊어졌습니다.")
    except Exception as e:
        print(f"🚨 예외 발생: {e}")


# 실행
if __name__ == "__main__":
    asyncio.run(communicate_with_server())




