import asyncio
import websockets
import json
import requests


# 先简单的用硬代码方案指定监控的群聊和私聊信息源，后续可以改进
# 注意群聊写法，群号后面还必须带上 @chatroom
watching_list = ['49591466778@chatroom', 'wxid_tnv0hd5hj3rs11']


async def pipeline(input_data):
    url = "http://127.0.0.1:8077/feed"
    response = requests.post(url, json=input_data)
    if response.status_code != 200:
        print("Warning: Failed to send message. check wiseflow status")
        print(response.text)


# 对应不同的数据结构，考虑后续维护升级可能，分成两个函数
async def get_public_msg(websocket_uri):
    reconnect_attempts = 0
    max_reconnect_attempts = 3
    while True:
        try:
            async with websockets.connect(websocket_uri, max_size=10 * 1024 * 1024) as websocket:
                while True:
                    response = await websocket.recv()
                    datas = json.loads(response)
                    for data in datas["data"]:
                        input_data = {
                            "user_id": data["StrTalker"],
                            "type": "publicMsg",
                            "content": data["Content"],
                            "addition": data["MsgSvrID"]
                        }
                        await pipeline(input_data)

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed with exception: {e}")
            reconnect_attempts += 1
            if reconnect_attempts <= max_reconnect_attempts:
                print(f"Reconnecting attempt {reconnect_attempts}...")
                await asyncio.sleep(1)
            else:
                print("Max reconnect attempts reached. Exiting.")
                break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break


async def get_general_msg(websocket_uri):
    reconnect_attempts = 0
    max_reconnect_attempts = 3
    while True:
        try:
            async with websockets.connect(websocket_uri, max_size=10 * 1024 * 1024) as websocket:
                while True:
                    response = await websocket.recv()
                    datas = json.loads(response)
                    for data in datas["data"]:
                        if data["IsSender"] == "1":
                            # 跳过自己发送的消息
                            continue
                        if data['StrTalker'] not in watching_list:
                            continue

                        # 目前仅处理文本消息和url（微信公众号分享卡片）两类消息
                        # 如需更多类型消息，请看 wxbot各类型信息原始json格式.txt
                        if data['Type'] == '1':
                            input_data = {
                                "user_id": data["StrTalker"],
                                "type": "text",
                                "content": data["StrContent"],
                                "addition": data["MsgSvrID"]
                            }
                        elif data['Type'] == '49':
                            if data['SubType'] != '5':
                                # 非文章形式的公众号消息，比如公众号发来的视频卡
                                continue
                            input_data = {
                                "user_id": data["StrTalker"],
                                "type": "url",
                                "content": data["Content"],
                                "addition": data["MsgSvrID"]
                            }
                        else:
                            continue
                        await pipeline(input_data)
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed with exception: {e}")
            reconnect_attempts += 1
            if reconnect_attempts <= max_reconnect_attempts:
                print(f"Reconnecting attempt {reconnect_attempts}...")
                await asyncio.sleep(1)
            else:
                print("Max reconnect attempts reached. Exiting.")
                break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break


async def main():
    uri_general = "ws://127.0.0.1:8066/ws/generalMsg"
    uri_public = "ws://127.0.0.1:8066/ws/publicMsg"

    # 创建并行任务
    task1 = asyncio.create_task(get_general_msg(uri_general))
    task2 = asyncio.create_task(get_public_msg(uri_public))

    # 等待所有任务完成
    await asyncio.gather(task1, task2)


# 使用asyncio事件循环运行main coroutine
asyncio.run(main())
