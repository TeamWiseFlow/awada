#!/bin/bash

# 设置环境变量
# export CONFIGS='avatars'
export LLM_API_BASE='http://127.0.0.1:9997/v1'
# export LLM_API_KEY='your_api_key_here'  # 如果需要 API 密钥，请取消注释并设置
# export QANYTHING_LOCATION='/home/dsw'  # 如果 Qanything 不在~下，请设置
export HTML_PARSE_MODEL='qwen2.5-instruct' # 通用网页解析器用到的大模型（微信文章解析用不到）
export VERBOSE=True # 是否输出详细日志（日志文件是否记录 debug 内容）
# export WX_BOT_ENDPOINT='127.0.0.1:8066' # wxbot Endpoint，默认本地8066端口则无需设置
# export MAIN_SERVICE_ENDPOINT='http://127.0.0.1:7777/' # 主服务 Endpoint，默认本地8077端口则无需设置

# 启动 uvicorn 服务，并监听代码变化
uvicorn main:app --host 0.0.0.0 --port 8077 --reload &
uvicorn_pid=$!

# 另开进程静默运行 weixin.py
python weixin.py &
weixin_pid=$!

# 另开进程静默运行 schedule_tasks.py
python schedule_tasks.py &
schedule_tasks_pid=$!

# 捕获 SIGINT 信号并终止所有后台进程
trap "kill $uvicorn_pid $weixin_pid $schedule_tasks_pid" SIGINT

# 等待所有后台进程结束
wait 