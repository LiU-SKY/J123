# server.py
# 재료가 아직 도착하지 않음
# 통신만 구현

# 서버 > 클라이언트 전송 메시지 요약
# 1. 사용자 요청을 받아 동작 준비 명령
# 2. 사용자 태그 선택 명령을 드론에 전달
# 3. 서버와 DB로 태그정보 전달


# server.py (websockets 12.x 호환)
import asyncio
from websockets.legacy.server import serve  # ✅ 변경된 serve 위치
import websockets

async def handler(websocket, path):
    print("🤝 클라이언트 연결됨")
    try:
        async for message in websocket:
            print(f"📩 수신: {message}")
            await websocket.send("서버 응답: 명령 없음")
    except websockets.exceptions.ConnectionClosed:
        print("❌ 연결 종료됨")

async def main():
    async with serve(handler, "localhost", 8765):  # ✅ 변경된 serve 사용
        print("🚀 서버 시작됨: ws://localhost:8765")
        await asyncio.Future()  # 무한 대기

if __name__ == "__main__":
    asyncio.run(main())



