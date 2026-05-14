"""
Sprint 80c — Citation Schema
Converts raw search results into internal JSON and Markdown citation format.
"""
import hashlib
from typing import Dict, List, Optional
from typing import Dict, List, Optional, Literal

SOURCE_TIER_MAP = {
    "stjornarradid": "government",
    "stjornartidindi": "government",
    "mojeek": "general",
    "wayback": "general",
}


def canonicalize_url(url: str) -> str:
    """Normalize URL: lowercase, remove www., trailing slash."""
    if not url:
        return ""
    u = url.strip().lower()
    if u.startswith("https://www."):
        u = "https://" + u[12:]
    elif u.startswith("http://www."):
        u = "http://" + u[11:]
    return u.rstrip("/")


def simhash_64(text: str) -> str:
    """Compute 64-bit SimHash hex fingerprint for dedup."""
    if not text:
        return "0" * 16
    v = [0] * 64
        # Simple token-weighted hash
    tokens = text.split()
    if not tokens:
        return "0" * 16
    for t in tokens:
        h = int(hashlib.md5(t.encode()).hexdigest()[:16], 16)
        for i in range(64):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1
    result = 0
    for i in range(64):
        if v[i] > 0:
            result |= (1 << i)
    return format(result, '016x')


def build_citation(raw_result: Dict, source: str = "mojeek", rank: int = 1,
                   tier: Optional[str] = None, score: float = 0.0) -> Dict:
    """Build internal citation dict from a raw search result."""
    url = raw_result.get("url", "")
    title = raw_result.get("title", "")
    snippet = raw_result.get("desc", raw_result.get("snippet", ""))
    
    if tier is None:
        tier = SOURCE_TIER_MAP.get(source, "general")
    
    return {
        "url": canonicalize_url(url),
        "title": title,
        "snippet": snippet,
        "source": source,
        "tier": tier,
        "score": score,
        "accessed_at": None,  # Filled by caller
        "rank": rank,
        "simhash": simhash_64(f"{title} {snippet}"),
    }


def render_markdown(citations: List[Dict]) -> str:
    """Render list of citations as Markdown numbered list."""
    if not citations:
        return ""
    lines = []
    for i, c in enumerate(citations, 1):
        url = c.get("url", "")
        title = c.get("title", "") or url
        snippet = c.get("snippet", "")
        line = f"{i}. [{title}]({url})"
        if snippet:
            line += f" – {snippet}"
        lines.append(line)
    return "\n".join(lines)


def hamming_distance(h1: str, h2: str) -> int:
    """Compute Hamming distance between two SimHash hex strings."""
    if len(h1) != len(h2):
        return 999
    diff = int(h1, 16) ^ int(h2, 16)
    return bin(diff).count("1")


def deduplicate(citations: List[Dict], threshold: int = 3) -> List[Dict]:
    """Remove duplicates using SimHash Hamming distance ≤ threshold."""
    seen: List[Dict] = []
    for c in citations:
        sh = c.get("simhash", "")
        is_dup = False
        for s in seen:
            if hamming_distance(sh, s.get("simhash", "")) <= threshold:
                is_dup = True
                break
        if not is_dup:
            seen.append(c)
    return seen
