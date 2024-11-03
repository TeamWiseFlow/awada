#!/bin/bash

# export CONFIGS='avatars'
export LLM_API_BASE='http://127.0.0.1:9997/v1'
# export LLM_API_KEY='your_api_key_here'  # 如果需要 API 密钥，请取消注释并设置
export VERBOSE=True
export AWADA_ENDPOINT='http://127.0.0.1:7777/'

python schedule_tasks.py