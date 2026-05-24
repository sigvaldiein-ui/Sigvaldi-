# Alvitur Operational Runbook — Supervisord

Created: 2026-05-24 — Sprint 102 operational hardening

## Architecture
Þrjár services managed by supervisord:
- alvitur-vllm (Port 8002, Priority 10)
- alvitur-qdrant (Port 6333, Priority 20)
- alvitur-uvicorn (Port 8000, Priority 30)

JWT keys eru loaded af wrapper script `start_uvicorn_supervisord.sh` áður en uvicorn fer í gang.

## Daily commands
- `supervisorctl status`
- `supervisorctl restart alvitur:*`
- `supervisorctl tail -f alvitur:alvitur-uvicorn`

## Deploy workflow
1. git pull origin main
2. supervisorctl restart alvitur:alvitur-uvicorn
