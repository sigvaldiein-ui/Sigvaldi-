#!/bin/bash
cd /workspace/Sigvaldi-
export JWT_PRIVATE_KEY=$(cat jwt_private.pem)
export JWT_PUBLIC_KEY=$(cat jwt_public.pem)
exec /workspace/venv-v2/bin/python3 -m uvicorn interfaces.web_server:app --host 0.0.0.0 --port 8000 --log-level info
