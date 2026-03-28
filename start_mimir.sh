#!/bin/bash
echo "🧠 Mímir ræsir (með PYTHONPATH á /workspace)..."

# Ræsum cron ef hann er ekki þegar í gangi
service cron start 2>/dev/null || true
echo "⏰ Cron í gangi"

# Segjum Python að leita í /workspace svo hann finni 'mimir_net' möppuna sem pakka
export PYTHONPATH=$PYTHONPATH:/workspace

while true; do
    # Ræsum bótinn
    python3 /workspace/mimir_net/mimir_bot_v2.py
    echo "⚠️ Mímir stöðvaðist - endurræsi eftir 10 sek..."
    sleep 10
done
