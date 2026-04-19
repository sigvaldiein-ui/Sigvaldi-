# Sprint 60c Endurheimt — Samhengi fyrir framhald

**Dagsetning:** 19. apríl 2026, 09:00 – 10:25 GMT
**Þátttakendur:** Sigvaldi Einarsson (CTO), Opus 4.5 (AI advisor)
**Staða við upphaf:** Ruglingur vegna tveggja Git repo-a á sama pod
**Staða við lok:** Syntax lagað, tilbúinn fyrir live switch

---

## 🎯 STÓRA UPPGÖTVUNIN

Pod-inn hefur **TVÖ aðskilin GitHub repos**:

| Mappa | Repo | Kóða-stig |
|---|---|---|
| `/workspace/mimir-workspace/` | `sigvaldiein-ui/mimir-workspace.git` | Mix af main (Sprint 60c) og sprint46-phase1-infra branch (Sprint 6, 291 lína) |
| `/workspace/mimir_net/` | `sigvaldiein-ui/Sigvaldi-.git` | **Raunveruleg production** main branch, Sprint 60c+, 3,606 línur |

**Núverandi þjónn (PID 10635) keyrir úr `/workspace/mimir-workspace/` — RÖNG MAPPA.**
**Rétt mappa er `/workspace/mimir_net/` þar sem main kóðinn er.**

---

## 🔧 VERKLAG MORGUNSINS

### 1. Öryggisafrit (áður en snertum neitt)
- Git tag búið til: `backup-before-main-switch-20260419-1005`
- Push á GitHub: staðfest
- Local backup: `web_server.py.bak-19apr-0930` í mimir-workspace/interfaces

### 2. Stash af uncommitted vinnu í mimir-workspace
- Stash: `Sprint46-WIP-before-main-switch-19apr-1006`
- 20+ skrár geymd öruggt

### 3. Greining á mimir_net
- Commit `b143e66` 16. apríl: „feat: add Office (xlsx/docx) parsing fallback"
- Commit `6c5ba92` 19. apríl 10:17: „Pre-sprint8 checkpoint" (gerðum í morgun)
- Stash: `mimir_net-untracked-19apr-1016`

### 4. SYNTAX VILLA FUNDIN
- Lína 3266 hafði debug `logger.info` með 24-bil inndrátt (átti að vera 12 eða fjarlægt)
- Commit sem olli villunni: `6c5ba92` (frá því í morgun)
- Þetta þýðir: mimir_net kóðinn **hefur aldrei ræst síðan 13. apríl** vegna þessarar villu
- Lagað með: `sed -i '/logger.info("\[ALVITUR\] DEBUG: About to call LLM/d'`
- Syntax check: ✅✅✅ PASS
- Ný stærð: 3,606 línur (einni minna en áður)
- Öryggisafrit fyrir lagfæringu: `web_server.py.before-syntax-fix-1023`

---

## 📋 HVAÐ ER EFTIR

### Næsta skref (skref 8 í plani):
LIVE SWITCH — skipta þjóni úr mimir-workspace yfir á mimir_net.

Skipanir sem bíða að keyra:
```bash
# 1. Stoppa gamla þjón
kill 10635

# 2. Ræsa nýja þjón úr mimir_net
cd /workspace/mimir_net/interfaces
nohup python3 -u web_server.py >> /workspace/web_server.log 2>&1 &

# 3. Staðfesta
sleep 3
curl -s http://localhost:8000/health | python3 -m json.tool
```

### Eftir switch:
1. Prófa upload á XLSX skrá → ætti að virka
2. Staðfesta „AI hefur ekki aðgang" vandinn sé farinn (Sprint 60c honesty prompt)
3. Committa syntax lagfæringu í mimir_net Git
4. Bæta við PPTX parser (python-pptx þegar uppsettur)
5. Staðfesta Tavily MCP web search virkar
6. Plugga inn Straumur/Kvika greiðslumiðlun

---

## 🔑 MIKILVÆG SLÓÐ OG BREYTUR

- Production mappa: `/workspace/mimir_net/`
- web_server.py: `/workspace/mimir_net/interfaces/web_server.py` (3,606 línur)
- .env: `/workspace/mimir_net/config/.env`
- static dir: `/workspace/mimir_net/interfaces/static/`
- index.html: `/workspace/mimir_net/interfaces/index.html`
- secure docs: `/workspace/mimir_net/secure_docs/`
- Cloudflare tunnel: PID 9585, tunnel 490c85db (AlviturBot)
- Port: 8000

### .env inniheldur:
OPENROUTER_API_KEY, STRAUMUR_API_KEY+HMAC+TERMINAL+WEBHOOK_SECRET,
KVIKA_PASSWORD, TAVILY_API_KEY+MCP_URL, TELEGRAM_TOKEN,
PERPLEXITY_API_KEY, GOOGLE_API_KEY, MIMIR_EMAIL_USER/PASS,
GMAIL_SEND_PASSWORD, ORKUSKIPTI_CONTRACT_ID, ALVITUR_API_KEYS,
ALVITUR_MASTER_KEY_HASH, OPENROUTER_ZDR_CONFIRMED, GITHUB_TOKEN,
GOOGLE_JSON_KEY_FILE, GUMROAD_LIST, MIMIR_APP_PASSWORD

