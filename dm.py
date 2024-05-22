import asyncio
import websockets
import concurrent.futures
import json
import uuid
import datetime

# 假设这是您的消息处理函数，可能涉及耗时操作


def msg_handler(message):
    # 在这里处理您的消息，例如打印、解析、存储或进一步处理
    data = json.loads(message)
    with open(f"{uuid.uuid4()}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def get_server_data():
    uri = "ws://127.0.0.1:6666/ws/publicMsg"
    async with websockets.connect(uri) as websocket:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            while True:
                response = await websocket.recv()
                print(f"Received from server, the time is{datetime.datetime.now()}")
                # 在线程池中异步执行msg_handler，不阻塞当前事件循环
                await loop.run_in_executor(pool, msg_handler, response)

# 使用asyncio事件循环运行get_server_data coroutine
asyncio.run(get_server_data())
