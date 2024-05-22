"""
self-hold Union Port
awada/lurker/consultant 对接前端的接口都用这一套
只提供一个接口 localhost:6666/union 给前端，
按插件模式同时提供给所有引入的模块（fastapi框架，多进程）
"""

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Literal, Optional
from fastapi.middleware.cors import CORSMiddleware

# add modules
from lurker import pipeline


class Request(BaseModel):
    """
    Input model
    遵循union统一入参格式
    input = {'user_id': str, 'type': str, 'content':str， 'addition': Optional[str]}
    type限定为text、voice和file（含图片、视频文件，中台通过文件后缀名判断处理）；

    注意：1、add_file 和 del_file, type 只能是 file； ask 接口type 为text或者voice，不然会返回 -5 wrong input；
         2、add_file content里面要写绝对路径，但是del_file 这里仅写文件名！
         3、add_file 如果需要指定file的额外信息（比如原始中文文件名，可以通过addition参数给出
    """
    user_id: str
    type: Literal["text", "voice", "file", "image", "video", "location", "chathistory", "contant", "attachment", "url"]
    content: str
    addition: Optional[str] = None


app = FastAPI(
    title="Awada-type Union Backend",
    description="From Wiseflow Team.",
    version="0.1.0",
    openapi_url="/openapi.json"
)

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def read_root():
    msg = "Hello, this is Awada-type Union Backend"
    return {"msg": msg}


@app.post("/union")
def no_return_call(background_tasks: BackgroundTasks, request: Request):
    background_tasks.add_task(pipeline, _input=request.model_dump())
    return {"msg": "received well"}
