#!/bin/bash
# start_all.sh — Mímir uppsetning
# Sprint 20: AlviturBot tunnel (490c85db) bætt við
# Keyrir: agent_core + telegram bot + web_server + cloudflared tunnel

set -e

WORKSPACE=/workspace
MIMIR=$WORKSPACE/mimir_net
LOG=$WORKSPACE

echo "=== Mímir uppsetning ==="

# --- 1. Python pakkar ---
pip install -q fastapi uvicorn pydantic httpx requests tavily-python 2>/dev/null || true

# --- 2. Agent Core ---
echo "Ræsi Agent Core..."
cd $MIMIR
nohup python3 -u core/agent_core_v4.py >> $LOG/agent_core.log 2>&1 &
echo "Mímir Agent Core ræstur!"

# --- 3. Telegram Bot ---
echo "Ræsi Telegram Bot..."
nohup python3 -u interfaces/telegram_bot_v9_prod.py >> $LOG/telegram_bot.log 2>&1 &
echo "Mímir Bot ræstur!"

# --- 4. Web Server ---
echo "Ræsi Web Server..."
cd $MIMIR/interfaces
nohup python3 -u web_server.py >> $LOG/web_server.log 2>&1 &
echo "Web Server ræstur á porti 8000!"

# --- 5. Cloudflare Tunnel (AlviturBot) ---
echo "Ræsi Cloudflare Tunnel..."
sleep 3
TOKEN=$(grep -o 'eyJ[^ ]*' $MIMIR/config/cf_token.txt 2>/dev/null || cat $MIMIR/config/cf_token.txt | tr -d '\n\r ')
nohup cloudflared tunnel --no-autoupdate run --token $TOKEN \
    >> $LOG/mimir_net/logs/cloudflared.log 2>&1 &
echo "Cloudflare Tunnel ræstur!"

echo ""
echo "=== Allt ræst ==="
echo "Web:      http://localhost:8000"
echo "Tunnel:   AlviturBot (490c85db)"
echo "Lén:      https://alvitur.is"
