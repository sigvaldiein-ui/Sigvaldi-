#!/bin/bash
export TELEGRAM_TOKEN=8581446527:AAHjeOCY90XzTNgmzElaiaKL_SgOvDVuag0
export OPENROUTER_API_KEY=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

echo "🧠 Mímir ræsir..."
while true; do
    python /workspace/mimir_bot_v2.py
    echo "⚠️ Mímir stöðvaðist - endurræsi eftir 10 sek..."
    sleep 10
done
