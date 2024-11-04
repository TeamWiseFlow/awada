import os,json
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from dm import DialogManager
from typing import Dict, Literal, Optional
from fastapi.middleware.cors import CORSMiddleware
from utils.general_utils import isURL, extract_urls, get_logger


# 每一个 avatar 的管理（导演、服务账号列表、学习源列表）都在connect 里面维护，dm 服务仅负责实现
# 但是connect 需要实时的把 avatar 的 config 放在config_folder_path下面
# 默认 bot 只允许有一个，此 bot 的 config 中可以不配置 bot_id,或者 bot_id留空，如果有多个这样的配置，只有最后一个会生效
logger = get_logger(logger_name='dm', logger_file_path='projects_data')
def load_configs() -> dict[str, DialogManager]:
    config_folder_path = os.environ.get("CONFIGS", "avatars")
    config_files = [file for file in os.listdir(config_folder_path) if file.endswith('.json')]
    dm_maps = {}
    for file in config_files:
        config_file = os.path.join(config_folder_path, file)
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        try:
            dm = DialogManager(config, config_file, logger)
        except Exception as e:
            logger.error(f"Error loading config file {config_file}: {e}")
            continue
        bot_id = config.get("bot_id", "")
        if not bot_id:
            dm_maps["default"] = dm
        else:
            dm_maps[bot_id] = dm
    return dm_maps


class Request(BaseModel):
    """
    Input model
    input = {“user_id”:”xxx”, “type”:”text”, 'content':str，'addition': Optional[str]}
    type限定为["text", "file", "image", "video", "location", "chathistory", "attachment", "url", "voice"]；

    注意：1、dm接口用于服务，feed 接口用于添加知识，call 为混合接口，会自动进行判断（基于 type 规则和 service_map、source_map)；
         2、dm接口目前只支持 text voice 和file 类型，feed 接口仅支持 file 和 url 类型，其余均为预留
         3、不管调用哪个接口，都会进行service_map、source_map规则判断
         4、提交feed（包括想通过 call 进行学习，user_id 填写 source 的 id，addition 为附加信息，比如公众号消息抽取出的摘要）
    """
    user_id: str
    type: Literal["text", "file", "image", "video", "location", "chathistory", "attachment", "url", "voice"]
    content: str
    addition: Optional[str] = None
    bot_id: Optional[str] = "default"


app = FastAPI(
    title="Awada Backend",
    description="From WiseFlow Team.",
    version="1.0.0",
    openapi_url="/openapi.json"
)

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

dm_maps = load_configs()
if not dm_maps:
    raise ValueError("No valid config files found.")

@app.get("/")
def read_root():
    msg = "Hello, this is Awada-1.0.0 Backend Service"
    return msg

@app.get("/reassemble")
def reassemble():
    global dm_maps
    dm_maps = load_configs()
    if not dm_maps:
        return "error-no dms"
    return "dm-reassembled"

@app.post("/dm")
async def service(request: Request) -> Dict:
    _input = request.model_dump()
    if _input["bot_id"] not in dm_maps:
        return {"flag": 3, "result": [{"type": "text", "answer": f"{_input['bot_id']} 未启动，无法提供服务"}]}
    return await dm_maps[_input["bot_id"]](_input)

@app.post("/feed")
async def learn(background_tasks: BackgroundTasks, request: Request):
    _input = request.model_dump()
    if _input["bot_id"] not in dm_maps:
        return {"flag": 3, "result": [{"type": "text", "answer": f"{_input['bot_id']} 未启动，无法提供服务"}]}

    _type = _input["type"]
    if _type == "file":
        return await dm_maps[_input["bot_id"]].add_file(_input)

    if _type == "url":
        if not isURL(_input["content"]):
            return dm_maps[_input["bot_id"]].build_out(-5, "invalid url")
        # cache = {'source': _input["user_id"], 'abstract': _input["addition"]}
        background_tasks.add_task(dm_maps[_input["bot_id"]].wiseflow, _input["content"], {})
        return dm_maps[_input["bot_id"]].build_out(0, "well received but you should check qanything dashboard for final result!")

    # 目前不太推荐使用 feed 接口的提交text 类型，如果是 call 接口，text 会自动归类为 service
    if _type == "text":
        urls = extract_urls(_input['content'])
        if not urls:
            # todo get info from text process （记一下功能整合）
            return dm_maps[_input["bot_id"]].build_out(1, "can not find any url in text")
        for url in urls:
            background_tasks.add_task(dm_maps[_input["bot_id"]].wiseflow, url, {})
        return dm_maps[_input["bot_id"]].build_out(0, "well received but you should check qanything dashboard for final result!")

    return dm_maps[_input["bot_id"]].build_out(-5, "invalid type")
