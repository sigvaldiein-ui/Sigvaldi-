"""Leið B — Local vLLM Qwen 3 32B AWQ sovereign (vault tier).

100% local inference on RunPod A40 (port 8002). No cloud fallback.
Returns: (content, model_used, usage_dict) or (None, None, None).
"""
import logging
logger = logging.getLogger("alvitur.web")


def _vault_system_prompt():
    return ("Þú ert Alvitur — íslensk gervigreindaraðstoð á trúnaðarstigi (Vault). "
            "Þú keyrir á íslenskri GPU. Gögn fara aldrei úr vélinni.\n\n"
            "REGLUR UM ÍSLENSKU:\n"
            "1. Svaraðu ALLTAF á réttri íslensku með fullum beygingum.\n"
            "2. Gættu að föllum (nf/þf/þgf/ef) og kynjum (kk/kvk/hk).\n"
            "3. Notaðu aldrei orð sem þú ert ekki viss um — veldu einfaldara orð.\n"
            "4. Ekki búa til orð. Ef þú veist ekki orðið — umorðaðu.\n\n"
            "DÆMI UM GÓÐA SVÖRUN:\n"
            "Spurning: Hvað er höfuðborg Íslands?\n"
            "Svar: Reykjavík er höfuðborg Íslands. Hún er stærsta borg landsins og þar búa um 130.000 manns.\n\n"
            "Spurning: Greindu þessa færslu: '01.12.2025 | Launagreiðsla | 450000'\n"
            "Svar: Þetta er innborgun launa að fjárhæð 450.000 krónur þann 1. desember 2025. Þetta flokkast sem tekjur.\n\n"
            "Svaraðu nú spurningu notandans í sama stíl.")


async def _call_leid_b(user_msg, max_tokens=8192):
    """Local sovereign vLLM. NO cloud fallback. Returns (content, model, usage) or (None,None,None)."""
    from interfaces.config import VAULT_LOCAL_URL, VAULT_LOCAL_MODEL, VAULT_LOCAL_TIMEOUT
    import httpx as _hx
    try:
        async with _hx.AsyncClient() as c:
            r = await c.post(VAULT_LOCAL_URL,
                headers={"Content-Type": "application/json"},
                json={"model": VAULT_LOCAL_MODEL,
                      "messages": [{"role":"system","content":_vault_system_prompt()},{"role":"user","content":user_msg}],
                      "max_tokens": max_tokens, "temperature": 0.3, "top_p": 0.9,
                      "chat_template_kwargs": {"enable_thinking": False}},
                timeout=float(VAULT_LOCAL_TIMEOUT))
            if r.status_code != 200:
                logger.error(f"[ALVITUR] leid_b local vLLM status={r.status_code} body={r.text[:200]}")
                return (None, None, None)
            d = r.json()
            ms = VAULT_LOCAL_MODEL.rsplit("/", 1)[-1]
            u = d.get("usage", {})
            logger.info(f"[ALVITUR] leid_b sovereign ok model={ms} in={u.get('prompt_tokens',0)} out={u.get('completion_tokens',0)}")
            return (d["choices"][0]["message"]["content"], ms, u)
    except Exception as e:
        logger.error(f"[ALVITUR] leid_b local vLLM exc={type(e).__name__}: {e}")
        return (None, None, None)


