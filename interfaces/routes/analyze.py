from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import os, time, logging, hashlib, io
from datetime import datetime, timezone, timedelta
import concurrent.futures as _cf
import httpx

from interfaces.config_runtime import _VAULT_SEMAPHORE_WS, _MODEL_LEIDA_A, _MODEL_LEIDA_B
from interfaces.models.schemas import ChatBeidni, ChatSvar, HeilsusvarModel
from interfaces.utils.helpers import _polish_fn_txt, _detect_filetype, _parse_docx, _parse_xlsx
from interfaces.utils.quota import FREE_QUOTA, _quota_tracker_doc, _beta_tracker, _er_beta_fras, _er_beta_ip, _promota_beta
from interfaces.utils.openrouter import _get_openrouter_balance, _wallet_preflight, _log_intent, SECURE_DOCS_DIR, MAX_PDF_SIZE
from interfaces.pipeline import _call_leid_a, _call_leid_b, _vault_system_prompt

logger = logging.getLogger("alvitur.web")

router = APIRouter()

@router.post("/api/analyze-document")
async def analyze_document(request: Request, file: Optional[UploadFile] = File(None), query: Optional[str] = Form(None)):
    """
    Sprint 21 — PDF Analyze Endpoint (Lag 1).
    Tekur við PDF skrá, les texta með PyMuPDF og búr til grófótta greiningu.
    Zero-Data: Skrá er eyð um leið og vinnslu ljúkur.
    Sprint 43b: query parameter wired from multipart form data.
    Sprint 43c: file optional — text-only queries fall back to direct LLM call.
    """

    # ── Sprint 43c: text-only fallback ──────────────────────────────
    _tier_hdr = request.headers.get("X-Alvitur-Tier", "general").lower().strip() if request else "general"
    _llm_model = _MODEL_LEIDA_B if _tier_hdr == "vault" else _MODEL_LEIDA_A
    if file is None or file.filename == "":
        if not query or not query.strip():
            return JSONResponse(status_code=422, content={
                "error_code": "empty_prompt",
                "detail": "Vinsamlegast skrifaðu fyrirspurn eða hladdu upp skjali.",
            })
        # Sprint 46 Phase 1b: quota check á text-only path (var vantar)
        import hashlib as _hl
        _master_key_txt = os.environ.get("ALVITUR_MASTER_KEY_HASH", "")
        _req_key_txt = request.headers.get("X-Master-Key", "") if request else ""
        _is_admin_txt = bool(_master_key_txt and _req_key_txt and _hl.sha256(_req_key_txt.encode()).hexdigest() == _master_key_txt)
        _client_ip_txt = (
            request.headers.get("CF-Connecting-IP")
            or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )
        # ── Sprint 64 A1: Beta check á text-only path (var vantar) ──
        # Speglarar logic í /api/chat (line ~3593) og analyze-document file-path (line ~3294)
        if _er_beta_fras(query or ""):
            _promota_beta(_client_ip_txt)
            logger.info(f"[BETA] {_client_ip_txt} promotaður í beta-tier (7d) via text-only")
        _is_beta_txt = _er_beta_ip(_client_ip_txt)
        # ── /Sprint 64 A1 beta check ──
        _log_intent("analyze-document/text-only", query, None, None, _tier_hdr)
        _quota_count_txt = _quota_tracker_doc.get(_client_ip_txt, 0) + 1
        if not _is_admin_txt and not _is_beta_txt:
            _quota_tracker_doc[_client_ip_txt] = _quota_count_txt
        if _quota_count_txt > FREE_QUOTA and not _is_admin_txt and not _is_beta_txt:
            return JSONResponse(status_code=403, content={
                "success": False,
                "error": "Ókeypis prufutími er liðinn.",
                "error_code": "quota_exceeded",
                "upgrade_required": True,
                "upgrade_url": "/askrift",
                "message": "Þú hefur nýtt þér 5 ókeypis beiðnir. Uppfærðu til að halda áfram.",
            })

        # Text-only path: send query directly to LLM (async — Sprint 46 Phase 1b)
        import os as _os
        import httpx as _httpx
        from datetime import datetime as _dt, timezone as _tz
        _key = _os.environ.get("OPENROUTER_API_KEY", "")
        _tier = _tier_hdr
        _summary = None
        _rag_txt = None  # tryggjum að nafnið sé til í lok return-blokks
        # 🟢 Sprint 62 Patch E v2: no-key → sovereign Leið B strax (skip OpenRouter entirely)
        if not _key and _tier_hdr != "vault":
            logger.warning("[ALVITUR] Sprint62E NO-KEY → sovereign fallback á Leið B")
            try:
                async with _VAULT_SEMAPHORE_WS:
                    _summary, _model_used, _usage = await _call_leid_b((query or "").strip())
            except Exception as _fe:
                logger.error(f"[ALVITUR] Sprint62E exc: {type(_fe).__name__}: {_fe}")
                _summary = None
            if _summary is None:
                return JSONResponse(status_code=503, content={
                    "error_code": "sovereign_unavailable",
                    "detail": "Staðbundin gervigreind er að ræsast. Reyndu eftir andartak."})
            logger.info(f"[ALVITUR] Sprint62E sovereign OK model={_model_used}")
            return JSONResponse(status_code=200, content={
                "success": True, "summary": _summary, "mode": "text-only",
                "pipeline_source": f"sovereign_nokey_{_model_used}", "model": _model_used})
        if _key:
            try:
                _now_str = _dt.now(_tz.utc).strftime("%Y-%m-%d %H:%M UTC")
                # Sprint 47: Domain classification + specialist prompt
                # Sprint 60c: None guard + honesty instruction
                from interfaces.specialist_prompts import get_specialist_prompt as _get_prompt
                from interfaces.skills.classify import ClassifySkill as _ClsSkill
                try:
                    _domain_txt = await _ClsSkill().run((query or "").strip() or "general", tier=_tier_hdr)
                except Exception:
                    _domain_txt = "general"
                _domain_txt = _domain_txt or "general"
                # s68-hotfix Part 3: text-only + tone-guide + thinking-suppress
                _honesty = (
                    "\n\nMikilvægt: Notandi hefur ekki hengt við skjal — þetta er almenn "
                    "spurning. Svaraðu út frá almennri þekkingu þinni á íslensku. "
                    "Ef þú veist ekki svarið með vissu, segðu það heiðarlega og bjóddu "
                    "framhaldsspurningu. Ekki búa til staðreyndir. "
                    "MIKILVÆGT UM FRAMSETNINGU: Ekki sýna hugsanaferli þitt — engar "
                    "<thinking>-tög, engin ‚bíð, ég þarf að“ setningar, engin internal-monologue. "
                    "Sendu aðeins hreint, prófessjónal svar beint. Engar emoji, "
                    "engin upphrópunarmerki, formlegt B2B-mál."
                )
                _system_prompt = _get_prompt(_domain_txt, _now_str) + _honesty
                # Sprint 70 Track D — RAG+ hook (text-only path)
                try:
                    from core.rag_orchestrator import retrieve_legal_context, build_rag_injection
                    _rag_txt = retrieve_legal_context(
                        query=(query or "").strip(),
                        intent_domain=_domain_txt,
                        tier=_tier,
                        tenant_id="system",
                    )
                    if _rag_txt.refusal:
                        from fastapi.responses import JSONResponse as _JR
                        return _JR(content={"success":True,"response":_rag_txt.refusal,
                            "pipeline_source":"rag_refusal_vault","domain":_domain_txt,
                            "zero_data":True,"found":True,"status":"ready_for_analysis",
                            "citations":[],"quota_warning":None,"tier":_tier})
                    if _rag_txt.used_retrieval:
                        _system_prompt = _system_prompt + build_rag_injection(_rag_txt.chunks)
                        _pipeline_source_txt = "rag_grounded_" + _tier
                    elif _rag_txt.fallback_to_gemini:
                        _system_prompt = _system_prompt + "[ATH: Engin lagatilvitnun fannst. Svaraðu varlega.]"
                        _pipeline_source_txt = "rag_fallback_general"
                except Exception as _rag_e2:
                    logger.warning("[RAG] text-only villa: %s", _rag_e2)
                logger.info(f"[ALVITUR] Sprint61 text-only tier={_tier} domain={_domain_txt}")
                _pipeline_source_txt = "unknown"
                if _tier == "vault":
                    from interfaces.config import VAULT_MAX_INPUT_TOKENS as _vmax
                    from interfaces.utils.helpers import _estimate_tokens
                    if _estimate_tokens(query or "") > _vmax:
                        return JSONResponse(status_code=413, content={
                            "error_code": "vault_input_too_large",
                            "detail": "Fyrirspurn er of stór fyrir Vault tier (max 8000 tokens). Styttu textann."})
                    async with _VAULT_SEMAPHORE_WS:
                        _summary, _model_used, _usage = await _call_leid_b(query.strip())
                    if _summary is None:
                        return JSONResponse(status_code=503, content={
                            "error_code": "vault_local_unavailable",
                            "detail": "Trúnaðarþjónusta tímabundið ekki tiltæk. Local AI module er að ræsast — reyndu aftur eftir 1 mínútu."})
                    _pipeline_source_txt = f"local_vllm_{_model_used}"
                    _in_tok = _usage.get("prompt_tokens", 0); _out_tok = _usage.get("completion_tokens", 0)
                    logger.info(f"[ALVITUR] leid_b sovereign tokens in={_in_tok} out={_out_tok}")
                else:
                    _summary, _model_used, _usage = await _call_leid_a(_system_prompt, query.strip())
                    if _summary is None:
                        logger.warning("[ALVITUR] Sprint62C text-only: Leið A None, reyni fallback á Leið B")
                        try:
                            async with _VAULT_SEMAPHORE_WS:
                                _summary, _model_used, _usage = await _call_leid_b(query.strip())
                        except Exception as _fe:
                            logger.error(f"[ALVITUR] Sprint62C fallback exc: {type(_fe).__name__}: {_fe}")
                            _summary = None
                        if _summary is None:
                            return JSONResponse(status_code=503, content={
                                "error_code": "both_pipelines_unavailable",
                                "detail": "Þjónusta tímabundið ekki aðgengileg. Reyndu eftir augnablik."})
                        _pipeline_source_txt = f"fallback_local_{_model_used}"
                        logger.info(f"[ALVITUR] Sprint62C fallback OK: model={_model_used}")
                    else:
                        _pipeline_source_txt = f"openrouter_{_model_used.split('/')[-1]}"
                    _in_tok = _usage.get("prompt_tokens", 0); _out_tok = _usage.get("completion_tokens", 0)
                    _cost = (_in_tok * 0.15 + _out_tok * 0.60) / 1_000_000 if "gpt-4o-mini" in _model_used else (_in_tok * 3.00 + _out_tok * 15.00) / 1_000_000 if "claude-sonnet" in _model_used else 0.0
                    logger.info("[ALVITUR] token_obs pipeline=text_query model=%s tier=%s in=%d out=%d cost=%.6f", _model_used, _tier, _in_tok, _out_tok, _cost)
                    try:
                        _summary = await _polish_fn_txt(_summary, _key)
                    except Exception as _pe:
                        logger.warning(f"[ALVITUR] polish failed (non-fatal): {_pe}")
            except Exception as _e:
                logger.error(f"[ALVITUR] text-only pipeline exc: {type(_e).__name__}: {_e}")
                _summary = None
                _domain_txt = "general"
                _pipeline_source_txt = "error"
        if _summary is None:
            # Sprint 62 Patch C: Final safety net — both pipelines down
            return JSONResponse(status_code=503, content={
                "error_code": "service_unavailable",
                "detail": "Greiningar þjónusta tímabundið ekki aðgengileg. Reyndu aftur eftir andartak.",
            })
        return JSONResponse(content={
            "success": True,
            "filename": None,
            "sidur": 0,
            "zero_data": True,
            "tier": _tier,
            "query": query.strip(),
            "response": _summary,
            "domain": _domain_txt,
            "citations": [],
            "found": True,
            "status": "ready_for_analysis",
            "pipeline_source": _pipeline_source_txt if "_pipeline_source_txt" in dir() else "unknown",
            "rag_metadata": _rag_txt.__dict__ if (_rag_txt is not None and hasattr(_rag_txt,"used_retrieval")) else {},
        })

    import fitz  # PyMuPDF
    # ... (restinn óbreyttur frá web_server.py eftir text-only block)
