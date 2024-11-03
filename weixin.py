import websockets
import json
import re
import httpx
import asyncio
import os
from utils.general_utils import get_logger, aio_config_load, aio_save_config, is_file_exists, read_file_as_base64
from utils.data_template import config_template
from typing import Optional


"""
有关导演账号：
awada 里面“导演”一词的含义其实就是管理员，拥有创建机器人，并管理机器人学习列表和服务列表的权限。

最原初的管理员就是登录 wxbot 的账号自己，因为每一个微信账号都不可能凭空出现，背后肯定是有个人的，且部分操作，比如关注公众号等这个也只有用该账号对应的真实客户端进行操作，所以用自身账号作为原初导演账号是最自然的。也无需用户自己
做额外的设置，只需要拿起登录的实际设备操作即可。
另外原初导演可以指定 co_director, co_director理论上拥有原初导演一样的权限，但是有些操作目前程序是无法实现的，毕竟我们不是做遥控终端。

无论是创建 bot、指定服务清单、指定学习源，还是删除bot、删除服务清单、删除学习源，因为目前没有对普通用户特别友好的方式获取wxid，所以只能通过群聊操作进行，当然程序还是保留了私聊操作的代码，只是需要用户自己先想办法获取对应的 wxid
然而，如果用户能做到这一点，我想他会更加倾向于直接修改本地 json 文件……因此目前weixin.py中仅实现的是以群聊为单位创建 bot，开启（同时具有服务和学习）、关闭（直接同时 bot 对应的服务，包括关联的学习源群和服务群），添加学习源，添加服务源。

另外目前没办法很好的通过微信对话操作公众号的学习源分配，所以所有关注的公众号消息都会且只会累积到一个 default 的 bot_id下，用户需要手动配置这个 bot 的服务列表和其他内容。用户也可以手动配置公众号（gh_开头)id 到某个 bot 的学习源中，此时该公众号不会被 default 学习。
default bot 不必 手动创建，第一次完整启动后会自己创建，之后用户可以编辑 avatars 下面的 default.json。
另外提供了一个方便获取群聊id 和用户 id 的指令，但仅限于原初导演账号

导演和 co_director列表储存于同级目录下的 directors.json中（如有）
"""
# 千万注意扫码登录时不要选择“同步历史消息”，否则会造成 bot 上来挨个回复历史消息

logger = get_logger(logger_name='weixin', logger_file_path='projects_data')

# 先检查下 wx 的登录状态，同时获取已登录微信的 wxid
WX_BOT_ENDPOINT = os.environ.get('WX_BOT_ENDPOINT', '127.0.0.1:8066')
wx_url = f"http://{WX_BOT_ENDPOINT}/api/"
try:
    # 发送GET请求
    response = httpx.get(f"{wx_url}checklogin")
    response.raise_for_status()  # 检查HTTP响应状态码是否为200

    # 解析JSON响应
    data = response.json()

    # 检查status字段
    if data['data']['status'] == 1:
        # 记录wxid
        self_wxid = data['data']['wxid']
        logger.info(f"已登录微信账号: {self_wxid}")
    else:
        # 抛出异常
        logger.error("未检测到任何登录信息，将退出")
        raise ValueError("登录失败，status不为1")
except Exception as e:
    logger.error(f"无法链接微信端点:{wx_url}, 错误：\n{e}")
    raise ValueError("登录失败，无法连接")

# 获取登录微信昵称，用于后面判断是否@自己的消息
response = httpx.get(f"{wx_url}userinfo")
response.raise_for_status()  # 检查HTTP响应状态码是否为200
# 解析JSON响应
data = response.json()
self_nickname = data['data'].get('nickname', " ")
logger.info(f"self_nickname: {self_nickname}")

if os.path.exists('directors.json'):
    logger.info("directors.json exists, loading...")
    with open('directors.json', 'r', encoding='utf-8') as f:
        directors = json.load(f)
else:
    directors = [self_wxid]

logger.info(f"directors: {directors}")

