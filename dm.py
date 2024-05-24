import asyncio
import websockets
import concurrent.futures
import json
from rally_point import roster


# 假设这是您的消息处理函数，可能涉及耗时操作
async def get_public_msg():
    uri = "ws://127.0.0.1:8066/ws/publicMsg"
    async with websockets.connect(uri, max_size=10 * 1024 * 1024) as websocket:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            while True:
                response = await websocket.recv()
                datas = json.loads(response)
                for data in datas["data"]:
                    if data["IsSender"] != "0":
                        print('self-send message, pass')
                        print(data)
                        continue
                    input_data = {"user_id": data["StrTalker"], "type": "publicMsg", "content": data["Content"], "addition": data["MsgSvrID"]}
                    for agent in roster["publicMsg"]:
                        await loop.run_in_executor(pool, agent, input_data)

# 使用asyncio事件循环运行get_public_msg coroutine
asyncio.run(get_public_msg())
