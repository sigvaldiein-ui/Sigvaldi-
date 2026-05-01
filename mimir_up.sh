#!/bin/bash
pkill -9 -f telegram_bot.py 2>/dev/null
sleep 2
nohup python3 /workspace/mimir_net/interfaces/telegram_bot.py >> /workspace/logs/mimir_live.log 2>&1 &
sleep 2
tail -n 5 /workspace/logs/mimir_live.log
