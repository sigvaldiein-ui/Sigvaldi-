#!/bin/bash
# Ræsa supervisord með umhverfisbreytum úr .env
cd /workspace/Sigvaldi-
source .env
export CF_TUNNEL_TOKEN
supervisord -c /workspace/supervisor/supervisord.conf
echo "Supervisord started with CF_TUNNEL_TOKEN from .env"
