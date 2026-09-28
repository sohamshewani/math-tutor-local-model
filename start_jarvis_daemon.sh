#!/bin/bash
cd ~/qwen_finetune
source ai_env/bin/activate

# Ensure MLX Server is running
if ! lsof -i :8080 > /dev/null; then
    nohup python -m mlx_lm.server --model mlx-community/Qwen2.5-7B-Instruct-4bit --adapter-path adapters --port 8080 > server.log 2>&1 &
    sleep 3
fi

# Launch Standalone HUD App
nohup python jarvis_app.py > jarvis.log 2>&1 &
