"""
Sprint 62 Patch C: Leið A → Leið B sovereign fallback.

When OpenRouter (Leið A) fails, instead of returning 502, fall through
to the local sovereign Qwen3-32B (Leið B) and return that answer to the user.
User sees a seamless response; log tags pipeline_source=fallback_local_*.

Three 502 sites identified:
 - L3134 (text-only, after _call_leid_a None) → fallback to Leið B
 - L3152 (text-only safety net after try/except) → change to 503 (both failed)
 - L3392 (analyze-doc file path, after _call_leid_a None) → fallback to Leið B
"""
import sys
from pathlib import Path

TARGET = Path("interfaces/web_server.py")

# ── Site 1: Line ~3134 — text-only path Leið A failure ──────────────
OLD_1 = '''                else:
                    _summary, _model_used, _usage = await _call_leid_a(_system_prompt, query.strip())
                    if _summary is None:
                        return JSONResponse(status_code=502, content={
                            "error_code": "llm_unavailable",
                            "detail": "Ekki tókst að ná sambandi við greiningar þjónustu. Reyndu aftur."})
                    _pipeline_source_txt = f"openrouter_{_model_used.split('/')[-1]}"'''

NEW_1 = '''                else:
                    _summary, _model_used, _usage = await _call_leid_a(_system_prompt, query.strip())
                    if _summary is None:
                        # Sprint 62 Patch C: Leið A klikkaði → sovereign fallback á Leið B
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
                        _pipeline_source_txt = f"openrouter_{_model_used.split('/')[-1]}"'''

# ── Site 2: Line ~3152 — text-only outer safety net (both failed) ───
OLD_2 = '''        if _summary is None:
            return JSONResponse(status_code=502, content={
                "error_code": "llm_unavailable",
                "detail": "Ekki tókst að ná sambandi við greiningar þjónustu. Reyndu aftur.",
            })'''

NEW_2 = '''        if _summary is None:
            # Sprint 62 Patch C: Final safety net — both pipelines down
            return JSONResponse(status_code=503, content={
                "error_code": "service_unavailable",
                "detail": "Greiningar þjónusta tímabundið ekki aðgengileg. Reyndu aftur eftir andartak.",
            })'''

# ── Site 3: Line ~3392 — analyze-doc file path, Leið A failure ──────
OLD_3 = '''                    _summary, _model_used, _usage = await _call_leid_a(_system_prompt, _msg)
                    if _summary is None:
                        return JSONResponse(status_code=502, content={
                            "error_code": "llm_unavailable",
                            "detail": "Ekki tókst að ná sambandi við greiningar þjónustu. Reyndu aftur."})
                    _pipeline_source_doc = f"openrouter_{_model_used.split('/')[-1]}"'''

NEW_3 = '''                    _summary, _model_used, _usage = await _call_leid_a(_system_prompt, _msg)
                    if _summary is None:
                        # Sprint 62 Patch C: Leið A klikkaði → sovereign fallback á Leið B
                        logger.warning("[ALVITUR] Sprint62C analyze_doc: Leið A None, reyni fallback á Leið B")
                        try:
                            async with _VAULT_SEMAPHORE_WS:
                                _summary, _model_used, _usage = await _call_leid_b(_msg)
                        except Exception as _fe:
                            logger.error(f"[ALVITUR] Sprint62C analyze_doc fallback exc: {type(_fe).__name__}: {_fe}")
                            _summary = None
                        if _summary is None:
                            return JSONResponse(status_code=503, content={
                                "error_code": "both_pipelines_unavailable",
                                "detail": "Þjónusta tímabundið ekki aðgengileg. Reyndu eftir augnablik."})
                        _pipeline_source_doc = f"fallback_local_{_model_used}"
                        logger.info(f"[ALVITUR] Sprint62C analyze_doc fallback OK: model={_model_used}")
                    else:
                        _pipeline_source_doc = f"openrouter_{_model_used.split('/')[-1]}"'''


def main():
    src = TARGET.read_text()
    if "Sprint 62 Patch C" in src:
        print("⚠️  Patch C þegar beitt.")
        return 0

    patches = [("Site 1 (L~3134)", OLD_1, NEW_1),
               ("Site 2 (L~3152)", OLD_2, NEW_2),
               ("Site 3 (L~3392)", OLD_3, NEW_3)]

    for name, old, new in patches:
        if old not in src:
            print(f"❌ {name}: fann ekki gamla strenginn.")
            return 1
        if src.count(old) > 1:
            print(f"❌ {name}: strengur fannst {src.count(old)} sinnum.")
            return 1

    patched = src
    for name, old, new in patches:
        patched = patched.replace(old, new)
        print(f"✅ {name} beittur.")

    import ast
    try:
        ast.parse(patched)
    except SyntaxError as e:
        print(f"❌ Syntax villa: {e}")
        return 1

    TARGET.write_text(patched)
    print("\n✅ Patch C að fullu beittur. Syntax OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
