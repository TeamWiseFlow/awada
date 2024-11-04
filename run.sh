#!/bin/bash

# export CONFIGS='avatars'
export LLM_API_BASE='http://127.0.0.1:9997/v1'
# export LLM_API_KEY='your_api_key_here'  # 如果需要 API 密钥，请取消注释并设置
# export QANYTHING_LOCATION='/home/dsw'
export HTML_PARSE_MODEL='qwen2.5-instruct'
# export VERBOSE=True

uvicorn main:app --host 0.0.0.0 --port 8077