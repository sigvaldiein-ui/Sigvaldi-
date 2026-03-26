#!/bin/bash
# ==========================================
# 🛡️ MÍMIR STARTUP PROTOCOL (SOP) v3.2 - CLEAN ROOM
# ==========================================

echo "🧹 Skref 1: Hreinsa út alla gamla drauga..."
pkill -9 -f "telegram_bot.py" || echo "Enginn bot í gangi."

echo "⏳ Skref 2: Hvíld í 5 sekúndur (Port alignment)..."
sleep 5

echo "🚀 Skref 3: Ræsi Mímir v3.2 úr Rót (/workspace)..."
# Loggar fara í sérstaka logs möppu til að halda vinnusvæði hreinu
nohup python3 -u /workspace/telegram_bot.py >> /workspace/logs/mimir_live.log 2>&1 &

echo "⏳ Skref 4: Bíð eftir vélarrúminu..."
sleep 5

echo "📋 Skref 5: Staðfesting úr vélarrúminu (/workspace/logs/mimir_live.log):"
echo "---------------------------------------------------"
tail -n 15 /workspace/logs/mimir_live.log
echo "---------------------------------------------------"

echo "✅ VERKI LOKIÐ. Prófaðu /restart í Telegram núna!"