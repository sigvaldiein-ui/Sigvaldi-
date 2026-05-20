# ALVITUR — REGLUR & LÆRDÓMSSAFN (19. maí 2026)
## § 1 — BINDANDI VINNUREGLUR
- Auðkenni efst: „Opus 4.7“ eða „Per #12“
- Endpoint: alltaf /api/chat, ALDREI /chat
- Framendi: Vanilla HTML/CSS/JS (Engin React, engin Tailwind)
- Aðgengi: Vægi á 30% skjástækkun fyrir CTO.
- Skel: Allar bash-blokkir enda á ROOT bergmáli.

## § 2 — TEYMI & HLUTVERK
- Sigvaldi Einarsson: CTO + HITL
- Opus 4.7: Yfirverkefnastjóri + Gate Reviewer
- Aðal (Gemini 3.1 Pro): Yfirarkitekt
- Per #12 (DeepSeek): Aðal-executor

## § 3 — LÆRDÓMSSAFN (#60 - #110)
- #60: No bluff. Empirical proof.
- #88: Read-before-write (Alltaf cat á undan).
- #102: Tablet Clipboard Paradigm (cat << 'EOF' heredoc).
- #110: *.db og *.sqlite stranglega bannað í git history.

### Lesson #112: Anti-Suggestive Delusion Architecture (Sprint 90)
- **Vandamál:** Líkanið les eigin innri vangaveltur (<think> tokens) í samhengissögunni og notar þær ómeðvitað sem harðar sannanir (Evidence), sem býður upp á keðjuverkun ofskynjana í flóknum keyrslum.
- **Lausn:** Strippa <think> tokens server-side í agent (VitansErindreki) áður en Guard-kerfi eða minni fá skjalið.
- **Gagna-samningur (Data Contract):** Skipta audit-loggun strangt í þrjá dálka á gáttarstigi (chat_routes.py):
  1. `actions_logged`: Innri rökfærslukeðja og hugsanir (sótt úr metadata).
  2. `observations_logged`: Það sem líkanið SÁ (RAG snippets, citations, hráleit).
  3. `final_response`: Synthesis-textinn sem fer til notanda.

### Lesson #117: vLLM Startup Timing & Authentication (20. maí 2026)
- **vLLM ræsing:** ~90 sek að hlaða safetensors, ~30 sek í CUDA graph. Heildartími ~2 mín.
- **API lykill:** vLLM með `--api-key` krefst `Authorization: Bearer <key>` headers. `401 Unauthorized` ≠ niðri.
- **Athugun:** `curl -s http://localhost:8002/v1/models -H "Authorization: Bearer token-abc123"`

### Lesson #118: Galaxy Tab S8 + SSH Clipboard Limitations
- **Vandamál:** Langir Python strengir með `\n` og gæsalöppum brotna í flutningi yfir SSH klippiborð.
- **Lausn A:** Nota `nano` fyrir flóknar skráarbreytingar.
- **Lausn B:** Nota `python3 -c "..."` með einföldum strengjum, forðast `cat << 'EOF'` með innri gæsalöppum.

### Lesson #119: curl POST vs GET fyrir SSE
- **Vandamál:** `curl -N` (no-buffer) með POST getur valdið `ClientDisconnect` áður en server svarar.
- **Lausn:** Nota `--max-time` án `-N`, eða prófa með GET fyrst til að staðfesta grunnvirkni.

### Lesson #120: DEV Port Isolation (8003)
- **Regla:** Öll hættuleg próf keyra á porti 8003. PROD (8000) er aldrei snert nema með formlegu samþykki.
- **Ræsing DEV:** `uvicorn interfaces.web_server:app --port 8003`

### Lesson #121: FastAPI StreamingResponse + request.json() — Generator Scope (20. maí 2026)
- **Vandamál:** `request.json()` má EKKI vera inni í `async def sse_generator()` þegar `StreamingResponse` er notað. FastAPI tæmir request body áður en generator byrjar.
- **Einkenni:** `starlette.requests.ClientDisconnect` í hvert skipti.
- **Lausn:** Lesa `body = await request.json()` og `query = body.get("query")` FYRIR ofan generator, ekki inni í honum.

### Lesson #122: vLLM model nafn verður að vera nákvæm slóð
- **Vandamál:** `"model": "qwen-32b-awq"` virkar ekki. vLLM þarf fulla slóð.
- **Lausn:** `"model": "/workspace/models/qwen3-32b-awq"`

### Lesson #123: POST Smoke Test fyrir SSE með Tier-síu
- **Aðferð:** `timeout 60 curl -s -X POST :8003/api/chat/stream -H "X-Alvitur-Tier: Hvelfingin" -d '{"query":"Hae"}'`
- **Hvelfingin** (án vLLM): skilar `{"error": "Fullvalda innviðir ótilbúnir..."}` —  NEITAR ytri fallback
- **Vitinn** (án vLLM): skilar `{"info": "vLLM down, engaging OpenRouter fallback chain..."}` — reynir ytri fallback

### Lesson #124: fuser -k er óáreiðanlegt á RunPod
- **Vandamál:** `fuser -k 8003/tcp` drepur ekki alltaf ferli.
- **Lausn:** `kill -9 $(ss -tlnp | grep 8003 | grep -oP 'pid=\K\d+')` — beint PID kill.
