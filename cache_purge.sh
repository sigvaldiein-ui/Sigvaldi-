#!/bin/bash
# Sprint 81 #3 — Cloudflare Cache Purge automation
# Hreinsar allt skyndiminni fyrir alvitur.is

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Hlaða .env
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

if [ -z "$CF_API_TOKEN" ] || [ -z "$CF_ZONE_ID" ]; then
    echo "Villa: CF_API_TOKEN eða CF_ZONE_ID vantar í .env"
    exit 1
fi

echo "Hreinsa allt skyndiminni fyrir alvitur.is..."
RESP=$(curl -s -X POST \
    "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/purge_cache" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"purge_everything":true}')

SUCCESS=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))")

if [ "$SUCCESS" = "True" ]; then
    echo "✅ Cache purge tókst!"
    exit 0
else
    echo "❌ Cache purge mistókst:"
    echo "$RESP"
    exit 1
fi
