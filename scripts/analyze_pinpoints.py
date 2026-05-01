"""s68-b1: empirical pinpoint discovery on raw lög samples."""
import re
from pathlib import Path
from collections import Counter

SAMPLES = Path("data/bronze/logs/samples").glob("*.html")

# Strip HTML tags crudely for pattern analysis
TAG_RE = re.compile(r"<[^>]+>")

# Pattern families
PATTERNS = {
    "internal_pinpoint": re.compile(
        r"(?:\d+\.\s*t(?:öl)?ul?\.\s*)?"
        r"(?:\d+\.\s*mgr\.\s*)?"
        r"\d+\.\s*gr\."
    ),
    "external_pinpoint": re.compile(
        r"\d+\.\s*gr\.\s*laga\s+nr\.\s*\d+/\d{4}"
    ),
    "stafslidur": re.compile(r"[a-zA-Zþðæöáéíóúý]-lið(?:ar|ir|um|ur|s)?"),
    "tolulidur": re.compile(r"\d+\.\s*(?:tl|tölul)\."),
    "malsgrein": re.compile(r"\d+\.\s*mgr\."),
    "grein_range": re.compile(r"\d+\.\s*[–-]\s*\d+\.\s*gr\."),
    "law_full": re.compile(r"[Ll]ög(?:um|in|unum)?\s+nr\.\s*\d+/\d{4}"),
    "sbr_reference": re.compile(r"sbr\.\s+\d+\.\s*(?:mgr\.|gr\.|tl\.)"),
}

for f in sorted(SAMPLES):
    text = TAG_RE.sub(" ", f.read_text(encoding="utf-8", errors="ignore"))
    print(f"\n=== {f.name} ({len(text)} chars) ===")
    for name, rx in PATTERNS.items():
        matches = rx.findall(text)
        if matches:
            c = Counter(matches)
            print(f"  {name}: {len(matches)} total, top 3: {c.most_common(3)}")
