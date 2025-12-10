import asyncio
import websockets
import json

RUN_ID = "0cdf38d6-1cd0-4a69-bd75-b95dfff91570"  # from /graph/run or /graph/run_async


async def main():
    uri = f"ws://127.0.0.1:9000/ws/logs/{RUN_ID}"
    async with websockets.connect(uri) as websocket:
        try:
            while True:
                msg = await websocket.recv()
                print("WS >", msg)
        except websockets.ConnectionClosed:
            print("WebSocket closed")


if __name__ == "__main__":
    asyncio.run(main())
