#!/bin/bash
# ============================================================
# start_alvitur_8003.sh — DEV MODE á porti 8003
# Regla #80: Dev/prod parallel — 8003 er dev, 8000 er prod
# Sprint 81: Robust uppsetning — hreinsar port og bíður eftir losun
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
    # Hreinsa portið ef eitthvað situr eftir
    old_pid=$(ss -tlnp | grep ':8003' | sed -n 's/.*pid=\([0-9]*\).*/\1/p')
    if [ -n "$old_pid" ]; then
        echo "Drep gamalt ferli á 8003 (PID $old_pid)..."
        kill -9 $old_pid 2>/dev/null
        sleep 1
    fi

    # Bíða eftir að portið losni
    while ss -tlnp | grep -q ':8003'; do
        echo "Port 8003 enn í notkun, bíð..."
        sleep 1
    done

    echo "Ræsi Alvitur DEV á porti 8003..."
    python3 -m uvicorn interfaces.web_server:app --host 0.0.0.0 --port 8003
    echo "Uvicorn hætti — endurræsi eftir 5 sek..."
    sleep 5
done