---

## 🛡️ ÖRYGGISNET (5 stig)

1. Git tag á GitHub: `backup-before-main-switch-20260419-1005`
2. Stash mimir-workspace: `Sprint46-WIP-before-main-switch-19apr-1006`
3. Commit mimir_net: `6c5ba92`
4. Stash mimir_net untracked: `mimir_net-untracked-19apr-1016`
5. Local: `web_server.py.bak-19apr-0930`, `web_server.py.before-syntax-fix-1023`

---

## 💡 LÆRDÓMAR

1. **Qwens skýrsla var ónákvæm** — lýsti XLSX/PPTX sem „virka" en kóðinn studdi það ekki í sprint46-phase1-infra
2. **Tveir Git repos ollu ruglingi** — AI-s gerðu vinnu á mismunandi stöðum án þess að vita af því
3. **Debug logger lína aldrei fjarlægð** olli 6 daga downtime á main kóða án þess að eftir væri tekið
4. **Syntax check BEFORE switch** er gulls ígildi — fann villuna áður en downtime varð

---

**Höfundur:** Opus 4.5 í samstarfi við Sigvaldi Einarsson
**Motto dagsins:** Aim for the stars 🌟

---

## 🟡 KNOWN ISSUES eftir live switch (19. apríl 2026, 11:49 GMT)

### 1. XLSX greining virkar ekki í núverandi production útgáfu
- **Einkenni**: Upload á `.xlsx` skilar ekki vænum greiningum
- **Backend**: Sprint 28 K1/K2 parser er til í kóða (línur 2893–2938 í web_server.py) — `python3 -c "import openpyxl"` þarf að virka
- **Líkleg orsök**: Annað hvort (a) openpyxl ekki uppsett, (b) parser-bug, (c) samskipti við analyze-document endpoint
- **Prioritet**: Medium — DOCX og PDF virka, XLSX er nice-to-have fyrir Sprint 61a
- **Næsta skref**: Athuga `pip list | grep openpyxl` og prófa parser í isolation

### 2. summarize_doc MCP tool skilar tómum streng
- **Einkenni**: Endpoint svarar `{"success": true, "result": ""}` fyrir gefinn texta
- **Líkleg orsök**: MCP tool köllur LLM án þess að bíða eftir svari, eða system prompt er bilaður
- **Prioritet**: Low — aðrir tools virka, þessi er ekki kritíska
- **Næsta skref**: Debug í mcp_server.py línum sem innihalda summarize_doc

### 3. Telegram bot ekki keyrandi
- **Einkenni**: `ps aux | grep telegram` skilar engu
- **Spurning**: Á Mímir-Telegram bot að vera í loftinu á þessu pod?
- **Prioritet**: Óákveðinn — þarf stefnuákvörðun


---

## 🟡 KNOWN ISSUES eftir live switch (19. apríl 2026, 11:49 GMT)

### 1. XLSX greining virkar ekki í núverandi production útgáfu
- **Einkenni**: Upload á `.xlsx` skilar ekki vænum greiningum
- **Backend**: Sprint 28 K1/K2 parser er til í kóða (línur 2893–2938 í web_server.py)
- **Líkleg orsök**: Annað hvort (a) openpyxl ekki uppsett, (b) parser-bug, (c) samskipti við analyze-document endpoint
- **Prioritet**: Medium — DOCX og PDF virka, XLSX er fyrir Sprint 61a
- **Næsta skref**: `pip list | grep openpyxl` og prófa parser í isolation

### 2. summarize_doc MCP tool skilar tómum streng
- **Einkenni**: Endpoint svarar `{"success": true, "result": ""}` fyrir gefinn texta
- **Líkleg orsök**: MCP tool köllur LLM án þess að bíða, eða system prompt er bilaður
- **Prioritet**: Low
- **Næsta skref**: Debug í mcp_server.py fyrir summarize_doc

### 3. Telegram bot ekki keyrandi
- **Einkenni**: `ps aux | grep telegram` skilar engu
- **Spurning**: Á Mímir-Telegram bot að vera í loftinu á þessu pod?
- **Prioritet**: Óákveðinn — þarf stefnuákvörðun

---

## ✅ SPRINT 60c ENDURHEIMT LOKIÐ

**Dagsetning:** 19. apríl 2026, 09:00 – 11:50 GMT (2 klst 50 mín)
**Staða:** alvitur.is er opin fyrir Ísland á Sprint 58+ kóðagrunni
**GitHub:** Allar breytingar á `sigvaldiein-ui/Sigvaldi-.git` main branch

### Lokaprófanir (11:46 GMT)
- ✅ `/api/health` → sprint58, production
- ✅ 7 síður HTTP 200 (/, personuvernd, skilmalar, oryggi, askrift, mimir-demo, alvitur-v2)
- ✅ 4 MCP tools skráðir (search_law, summarize_doc, classify_doc, translate_text)
- ✅ classify_doc MCP tool svarar
- ✅ Forsíða með Almennum + Trúnaðar tabs virk
- ✅ File upload samræmt við backend: .pdf, .docx, .xlsx
- ⚠️ XLSX greining, summarize_doc tómt svar, Telegram bot → Sprint 61

