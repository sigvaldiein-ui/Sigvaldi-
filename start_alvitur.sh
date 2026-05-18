#!/bin/bash
# Alvitur production startup — með PATH fixi (Lærdómur #94)
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export PYTHONPATH="/workspace/Sigvaldi-:$PYTHONPATH"
cd /workspace/Sigvaldi-
export PYTHONDONTWRITEBYTECODE=1
export VAULT_STRICT_NO_EXTERNAL=false

while true; do
    # Lærdómur #95: ekki ræsa ef port er þegar í notkun
    if ss -tlnp | grep -q ':8000'; then
        echo "Port 8000 þegar í notkun — bíð..."
        sleep 10
        continue
    fi
    /usr/bin/python3 -m uvicorn interfaces.web_server:app \
        --host 0.0.0.0 --port 8000 --log-level warning
    echo "Uvicorn hrundi — endurræsi eftir 5 sek..."
    sleep 5
done