# 扫描配置文件、加载已创建的机器人配置
# 注意目前先只支持 同一个源或者同一个被服务对象只对应一个 bot
config_folder_path = os.environ.get("CONFIGS", "avatars")
config_files = [file for file in os.listdir(config_folder_path) if file.endswith('.json')]
logger.info(f"total {len(config_files)} config files from {config_folder_path}")
learn_sources_map = {}
service_list_map = {}
config_file_map = {}
for file in config_files:
    config_file = os.path.join(config_folder_path, file)
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    _bot_id = config.get("bot_id", "")
    if not _bot_id:
        _bot_id = 'default'
    config_file_map[_bot_id] = config_file
    learn_sources = config.get("learn_sources", [])
    for source in learn_sources:
        learn_sources_map[source] = _bot_id
    service_list = config.get("service_list", [])
    for service in service_list:
        service_list_map[service] = _bot_id

# 检查 default 配置是否存在，不存在则创建
if "default" not in config_file_map:
    config_file_map["default"] = os.path.join(config_folder_path, "default.json")
    config = config_template

    with open(config_file_map["default"], 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# 导演功能
director_codes = {"add_source_to": "/add_source",
                  "start": "/start",
                  "add_service_to": "/add_service",
                  "stop": "/stop",
                  "co_director": "/promotion",
                  "refresh": "/refresh",
                  "bot_list": "/list"}

director_guide = f"""指令列表如下:
•为群聊配置智能体 - 在要配置智能体的群中发送： {director_codes['start']}
•添加学习源到智能体 - 在要被添加为学习源的群中发送： {director_codes['add_source_to']} <bot_id>
•停止群聊的一切功能 - 在目标群中发送： {director_codes['stop']}
•为智能体添加新的服务对象群 - 在要被服务的群中发送： {director_codes['add_service_to']} <bot_id>
•刷新群成员（更新服务对象） - 在要刷新的群中发送： {director_codes['refresh']}
•获取所有已生效的智能体列表 - 对我发送： {director_codes['bot_list']}"""

config_lock = asyncio.Lock()

async def get_room_member_ids(room_id: str) -> list[str]:
    if not room_id.endswith('@chatroom'):
        # 特别危险，会直接导致 wxbot container错误……
        return []
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{wx_url}dbchatroom?wxid={room_id}")
        if response.status_code != 200:
            logger.error(f"can not get chatroom info for {room_id}")
            return []
        res = response.json()
        result = list(res['data']['Members'].keys())
        if self_wxid in result:
            result.remove(self_wxid)
        return result

async def get_bot_list() -> list[dict]:
    bot_id_name_dict = {}
    for bot_id, config_file in config_file_map.items():
        config = await aio_config_load(config_file)
        if not config: continue
        bot_id_name_dict[bot_id] = config['bot_name'] if config['bot_name'] else "未配置"
    if not bot_id_name_dict:
        reply = f"目前没有创建任何智能体，请先创建一个智能体。在任意我在的群聊中，发送：{director_codes['start']}"
    else: reply = "\n".join([f"{name}: {bot_id}" for bot_id, name in bot_id_name_dict.items()])
    return [{"type": "text", "answer": reply}]

# 如下所有功能请注意：目前设定一个群只能对应一个 bot 的学习源或者服务源（这二者是分开的），重复设置会直接冲掉前面的设置
async def start_wx_bot(room_id: str) -> list[dict]:
    global config_file_map
    # 目前方案获取不到群聊名称，需要导演指定
    if room_id in config_file_map:
        config = await aio_config_load(config_file_map[room_id])
    else:
        config = config_template
        config_file_map[room_id] = os.path.join(config_folder_path, f"{room_id}.json")

    config["bot_id"] = room_id
    service_list = await get_room_member_ids(room_id)
    config["service_list"].extend(service_list)
    config["service_list"].append(room_id)
    config["service_list"] = list(set(config["service_list"]))
    config["learn_sources"] = [room_id]
    async with config_lock:
        await aio_save_config(config, config_file_map[room_id])

    return [{"type": "text", "answer": f"已为群聊{room_id}创建组织内知识智能体初始配置文件{config_file_map[room_id]}，"
                                       f"请编辑文件完成详细配置后重启 awada 后端和 weixin 服务，在这之前智能体不会生效"}]

async def add_source_to(room_id: str, bot_id: str) -> list[dict]:
    global learn_sources_map
    if bot_id not in config_file_map:
        return [{"type": "text", "answer": f"未找到对应 {bot_id} 的机器人配置文件，请先创建该机器人配置文件，再添加学习源"}]
    if room_id in learn_sources_map and learn_sources_map[room_id] != bot_id:
        return [{"type": "text", "answer": f"{room_id} 已经被 {learn_sources_map[room_id]} 添加为学习源，无法再次添加"}]
    if room_id in learn_sources_map and learn_sources_map[room_id] == bot_id:
        return [{"type": "text", "answer": f"{room_id} 已经被 {bot_id} 添加为学习源，无需重复添加"}]

    config = await aio_config_load(config_file_map.get(bot_id, ""))
    if not config: return [{"type": "text", "answer": f"智能体 {bot_id} 配置文件异常，请检查后再操作"}]
    config["learn_sources"].append(room_id)
    async with config_lock:
        learn_sources_map[room_id] = bot_id
        await aio_save_config(config, config_file_map[bot_id])

    return [{"type": "text", "answer": f"已为 {room_id} 添加到 {bot_id} 的学习源，{bot_id} 将会主动学习该群聊信息"}]

async def add_service_to(room_id: str, bot_id: str) -> list[dict]:
    global service_list_map
    if bot_id not in config_file_map:
        return [{"type": "text", "answer": f"未找到对应 {bot_id} 的机器人配置文件，请先创建该机器人配置文件，再添加服务对象"}]
    if room_id in service_list_map and service_list_map[room_id] != bot_id:
        return [{"type": "text", "answer": f"{room_id} 已经被 {service_list_map[room_id]} 添加为服务对象，无法再次添加"}]
    if room_id in service_list_map and service_list_map[room_id] == bot_id:
        return [{"type": "text", "answer": f"{room_id} 已经被 {bot_id} 添加为服务对象，无需重复添加"}]

    if room_id.endswith('@chatroom'):
        service_list = await get_room_member_ids(room_id)
        service_list.append(room_id)
    else: service_list = [room_id]

    config = await aio_config_load(config_file_map[bot_id])
    if not config: return [{"type": "text", "answer": f"智能体 {bot_id} 配置文件异常，请检查后再操作"}]
    config["service_list"].extend(service_list)
    config["service_list"] = list(set(config["service_list"]))
    async with config_lock:
        await aio_save_config(config, config_file_map[bot_id])
        for wxid in service_list:
            service_list_map[wxid] = bot_id
    return [{"type": "text", "answer": f"已将贵群内所有成员添加到 {bot_id} 的服务清单。"}]

async def stop_any(room_id: str) -> list[dict]:
    global service_list_map, config_file_map, learn_sources_map
    if room_id in config_file_map:
        async with config_lock:
            del config_file_map[room_id]

    if room_id in learn_sources_map:
        async with config_lock:
            bot_id = learn_sources_map.pop(room_id)
            config = await aio_config_load(config_file_map.get(bot_id, ""))
            if config:
                if room_id in config["learn_sources"]: config["learn_sources"].remove(room_id)
                await aio_save_config(config, config_file_map[bot_id])

    if room_id in service_list_map:
        if room_id.endswith('@chatroom'):
            service_list = await get_room_member_ids(room_id)
            service_list.append(room_id)
        else:
            service_list = [room_id]
        async with config_lock:
            bot_id = service_list_map.pop(room_id)
            config = await aio_config_load(config_file_map.get(bot_id, ""))
            if config:
                if room_id in config["service_list"]: config["service_list"].remove(room_id)
                for wxid in service_list:
                    service_list_map.pop(wxid, None)
                    if room_id in config["service_list"]: config["service_list"].remove(wxid)
                await aio_save_config(config, config_file_map[bot_id])
            else:
                for wxid in service_list: service_list_map.pop(wxid, None)

    return [{"type": "text", "answer": f"已将 {room_id} 从所有学习源中取消，同时{room_id}以及所有成员从服务清单中移除，对应的 bot 也已解除关联（配置文件未删除，请手动处理，谨防不良后果）。"}]

async def co_director_prompt(room_id: str) -> list[dict]:
    global directors
    add_list = await get_room_member_ids(room_id)
    async with config_lock:
        directors.extend(add_list)
        directors = list(set(directors))
        await aio_save_config(directors, 'directors.json')

    logger.info(f"directors list updated: {directors}")
    for director in add_list:
        if director == self_wxid: continue
        await send_msg(director, [{"type": "text", "answer": f"您已被添加为组织知识智能体 {self_nickname} 的协作导演。{director_guide}"}])
    return [{"type": "text", "answer": f"已将 {room_id} 所有成员添加为协同导演"}]

async def refresh_any(room_id: str) -> list[dict]:
    global service_list_map
    if not room_id.endswith('@chatroom'):
        return [{"type": "text", "answer": f"{director_codes['refresh']}仅限群聊操作"}]

    if room_id not in service_list_map:
        return [{"type": "text",
                 "answer": f"{room_id} 未对应任何智能体，要添加群聊所有成员为某智能体服务对象，请在群聊中发送：{director_codes['add_service_to']} <bot_id>"}]

    bot_id = service_list_map[room_id]
    config = await aio_config_load(config_file_map.get(bot_id, ""))
    if not config: return [{"type": "text", "answer": f"智能体 {bot_id} 配置文件异常，请检查后再操作"}]

    async with config_lock:
        service_rooms = []
        for wxid in config["service_list"]:
            del service_list_map[wxid]
            if wxid.endswith('@chatroom'): service_rooms.append(wxid)

    # 重新拿一下所有 room 的成员列表，不这样做的话，无法剔除已经退群的成员
    service_list = []
    for r_id in service_rooms:
        service_list.extend(await get_room_member_ids(r_id))

    service_list.extend(service_rooms)
    service_list = list(set(service_list))
    config["service_list"] = service_list
    async with config_lock:
        for wxid in service_list:
            service_list_map[wxid] = bot_id
        await aio_save_config(config, config_file_map[bot_id])
    return [{"type": "text", "answer": f"已更新 {room_id} 中所有成员为 {bot_id} 的服务对象"}]


async def send_msg(user_id: str, contents: list[dict], at_list: Optional[list] = None):
    """
    user_id 请使用 wxid，包括群聊的 id （@chatroom 结尾，要写全）
    room at 信息说明：如果是群聊艾特消息，那么content字段中的@艾特符号数量需要和atlist中的被艾特人数组长度一致，简单来说，就是atlist中有多少个被艾特人的wxid，那么content字段中就需要有多少个艾特组合，位置随意，
    例如： {"wxid": "xx@chatroom", "content": "这里@11 只是@22 想告诉你@33 每个被艾特人的位置并不重要", "atlist": ["wxid_a", "wxid_b", "wxid_c"]} 每个被艾特人在content中 固定为@[至少两个字符的被艾特人名] + 一个空格！ 
    如果是发送@所有人消息，那么请在atlist字段中仅传入一个notify@all字符串，content字段中仅包含一个@符号规范（最少两字符+一个空格）， 一般建议是@所有人见名知意
    """
    i = 1
    for content in contents:
        if content["type"] == "text":
            endpoint = f"{wx_url}sendtxtmsg"
            if user_id.endswith("@chatroom") and at_list:
                body = {"wxid": user_id, "content": content["answer"], "atlist": at_list}
            else:
                body = {"wxid": user_id, "content": content["answer"]}
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=body)
                if response.status_code != 200:
                    logger.error(f"send message failed: {response.text}")
        elif content["type"] == "image":
            # 这部分有待测试，实例代码和接口文档不一致
            # 示例代码：https://github.com/jwping/wxbot/blob/main/python_client/main.py
            if not is_file_exists(content["answer"]):
                logger.warning(f"file {content['answer']} does not exist or not a file, aborting sending")
            endpoint = f"{wx_url}sendimgmsg"
            data = {"wxid": user_id}
            path = content["answer"]
            # 打开文件并读取为文件对象
            with open(path, 'rb') as file:
                # 构建 POST 请求的文件部分
                files = {'image': file}
                async with httpx.AsyncClient() as client:
                    response = await client.post(endpoint, data=data, files=files)
                    if response.status_code != 200:
                        logger.error(f"send file failed: {response.text}")
        elif content["type"] == "file":
            # 实测下来接口文档中提到的 path 方案不可用，表现为能够成功提交，但实际消息发不出去，也没有任何报错（返回的 code 是200）
            # 实例代码给出的方案实测下来只能成功发送 txt 和 docx 文件，其他文件表现跟传 path 方案一样
            # 实测下来只有 base64方案能发文件，但也不能保证每次都成功
            if not is_file_exists(content["answer"]):
                logger.warning(f"file {content['answer']} does not exist or not a file, aborting sending")
            endpoint = f"{wx_url}sendfilemsg"
            base64 = await read_file_as_base64(content["answer"])
            # filename = os.path.basename(content["answer"])
            # 这里有个超级大坑：这里的文件名不能用中文（至少使用 docker wxbot 的情况下）
            file_ext = os.path.splitext(content["answer"])[-1]
            filename = f"reference_file_{i}{file_ext}"
            data = {
                'wxid': user_id,
                'file': base64,
                'filename': filename
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=data)
                if response.status_code != 200:
                    logger.error(f"send file failed: {response.text}")
            i += 1

