#!/bin/bash
echo "🧠 Mímir ræsir (með PYTHONPATH)..."

# Segjum Python að leita í /workspace svo hann finni 'mimir_net' pakkann
export PYTHONPATH=$PYTHONPATH:/workspace

while true; do
    python3 /workspace/mimir_net/mimir_bot_v2.py
    echo "⚠️ Mímir stöðvaðist - endurræsi eftir 10 sek..."
    sleep 10
done
