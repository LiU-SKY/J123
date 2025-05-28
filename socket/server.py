# server.py
# 재료가 아직 도착하지 않음
# 통신만 구현

# 서버 > 클라이언트 전송 메시지 요약
# 1. 사용자 요청을 받아 동작 준비 명령
# 2. 사용자 태그 선택 명령을 드론에 전달
# 3. 서버와 DB로 태그정보 전달


# server.py (websockets 12.x 호환)
import asyncio
from websockets.legacy.server import serve  # ✅ websockets 12.x에서 serve 위치
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
    # ✅ 0.0.0.0으로 수정 → 외부 접속 허용
    async with serve(handler, "0.0.0.0", 8765):
        print("🚀 서버 시작됨: ws://0.0.0.0:8765 (외부 접속 허용)")
        await asyncio.Future()  # 무한 대기

if __name__ == "__main__":
    asyncio.run(main())




