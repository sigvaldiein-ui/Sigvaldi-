#!/bin/bash
# Sprint 81 #7 — Smoke test loop (án cron, fyrir RunPod)
# Keyrir tests/smoke.sh á 5 mín fresti og skráir í log skrá

LOG_DIR="/workspace/Sigvaldi-/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/smoke_$(date +%Y%m%d).log"

echo "=== Smoke loop ræst $(date) ===" >> "$LOG_FILE"

while true; do
    echo "" >> "$LOG_FILE"
    echo "=== Smoke test $(date) ===" >> "$LOG_FILE"
    bash /workspace/Sigvaldi-/tests/smoke.sh 8003 >> "$LOG_FILE" 2>&1
    echo "=== Lokið — exit kóði: $? ===" >> "$LOG_FILE"
    sleep 300  # 5 mínútur
done
