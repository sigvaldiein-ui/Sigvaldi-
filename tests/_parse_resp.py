#!/usr/bin/env python3
# tests/_parse_resp.py — helper for smoke.sh to extract fields from JSON
import json, sys
field = sys.argv[1] if len(sys.argv) > 1 else "summary"
try:
    data = json.loads(sys.stdin.read() or "{}")
except Exception:
    print("")
    sys.exit(0)
if field == "answer":
    print((data.get("summary") or data.get("response") or "")[:500])
else:
    print(data.get(field, ""))
