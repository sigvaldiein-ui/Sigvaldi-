# Sprint 68 — A.1 Depth Classifier Forensics

**Branch:** `sprint68-queue`
**Author:** Per (Claude Opus 4.7)
**Reviewer:** Opus 4.7 (gate before A.2)
**Date:** 2026-04-23

---

## TL;DR

`standard` F1 = 0.00 er ekki tuning-vandamál — það er **unreachable code**.
Núverandi depth classifier er **pure length/file-size heuristic** án semantic signals. Allar 6 `standard` queries í eval dataset eru 33–55 characters, langt undir 80-char þröskuldi sem routar í `fast`. Þær geta **aldrei** verið classified sem standard.

**Depth er semantic eign, ekki lengdar-eign.**
- `"greina gogn"` (11 chars) er deep
- `"Hvernig sæki ég um ökuskírteini?"` (42 chars) er standard
- Bæði líta eins út fyrir length-only classifier

---

## 1. Current depth logic (core/intent_gateway.py lines 161–166)

```python
reasoning_depth: ReasoningDepth = "standard"  # default
total_chars = len(q) + (file_size or 0) // 4
if total_chars < 80 and not filename:
    reasoning_depth = "fast"
elif total_chars > 5000 or (file_size or 0) > 100_000:
    reasoning_depth = "deep"
```

**Engin keyword signals.** Bara length + file size. Default er `standard` en hver stutt query hittir `fast` branch fyrst.

---

## 2. Confusion matrix (from s67-c-depth-confusion, n=40)
