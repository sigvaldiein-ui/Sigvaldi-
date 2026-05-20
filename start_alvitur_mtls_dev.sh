#!/bin/bash
uvicorn interfaces.web_server:app \
    --host 0.0.0.0 --port 8003 \
    --ssl-keyfile config/server_key.pem \
    --ssl-certfile config/server_cert.pem \
    --ssl-ca-certs config/alvitur_root_ca.pem \
    --ssl-cert-reqs 2
