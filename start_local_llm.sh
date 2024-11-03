#!/bin/bash

# 启动 xinference-local 并将其放到后台运行，同时保持输出到终端
xinference-local --host 0.0.0.0 --port 9997 &

# 获取 xinference-local 的进程 ID
XINFERENCE_PID=$!

# 等待几秒钟，确保 xinference-local 已经启动
sleep 10

# 启动 xinference launch
xinference launch --model-engine vllm --gpu_memory_utilization 0.9 --model-name qwen2.5-instruct --size-in-billions 7 --model-format gptq --quantization Int8

# 等待 xinference-local 进程结束
wait $XINFERENCE_PID
