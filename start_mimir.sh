#!/bin/bash
echo "Raesi Mimir v7.0 Omni-Mind..."

# Ræsum cron ef hann er ekki þegar í gangi
service cron start 2>/dev/null || true
echo "Cron i gangi"

export PYTHONPATH=$PYTHONPATH:/workspace

while true; do
    python3 /workspace/mimir_net/interfaces/telegram_bot_v9_PROD.py
    echo "Mimir stadvaðist - endurraesi eftir 10 sek..."
    sleep 10
done
