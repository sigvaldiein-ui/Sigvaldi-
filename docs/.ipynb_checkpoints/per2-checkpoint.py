"""
S68 A.2 patch: depth classifier redesign.

Adds:
  - _KW_DEPTH_STANDARD, _KW_DEPTH_DEEP keyword sets
  - New depth logic with precedence:
      1. Hard size limits  -> deep
      2. DEEP keyword match (with safety gates) -> deep
      3. STANDARD keyword match -> standard
      4. Length fast fallback -> fast
      5. Default -> standard

Opus suggestions integrated:
  - "saga"/"sögu" require co-occurrence with depth cue
  - "virkar" requires "hvernig" co-occurrence (AND gate)
  - Deep-dominance documented in docstring
"""
from __future__ import annotations
import sys
from pathlib import Path

SRC = Path("core/intent_gateway.py")
assert SRC.exists(), f"not found: {SRC}"

src = SRC.read_text(encoding="utf-8")

# ---------- PATCH 1: add _KW_DEPTH_* lists after _KW_PUBLIC block ----------
ANCHOR_AFTER_PUBLIC = '_KW_PUBLIC = {'
if src.count(ANCHOR_AFTER_PUBLIC) != 1:
    sys.exit(f"anchor mismatch: _KW_PUBLIC = {{ count={src.count(ANCHOR_AFTER_PUBLIC)}")

# Find end of _KW_PUBLIC block (closing brace on its own line)
idx_public_start = src.index(ANCHOR_AFTER_PUBLIC)
idx_public_end = src.index('}', idx_public_start) + 1
# Advance to end of that line
idx_insert = src.index('\n', idx_public_end) + 1

NEW_LISTS = '''
# ── Depth-keyword listar (S68 A.2) ──────────────────────────────────────
# Semantic signals fyrir reasoning_depth. Precedence í depth-block neðar.
# Stem-based (Lesson #19 frá S67).
_KW_DEPTH_STANDARD = {
    # explanatory verbs (require 1-2 paragraph answer)
    "útskýr", "skýr",                    # útskýra, útskýrðu, skýring
    "hvernig",                           # how-to (soft signal)
    "af hverju", "hvers vegna",          # causal
    "hvað er", "hvað eru",               # definitional
    "hvaða",                             # ranking/selection (accept FP trade-off
                                         # on "hvaða dagsetning er í dag")
    "berðu saman", "samanburð",          # comparison
}

_KW_DEPTH_DEEP = {
    # analysis verbs (explicit)
    "greina", "greindu", "greining",
    # conditional / hypothetical (space-wrapped to avoid substring FP)
    " ef ",
    # multi-party legal
    "réttindi", "skyldur", "krefja",
    # long-range synthesis cue (hard)
    "í smáatriðum", "smáatriðum", "i smaatridum", "smaatridum",
    # multi-step setup
    "set ég upp", "set upp", "uppsetning",
}

# "saga"/"sögu" require co-occurrence (Opus suggestion 1)
_KW_DEPTH_DEEP_SAGA_GUARDED = {"saga", "sögu", "sogu"}
_KW_DEPTH_DEEP_SAGA_COUES  = {"í smáatriðum", "smáatriðum", "smaatridum",
                              "segðu mér", "segdu mer"}

# "virkar" requires "hvernig" co-occurrence (Opus suggestion 2)
_KW_DEPTH_DEEP_MECH_TRIGGER = "virkar"
_KW_DEPTH_DEEP_MECH_GUARD   = "hvernig"

'''

if '_KW_DEPTH_STANDARD' in src:
    print("SKIP patch 1: _KW_DEPTH_STANDARD already present")
else:
    src = src[:idx_insert] + NEW_LISTS + src[idx_insert:]
    print(f"patch 1 OK: inserted {len(NEW_LISTS)} bytes after _KW_PUBLIC")

# ---------- PATCH 2: replace depth-block between anchors ----------
ANCHOR_START = '    # ── 4. Reasoning depth ──'
ANCHOR_END   = '    # ── 5. Confidence ──'

if src.count(ANCHOR_START) != 1 or src.count(ANCHOR_END) != 1:
    sys.exit("depth-block anchors not unique")

idx_s = src.index(ANCHOR_START)
idx_e = src.index(ANCHOR_END)

NEW_DEPTH_BLOCK = '''    # ── 4. Reasoning depth ──
    #
    # Precedence (highest wins). Changed in S68 A.2:
    # length is now a signal, not a gate.
    #   1. Hard size limits           -> deep   (keep: long input always deep)
    #   2. DEEP keyword match         -> deep   (semantic override)
    #   3. STANDARD keyword match     -> standard
    #   4. Length < 80 and no file    -> fast   (fallback, was gate)
    #   5. Default                    -> standard (finally reachable)
    #
    # When both DEEP and STANDARD match, DEEP wins (analysis dominates
    # explanation). Documented trade-off: "hvaða X er í dag?" may route
    # standard; accepted until A.3 eval shows actual impact.
    reasoning_depth: ReasoningDepth = "standard"
    total_chars = len(q) + (file_size or 0) // 4  # grófur token-proxy

    # (1) hard size
    if total_chars > 5000 or (file_size or 0) > 100_000:
        reasoning_depth = "deep"
    else:
        # (2) DEEP keywords (with safety gates)
        deep_hit = any(kw in q_lower for kw in _KW_DEPTH_DEEP)

        # saga/sögu guard: require co-occurrence with depth cue
        if not deep_hit and any(kw in q_lower for kw in _KW_DEPTH_DEEP_SAGA_GUARDED):
            if (any(cue in q_lower for cue in _KW_DEPTH_DEEP_SAGA_COUES)
                    or total_chars > 60):
                deep_hit = True

        # virkar guard: require "hvernig" in same query
        if not deep_hit and _KW_DEPTH_DEEP_MECH_TRIGGER in q_lower:
            if _KW_DEPTH_DEEP_MECH_GUARD in q_lower:
                deep_hit = True

        if deep_hit:
            reasoning_depth = "deep"
        # (3) STANDARD keywords
        elif any(kw in q_lower for kw in _KW_DEPTH_STANDARD):
            reasoning_depth = "standard"
        # (4) length fast fallback
        elif total_chars < 80 and not filename:
            reasoning_depth = "fast"
        # (5) default is already "standard"

'''

src_new = src[:idx_s] + NEW_DEPTH_BLOCK + src[idx_e:]
if src_new == src:
    sys.exit("patch 2 produced no change")
src = src_new
print("patch 2 OK: depth-block replaced")

# ---------- write back ----------
SRC.write_text(src, encoding="utf-8")
print(f"\nwrote {SRC}: {len(src)} bytes")
print(f"lines: {src.count(chr(10))}")