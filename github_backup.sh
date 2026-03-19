#!/bin/bash

# --- 🔑 ÞINN HLUTI ---
# Límdu ghp_ lykilinn þinn á milli gæsalappanna hér að neðan:
TOKEN="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"

# --- ⚙️ SJÁLFVIRKNI (ÉG HEF FYLLT ÚT ÞETTA) ---
USER="sigvaldiein-ui"
REPO="mimir-workspace"
EMAIL="sigvaldiein@gmail.com"

# 1. Stilla Git auðkenni
git config --global user.email "$EMAIL"
git config --global user.name "Sigvaldi"

# 2. Uppfæra fjar-tengingu (Remote) með lyklinum
# Þetta sér til þess að tölvan spyrji ALDREI um lykilorð
git remote add origin "https://$TOKEN@github.com/$USER/$REPO.git" 2>/dev/null
git remote set-url origin "https://$TOKEN@github.com/$USER/$REPO.git"

# 3. Framkvæma afritun
cd /workspace
git add mimir_simple.py watchdog.sh conversations.json
git commit -m "Auto-backup: $(date '+%Y-%m-%d %H:%M')" 2>/dev/null

# 4. Senda í hvelfinguna
git push -u origin main && echo "✅ GitHub backup tókst!" || echo "❌ Afritun mistókst - athugaðu ghp lykilinn."