#!/bin/bash
# Cache busting fyrir app_v3.js — býr til hash-aða útgáfu og uppfærir index.html
set -e
cd /workspace/Sigvaldi-
HASH=$(sha256sum interfaces/static/app_v3.js | cut -c1-8)
NEW_FILE="interfaces/static/app_v3.${HASH}.js"
cp interfaces/static/app_v3.js "$NEW_FILE"
sed -i "s|/static/app_v3.js?v=[0-9]*|/static/app_v3.${HASH}.js|g" interfaces/index.html
echo "Búinn: $NEW_FILE"
echo "index.html uppfærður"
