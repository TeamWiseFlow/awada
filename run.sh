#!/bin/bash
set -o allexport
source ../.env
set +o allexport
uvicorn backend:app --reload --host 0.0.0.0 --port 8066 &
python insights/background_task.py