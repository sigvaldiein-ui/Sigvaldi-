"""Kvótakerfi fyrir óinnskráða notendur — IP + netfang."""
import time

IP_QUOTA = {}        # IP -> {"count": 2, "reset": timestamp}
EMAIL_QUOTA = {}     # email -> {"count": 0, "limit": 20, "mb_used": 0.0, "mb_limit": 5.0, "reset": timestamp}

def check_ip_quota(ip: str) -> dict:
    """Skilar {"allowed": bool, "remaining": int} fyrir IP."""
    now = time.time()
    if ip not in IP_QUOTA or now - IP_QUOTA[ip]["reset"] > 86400:
        IP_QUOTA[ip] = {"count": 2, "reset": now}
    remaining = IP_QUOTA[ip]["count"]
    return {"allowed": remaining > 0, "remaining": remaining}

def use_ip_quota(ip: str) -> int:
    """Notar eina IP fyrirspurn. Skilar eftirstandandi."""
    if ip not in IP_QUOTA:
        check_ip_quota(ip)
    IP_QUOTA[ip]["count"] = max(0, IP_QUOTA[ip]["count"] - 1)
    return IP_QUOTA[ip]["count"]

def check_email_quota(email: str) -> dict:
    """Skilar {"allowed": bool, "remaining": int, "mb_remaining": float} fyrir netfang."""
    now = time.time()
    if email not in EMAIL_QUOTA or now - EMAIL_QUOTA[email]["reset"] > 86400:
        EMAIL_QUOTA[email] = {"count": 0, "limit": 20, "mb_used": 0.0, "mb_limit": 5.0, "reset": now}
    q = EMAIL_QUOTA[email]
    return {"allowed": q["count"] < q["limit"], "remaining": q["limit"] - q["count"], "mb_remaining": q["mb_limit"] - q["mb_used"]}

def use_email_quota(email: str, mb: float = 0.0) -> dict:
    """Notar eina netfangs-fyrirspurn. Skilar nýja stöðu."""
    if email not in EMAIL_QUOTA:
        check_email_quota(email)
    q = EMAIL_QUOTA[email]
    q["count"] += 1
    q["mb_used"] += mb
    return {"remaining": q["limit"] - q["count"], "mb_remaining": q["mb_limit"] - q["mb_used"]}


# ── P5: Kill-switch fyrir OpenRouter ─────────────────────────────
_DAILY_BUDGET = 5000  # ISK
_DAILY_SPENT = 0.0
_LAST_RESET = None

def openrouter_budget_ok(estimated_cost_usd: float = 0.05) -> bool:
    """Skilar True ef við erum innan dagsþaks. Breytir USD í ISK með föstu gengi."""
    global _DAILY_SPENT, _LAST_RESET
    import time
    now = time.time()
    # Endurstilla á miðnætti
    if _LAST_RESET is None or now - _LAST_RESET > 86400:
        _DAILY_SPENT = 0.0
        _LAST_RESET = now
    cost_isk = estimated_cost_usd * 140  # Fast gengi
    if _DAILY_SPENT + cost_isk > _DAILY_BUDGET:
        return False
    _DAILY_SPENT += cost_isk
    return True
