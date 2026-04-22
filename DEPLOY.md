# Alvitur Deploy Guide

Sprint 63 Track B — dev/prod separation and safe deploy.

## Port layout

| Port | Service | Role |
|------|---------|------|
| 8000 | web_server.py (PROD) | Alvitur endpoint for users |
| 8001 | nginx | PROD proxy entry (backup) |
| 8002 | vLLM Qwen3-32B-AWQ | Leid B sovereign fallback |
| 8003 | web_server.py (DEV) | Development sandbox |

## Environment files

- /workspace/.env       prod config (ALVITUR_ENV=prod, ALVITUR_PORT=8000)
- /workspace/.env.dev   dev  config (ALVITUR_ENV=dev,  ALVITUR_PORT=8003)

Both contain the same OPENROUTER_API_KEY. Neither is committed to git (see .gitignore).

## Start servers

PROD (default, reads /workspace/.env):

    nohup python3 -u interfaces/web_server.py > /workspace/web_server.log 2>&1 &

DEV (reads /workspace/.env.dev):

    ALVITUR_ENV=dev nohup python3 -u interfaces/web_server.py > /workspace/web_server_dev.log 2>&1 &

## Verify state

    curl -s http://localhost:8000/api/diagnostics | python3 -m json.tool
    curl -s http://localhost:8003/api/diagnostics | python3 -m json.tool

Expected fields:
- env: "prod" or "dev"
- port: 8000 or 8003
- version: current sprint tag
- leid_a_enabled: true if OpenRouter key valid
- leid_b_url: http://localhost:8002/v1/chat/completions

## Safe deploy (dev to prod)

    ./scripts/deploy_prod.sh

The script runs a 7-step verification:
1. Git state clean (warns on uncommitted changes)
2. DEV responding on 8003
3. DEV smoke test (text pipeline)
4. Leid A enabled on DEV
5. Restart PROD (and re-start DEV)
6. PROD responding after restart
7. PROD smoke test

Any failure aborts the deploy with a clear error message.

## Rollback

Backup files are created automatically on every change:

    interfaces/web_server.py.bak-<track>-<time>

Git tags mark stable points:
- v0.62-complete               last sprint baseline
- v0.63-pre-sprint             before Sprint 63
- v0.63-track-a-complete       Leid A + Leid B hybrid done
- v0.63-track-b-complete       dev/prod separation done

To roll back:

    git checkout v0.63-track-a-complete -- interfaces/web_server.py
    # or restore from backup
    cp interfaces/web_server.py.bak-trackB-b3-XXXX interfaces/web_server.py

## Troubleshooting

### Address already in use

Check which process holds the port:

    ss -tlnp | grep :<port>

Common conflicts: vLLM on 8002, nginx on 8001. Do not kill these.

### DEV will not start

    tail -30 /workspace/web_server_dev.log

Look for bind errors, missing env vars, or Python import errors.

### Leid A disabled

    curl -s http://localhost:8000/api/diagnostics

Check leid_a_key_length. Expected 70-80. If 0, .env did not load correctly.
