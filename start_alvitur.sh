#!/bin/bash
cd /workspace/Sigvaldi-
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/workspace/Sigvaldi-
while true; do
    python3 -m uvicorn interfaces.web_server:app --host 0.0.0.0 --port 8000
    echo "Uvicorn hrundi — endurræsi eftir 5 sek..."
    sleep 5
done
export VAULT_STRICT_NO_EXTERNAL=false
