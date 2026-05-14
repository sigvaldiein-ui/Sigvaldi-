#!/bin/bash
# ============================================================
# start_alvitur_8003.sh — DEV MODE á porti 8003
# Regla #80: Dev/prod parallel — 8003 er dev, 8000 er prod
# ============================================================
cd /workspace/Sigvaldi-
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/workspace/Sigvaldi-
export VAULT_STRICT_NO_EXTERNAL=false
export ALVITUR_ENV=development

echo "=== DEV MODE ==="
echo "Port: 8003"
echo "Env:  development"
echo "========================="

while true; do
    echo "Ræsi Alvitur DEV á porti 8003..."
    python3 -m uvicorn interfaces.web_server:app --host 0.0.0.0 --port 8003
    echo "Uvicorn hætti — endurræsi eftir 5 sek..."
    sleep 5
done