async def director_codes_handler(*args) -> list[dict]:
    logger.info(f"director codes handler: {args}")
    if args[0] == director_codes["add_source_to"]:
        if len(args) < 3:
            return [{"type": "text", "answer": f"为智能体添加新的服务对象群 - 在要被服务的群中发送： {director_codes['add_service_to']} <bot_id>"}]
        else:
            return await add_source_to(args[1], args[2])

    elif args[0] == director_codes["start"]:
        if len(args) < 2:
            return [{"type": "text", "answer": f"为群聊配置智能体 - 在要配置智能体的群中发送： {director_codes['start']}"}]
        else:
            return await start_wx_bot(args[1])

    elif args[0] == director_codes["stop"]:
        if len(args) < 2:
            return [{"type": "text", "answer": f"停止群聊的一切功能 - 在目标群中发送： {director_codes['stop']}"}]
        else:
            return await stop_any(args[1])

    elif args[0] == director_codes["add_service_to"]:
        if len(args) < 3:
            return [{"type": "text", "answer": f"为智能体添加新的服务对象群 - 在要被服务的群中发送： {director_codes['add_service_to']} <bot_id>"}]
        else:
            return await add_service_to(args[1], args[2])

    elif args[0] == director_codes["co_director"]:
        if len(args) < 2:
            return [{"type": "text", "answer": f'Usage: {director_codes["co_director"]}'}]
        else:
            return await co_director_prompt(args[1])

    elif args[0] == director_codes["refresh"]:
        if len(args) < 2:
            return [{"type": "text", "answer": f"刷新群成员（更新服务对象） - 在要刷新的群中发送： {director_codes['refresh']}\n"}]
        else:
            return await refresh_any(args[1])
    else:
        return [{"type": "text", "answer": f"未匹配正确的导演指令。{director_guide}"}]


