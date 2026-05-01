"""Sprint 68 C.0 — HTML pattern discovery with Opus 4.7 edge cases."""
import re
from pathlib import Path
from collections import Counter

SAMPLES = sorted(Path("data/bronze/logs/samples").glob("*.html"))

TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>")
CLASS_RE = re.compile(r'class="([^"]+)"')
ANCHOR_ID_RE = re.compile(r'<a\s+(?:name|id)="([^"]+)"')
HREF_RE = re.compile(r'<a\s+href="([^"]+)"')

# Standard markers
GREIN = re.compile(r"(\d+)\.\s*gr\.")
KAFLI = re.compile(r"(I{1,3}V?|IV|V?I{0,3}|IX|X{1,3})\.\s*kafl[ia]")
MGR = re.compile(r"(\d+)\.\s*mgr\.")

# Opus edge cases
AMENDED_ARTICLE = re.compile(r"(\d+)\.\s*gr\.\s*([a-zþæðö])\b")
NESTED_STAFL_TOLUL = re.compile(r"[a-zþæðö]-lið\s+\d+\.\s*(?:tl|tölul)\.")
TL_SHORT = re.compile(r"\b\d+\.\s*tl\.")
TL_FULL = re.compile(r"\b\d+\.\s*tölul\.")
LAW_SHORT = re.compile(r"\bl\.\s*\d+/\d{4}")
LAW_FULL = re.compile(r"\blaga\s+nr\.\s*\d+/\d{4}")
CHAPTER_REF = re.compile(r"(I{1,3}V?|IV|V?I{0,3}|IX|X{1,3})\.\s*kafl[ia]")

EDITORIAL = ["Lagasafn", "útgáfa", "Prenta í", "tveimur dálkum"]

print("="*70)
print("  SPRINT 68 C.0 — HTML PATTERN DISCOVERY")
print("="*70)

for f in SAMPLES:
    html = f.read_text(encoding="utf-8", errors="ignore")
    plain = re.sub(r"<[^>]+>", " ", html)
    print(f"\n### {f.name} ({len(html)//1024} KB)")

    # Standard structure
    tags = Counter(m.group(2).lower() for m in TAG_RE.finditer(html) if not m.group(1))
    classes = Counter(CLASS_RE.findall(html))
    anchors = ANCHOR_ID_RE.findall(html)

    print(f"  Top 8 tags: {tags.most_common(8)}")
    print(f"  Top 8 classes: {classes.most_common(8)}")
    print(f"  Anchor IDs: {len(anchors)} (first 5: {anchors[:5]})")
    print(f"  Grein markers: {len(GREIN.findall(plain))}")
    print(f"  Kafli markers: {len(KAFLI.findall(plain))}")
    print(f"  Málsgrein markers: {len(MGR.findall(plain))}")

    # Opus edge cases
    print(f"  --- Opus 4.7 edge cases ---")
    amended = AMENDED_ARTICLE.findall(plain)
    print(f"  Amended articles (X. gr. a): {len(amended)}")
    if amended[:5]:
        print(f"    examples: {[f'{a[0]}. gr. {a[1]}' for a in amended[:5]]}")

    nested = NESTED_STAFL_TOLUL.findall(plain)
    print(f"  Nested stafl+tolul (a-lið X. tl.): {len(nested)}")

    tl_s = len(TL_SHORT.findall(plain))
    tl_f = len(TL_FULL.findall(plain))
    print(f"  'tl.' short: {tl_s}  vs  'tölul.' full: {tl_f}")

    law_s = len(LAW_SHORT.findall(plain))
    law_f = len(LAW_FULL.findall(plain))
    print(f"  'l.' short: {law_s}  vs  'laga nr.' full: {law_f}")

    chap = CHAPTER_REF.findall(plain)
    print(f"  Chapter references: {len(chap)}")

    # Editorial
    ed_hits = {m: html.count(m) for m in EDITORIAL if html.count(m) > 0}
    print(f"  Editorial markers: {ed_hits}")

    # Tables
    print(f"  Tables: {html.count('<table')}")

print("\n" + "="*70)
print("  C.0 COMPLETE")
print("="*70)
