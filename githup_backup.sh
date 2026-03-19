#!/bin/bash

# --- 🔑 ÞINN HLUTI ---
TOKEN="ghp_U1Mbqiww2A3S9qEv0LNgiaAgefUHy03CXkNv"

# --- ⚙️ STILLINGAR ---
USER="sigvaldiein-ui"
REPO="mimir-workspace"
EMAIL="sigvaldiein@gmail.com"

git config --global user.email "$EMAIL"
git config --global user.name "Sigvaldi"

# Uppfæra fjar-tengingu (Remote)
git remote add origin "https://$TOKEN@github.com/$USER/$REPO.git" 2>/dev/null
git remote set-url origin "https://$TOKEN@github.com/$USER/$REPO.git"

# --- 🚀 FRAMKVÆMD (SNJALLARI ÚTGÁFA) ---
cd /workspace

# Við segjum Git að bæta við ÖLLUM forritum og handritum sem eru til
git add *.py *.sh *.md *.jsonl 2>/dev/null

# Búa til pakkann (Commit)
git commit -m "Strategic Backup: $(date '+%Y-%m-%d %H:%M')"

# Senda á GitHub
git branch -M main
git push -u origin main && echo "✅ GitHub backup tókst!" || echo "❌ Afritun mistókst ennþá."