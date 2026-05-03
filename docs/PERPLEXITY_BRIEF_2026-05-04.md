# Perplexity Brief — Alvitur.is staða 4. maí 2026

## Kóðatré (interfaces/ core/ services/)
interfaces/middleware/ (auth, errors, security)
interfaces/routes/ (chat, analyze, auth, health, hvelfing, tools, checkout, pages)
interfaces/pipeline/ (leid_a, leid_b)
interfaces/skills/ (classify, extract, summarize, translate)
interfaces/tools/ (search_law, classify_doc, summarize_doc, translate_text)
interfaces/departments/ (legal, finance, research, writing, general)
interfaces/utils/ (quota, rate_limit, openrouter, tabular_*)
interfaces/models/ (schemas, user)
core/rag_orchestrator.py, embeddings.py, db_manager.py
core/ingestion/ (chunker, vector_store)
services/oidc_service.py, user_service.py
services/payment_config.py, payment_checkout.py, payment_webhooks.py

## Gagnagrunnar
- mimir_memory.db: audit_log, audit_log_v2, users
- mimir_core.db: users, conversation_log, user_profiles

## Lykilskjöl
- YFIRLIT.md — stöðutafla, arkitektúrmynstur, öryggisnet
- REGLUR_ALLAR.md — 13 verklagsreglur + 10 Per strangar reglur
- LAERDOMAR_ALLIR.md — 62 lærdómar (30 skráðir, 32 eyður)
- DISKASKÝRSLA.md — diskastaða, vaxtarspá, backup-staða

## Sprint timeline (S74-S79)
- S74: OIDC + PKCE + AuthMiddleware + K3 23.621 chunks
- S75: SessionMiddleware fix, PKCE, redirect
- S76: Hvelfingin /health, anon demo, öryggisnet
- S76c: payment_handler split, mappahreinsun
- S77: vLLM 0.19.0 CUDA fix, Qwen3-32B lifandi
- S78: RAG end-to-end (empirical: lagatilvitnanir)
- S79: Audit log virkjaður (empirical: CHAT_QUERY færsla)

## Nýjustu lærdómar (#56-66)
56: itsdangerous dependency
57: AUDKENNI_BASE_URL = fullur issuer
58: RedirectResponse þarf ["url"]
59: PKCE S256 í oauth.register()
60: Aldrei segja verk "lokið" án empirical verification (meta-regla)
61: Qdrant query_points notar query=vec
62: RAG-samhengi verður að berast alla leið í LLM
63: Sjálfvirk skipting hentar aðeins vel afmörkuðum skrám
64: Halda öllum slóðum undir einni rót
65: sed innfelling hentar illa fyrir Python
66: Audit log: virkja á einum stað fyrst, empirical prófa, síðan útvíkka

## DB Schema — audit_log_v2
CREATE TABLE audit_log_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    user_id INTEGER,
    action TEXT NOT NULL,
    tier TEXT DEFAULT 'general',
    query_hash TEXT,
    response_hash TEXT,
    tokens_used INTEGER DEFAULT 0,
    model TEXT DEFAULT 'unknown',
    pipeline_source TEXT,
    rag_chunks_count INTEGER DEFAULT 0,
    client_ip_hash TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_code TEXT,
    metadata TEXT DEFAULT '{}'
);

## Diskurstaða
- Container: 15 GB / 100 GB (15%)
- Volume: 21 GB / 50 GB (42%)
- Qdrant alvitur_laws_v2: 259,8 MB (23.621 chunks, ~11 KB/chunk)
- Vaxtarspá: 50 GB kvóti næst ~2027