# The XML parsing scheme is not used because there are abnormal characters in the XML code extracted from the weixin public_msg
item_pattern = re.compile(r'<item>(.*?)</item>', re.DOTALL)
url_pattern = re.compile(r'<url><!\[CDATA\[(.*?)]]></url>')
summary_pattern = re.compile(r'<summary><!\[CDATA\[(.*?)]]></summary>', re.DOTALL)

service_url = os.environ.get('AWADA_ENDPOINT', 'http://127.0.0.1:8077/')
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
                        if "StrTalker" not in data or "Content" not in data:
                            logger.warning(f"invalid data:\n{data}")
                            continue
                        user_id = data["StrTalker"]
                        bot_id = learn_sources_map.get(user_id, 'default')

                        items = item_pattern.findall(data["Content"])
                        # Iterate through all < item > content, extracting < url > and < summary >
                        for item in items:
                            url_match = url_pattern.search(item)
                            url = url_match.group(1) if url_match else None
                            if not url:
                                logger.warning(f"can not find url in \n{item}")
                                continue
                            # URL processing, http is replaced by https, and the part after chksm is removed.
                            url = url.replace('http://', 'https://')
                            cut_off_point = url.find('chksm=')
                            if cut_off_point != -1:
                                url = url[:cut_off_point - 1]

                            summary_match = summary_pattern.search(item)
                            addition = summary_match.group(1) if summary_match else None
                            post_body = {"user_id": user_id, "type": "url", "content": url, "addition": addition, "bot_id": bot_id}
                            async with httpx.AsyncClient() as client:
                                response = await client.post(f"{service_url}feed", json=post_body)
                            if response.status_code != 200:
                                logger.warning(f"failed to post to service, 响应内容: {response.text}")
                                for director in directors:
                                    await send_msg(director, [{'type': 'text', 'answer': "[惊恐]后端服务feed 接口异常，请去排查"}])
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection closed with exception: {e}")
            reconnect_attempts += 1
            if reconnect_attempts <= max_reconnect_attempts:
                logger.info(f"Reconnecting attempt {reconnect_attempts}...")
                await asyncio.sleep(1)
            else:
                logger.error("Max reconnect attempts reached. Exiting.")
                for director in directors:
                    await send_msg(director, [{'type': 'text', 'answer': "[惊恐]公众号消息接口断了，快去看看吧"}])
                break
        except Exception as e:
            logger.error(f"PublicMsgHandler error: {e}")
            error_message = str(e)
            if error_message:
                for director in directors:
                    await send_msg(director, [{'type': 'text', 'answer': f"[惊恐]公众号消息提交后台process错误\n{error_message}"}])


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
                        """
                        目前使用的wx-bot 方案来自：https://github.com/jwping/wxbot
                        创建群聊、解散群聊、管理群聊这些都不支持
                        添加好友、接受好友申请这些也不支持，
                        关注公众号、解除关注公众号这些也不支持，
                        如上都需要在实际登录的手机上进行操作
                        另外，获取图片、视频和文件信息，只能获取通知，拿不到文件本身（需要额外的代码），所以无法通过个微上传文件，需要使用企微或者服务器上用 qanyting 的界面（推荐）
                        用户主动离群的消息也拿不到。
                        获取的信息是以list[dict]形式给到的，每一个 dict 目前用到的字段就是：'IsSender'、'Sender'、'StrContent'、 'StrTalker'、 'Type'、 'SubType'、 'Content'
                        其中：
                        'Content' 只有'Type'49，也就是公众号文章卡片信息（'SubType' 5）或者引用消息（'SubType' 57）是才有；
                        'Sender' 只有在'IsSender'为1，也就是bot 自己发的消息时才有，如果是群聊消息可以在这里解析出 at user list
                        'StrTalker' 如果是别人发给 bot 的，这里是发送人的 wxid，如果是 bot 发给别人的，这是是接收人的wxid，但注意，如果是群聊，则无论如何是群聊 wxid（以@chatroom结尾）
                        """
                        # 目前仅处理文本消息、文件和url（微信公众号分享卡片）三类消息
                        # 如需更多类型消息，请看 wxbot各类型信息原始json格式.txt
                        user_id = data["StrTalker"]
                        if data['Type'] == '1':
                            # 先判断是否自己的消息以及是否群聊消息
                            is_self = True if data["IsSender"] == "1" else False
                            is_room = True if user_id.endswith("@chatroom") else False

                            if is_self and not is_room: continue

                            content = data["StrContent"]

                            if not is_room and content.startswith("/") and user_id in directors:
                                if content == director_codes['bot_list']:
                                    await send_msg(user_id, await get_bot_list())
                                    continue
                                commands = content.split(" ")
                                commands = [command for command in commands if command.strip()]
                                reply = await director_codes_handler(*commands)
                                await send_msg(user_id, reply)
                                continue

                            # 群聊消息，判断是否导演指令，如果不是记录是否自己被 at，都不是的话可以忽略了
                            atlist = None
                            if is_room:
                                sender = data['Sender']
                                if (is_self or sender in directors) and content.startswith("/"):
                                    commands = content.split(" ")
                                    commands = [command.strip() for command in commands if command.strip()]
                                    commands.insert(1, user_id)
                                    reply = await director_codes_handler(*commands)
                                    await send_msg(user_id, reply)
                                    continue

                                if is_self: continue
                                if user_id not in service_list_map: continue
                                if f"@{self_nickname} " not in content: continue

                                content = content.replace(f"@{self_nickname} ", "")
                                async with httpx.AsyncClient() as client:
                                    response = await client.get(f"{wx_url}dbaccountbywxid?wxid={sender}")
                                    if response.status_code != 200:
                                        logger.error(f"can not get info for {sender}")
                                    else:
                                        res = response.json()
                                        if len(res["data"]["NickName"]) < 2:
                                            nickname = f'{res["data"]["NickName"]}  '
                                        else:
                                            nickname = res["data"]["NickName"]
                                        atlist = (nickname, sender)

                            if user_id not in service_list_map: continue

                            input_data = {
                                "user_id": user_id,
                                "type": "text",
                                "content": content,
                                "bot_id": service_list_map[user_id]
                            }
                            async with httpx.AsyncClient(timeout=httpx.Timeout(24.88)) as client:
                                response = await client.post(f"{service_url}dm", json=input_data)
                                if response.status_code != 200:
                                    logger.warning(f"failed to post to service, 响应内容: {response.text}")
                                    res = {'flag': 1, 'result': [{'type': 'text', 'answer': "[惊恐]后端服务异常，请管理员速去排查"}]}
                                else:
                                    res = response.json()

                            if atlist:
                                nickname, wxid = atlist
                                res['result'][0]['answer'] = f"{res['result'][0]['answer']} @{nickname} "
                                await send_msg(user_id, res['result'], at_list=[wxid])
                            else:
                                await send_msg(user_id, res['result'])

                            if res['flag'] == 1 or res['flag'] < -2:
                                for director in directors:
                                    await send_msg(director, res['result'])

                        elif data['Type'] == '49':
                            if user_id not in learn_sources_map: continue
                            if data['SubType'] != '5':
                                # 非文章形式的公众号消息，比如公众号发来的视频卡
                                continue
                            content = data["Content"]
                            item = re.search(r'<url>(.*?)&amp;chksm=', content, re.DOTALL)
                            if not item:
                                logger.debug("shareUrlOpen not find")
                                item = re.search(r'<shareUrlOriginal>(.*?)&amp;chksm=', content, re.DOTALL)
                                if not item:
                                    logger.debug("shareUrlOriginal not find")
                                    item = re.search(r'<shareUrlOpen>(.*?)&amp;chksm=', content, re.DOTALL)
                                    if not item:
                                        logger.warning(f"cannot find url in \n{content}")
                                        return
                            extract_url = item.group(1).replace('amp;', '')
                            summary_match = re.search(r'<des>(.*?)</des>', content, re.DOTALL)
                            summary = summary_match.group(1) if summary_match else None
                            logger.debug(f"parsed source:{user_id}, url: {extract_url}")
                            post_body = {"user_id": user_id, "type": "url", "content": extract_url, "addition": summary, "bot_id": learn_sources_map[user_id]}
                            async with httpx.AsyncClient() as client:
                                response = await client.post(f"{service_url}feed", json=post_body)
                            if response.status_code != 200:
                                logger.warning(f"failed to post to service, 响应内容: {response.text}")
                                for director in directors:
                                    await send_msg(director, [{'type': 'text', 'answer': "后端服务feed 接口异常，快去看看吧[惊恐]"}])
                        elif data['Type'] == '10000':
                            if not user_id.endswith("@chatroom"): continue
                            if user_id not in service_list_map: continue
                            if data['StrContent'].endswith("已解散该群聊"):
                                # 群聊解散，stop any：
                                _ = await stop_any(user_id)
                                logger.info(f"群 {user_id} 已解散，停止所有服务，解除所有学习源，解除所有关联智能体（配置文件保留）")
                                for director in directors:
                                    await send_msg(director, [{'type': 'text', 'answer': f"群 {user_id} 已解散，停止所有服务，解除所有学习源，解除所有关联智能体（配置文件保留）"}])
                            elif data['StrContent'].endswith("移出了群聊") or data['StrContent'].endswith("加入了群聊"):
                                # 新成员入群或者有人被清理（主动退群没消息），这个时候虽然拿不到入群和退群人的 wxid，但是可以刷新群
                                logger.info(f"{user_id} 成员变动，refreshing")
                                await asyncio.sleep(10)
                                reply = await refresh_any(user_id)
                                logger.debug(f"refresh group: {reply}")
                        else:
                            continue
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection closed with exception: {e}")
            reconnect_attempts += 1
            if reconnect_attempts <= max_reconnect_attempts:
                logger.info(f"Reconnecting attempt {reconnect_attempts}...")
                await asyncio.sleep(1)
            else:
                logger.error("Max reconnect attempts reached. Exiting.")
                for director in directors:
                    await send_msg(director, [{'type': 'text', 'answer': "[惊恐]通用消息接口断了，快去看看吧!"}])
                break
        except Exception as e:
            logger.error(f"GeneralMsgHandler error: {e}")


async def main():
    uri_general = f"ws://{WX_BOT_ENDPOINT}/ws/generalMsg"
    uri_public = f"ws://{WX_BOT_ENDPOINT}/ws/publicMsg"

    # 创建并行任务
    task1 = asyncio.create_task(get_general_msg(uri_general))
    task2 = asyncio.create_task(get_public_msg(uri_public))

    # 等待所有任务完成
    await asyncio.gather(task1, task2)


# 使用asyncio事件循环运行main coroutine
asyncio.run(main())
