#!/bin/bash
# Sprint 63 Track B4: Safe dev-to-prod deploy
# Usage: ./scripts/deploy_prod.sh

set -e

echo "==============================================="
echo "  ALVITUR DEPLOY PROD — Sprint 63 Track B"
echo "==============================================="

cd /workspace/Sigvaldi-

echo ""
echo "[1/7] Verify git state is clean"
if [ -n "$(git status --porcelain | grep -v '^??')" ]; then
    echo "  WARN: uncommitted changes detected"
    git status --short
    echo ""
    read -p "  Continue anyway? (y/N) " ans
    [ "$ans" != "y" ] && exit 1
fi

echo ""
echo "[2/7] Verify DEV is running on 8003"
if ! curl -s --max-time 3 http://localhost:8003/api/diagnostics > /tmp/dev_diag.json; then
    echo "  FAIL: DEV not responding on 8003"
    exit 1
fi
DEV_ENV=$(python3 -c "import json; print(json.load(open('/tmp/dev_diag.json'))['env'])")
if [ "$DEV_ENV" != "dev" ]; then
    echo "  FAIL: 8003 is not DEV (env=$DEV_ENV)"
    exit 1
fi
echo "  OK: DEV env=$DEV_ENV port=8003"

echo ""
echo "[3/7] Smoke test DEV (text + file)"
DEV_TEXT=$(curl -s -X POST http://localhost:8003/api/analyze-document -F "query=ping" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('pipeline_source', 'NONE'))")
if [ "$DEV_TEXT" = "NONE" ] || [ -z "$DEV_TEXT" ]; then
    echo "  FAIL: DEV text smoke broken"
    exit 1
fi
echo "  OK: DEV text pipeline=$DEV_TEXT"

echo ""
echo "[4/7] Verify Leid A enabled on DEV"
DEV_A=$(python3 -c "import json; print(json.load(open('/tmp/dev_diag.json'))['leid_a_enabled'])")
if [ "$DEV_A" != "True" ]; then
    echo "  FAIL: Leid A not enabled on DEV"
    exit 1
fi
echo "  OK: Leid A enabled"

echo ""
echo "[5/7] Restart PROD (8000)"
pkill -f "interfaces/web_server.py" 2>/dev/null
sleep 2
# Ressa einungis PROD - ekki kick-a dev
nohup python3 -u interfaces/web_server.py > /workspace/web_server.log 2>&1 &
sleep 5
# ALLTAF ressa dev aftur ef það var upp
ALVITUR_ENV=dev nohup python3 -u interfaces/web_server.py > /workspace/web_server_dev.log 2>&1 &
sleep 5

echo ""
echo "[6/7] Verify PROD is up"
PROD_DIAG=$(curl -s --max-time 5 http://localhost:8000/api/diagnostics)
if [ -z "$PROD_DIAG" ]; then
    echo "  FAIL: PROD not responding after restart"
    exit 1
fi
PROD_ENV=$(echo "$PROD_DIAG" | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['env'])")
PROD_VER=$(echo "$PROD_DIAG" | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['version'])")
echo "  OK: PROD env=$PROD_ENV version=$PROD_VER"

echo ""
echo "[7/7] Final smoke test on PROD"
PROD_PIPE=$(curl -s -X POST http://localhost:8000/api/analyze-document -F "query=ping" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('pipeline_source','NONE'))")
echo "  OK: PROD pipeline=$PROD_PIPE"

echo ""
echo "==============================================="
echo "  DEPLOY SUCCESS"
echo "==============================================="
