#!/bin/bash
pip install -r /workspace/requirements.txt -q
pkill -f mimir_bot_v2.py
pkill -f agent_core.py
sleep 2
nohup python /workspace/agent_core.py >> /workspace/mimir.log 2>&1 &
echo "Mímir Agent Core ræstur!"
nohup python3 /workspace/mimir_bot_v2.py >> /workspace/mimir.log 2>&1 &
echo "Mímir Bot ræstur!"
ln -sf $(python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())") /usr/local/bin/ffmpeg
tar -czf /workspace/mimir_backup_$(date +%Y%m%d).tar.gz /workspace/mimir_bot_v2.py /workspace/agent_core.py /workspace/start_all.sh /workspace/requirements.txt /workspace/LEIDBEININGAR.md 2>/dev/null
echo "Backup búinn!"
pip install pyTelegramBotAPI requests openai langchain langchain-openai langgraph openai-whisper -q
pip install python-dotenv -q
pip install pyTelegramBotAPI python-dotenv langchain langchain-openai langgraph openai-whisper -q
apt-get install -y tmux -q 2>/dev/null; nohup python /workspace/mimir_bot_v2.py > /workspace/mimir.log 2>&1 &
