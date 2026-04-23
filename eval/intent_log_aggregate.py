#!/usr/bin/env python3
"""
Sprint 66 Track B3 — Intent log aggregator (zero PII).

Parses [INTENT] log lines emitted by interfaces/web_server.py _log_intent()
and produces aggregate statistics. Does NOT read or persist any raw query
text, IP address, or user identifier.

Input log format (one line per classification):
  YYYY-MM-DD HH:MM:SS [INFO] alvitur.web: [INTENT] endpoint=X domain=Y \
    depth=Z conf=N.NN sens=L adapter=A src=S

Usage:
  python3 eval/intent_log_aggregate.py [--logs PATH ...] [--out PATH]

Defaults scan both /workspace/web_server.log and logs/web_server.log.
Output path defaults to eval/intent_live_stats_{YYYY-MM-DD}.json.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

# Tolerant regex: named groups, each field optional in case log format drifts.
LINE_RE = re.compile(
    r"\[INTENT\]\s+"
    r"endpoint=(?P<endpoint>\S+)\s+"
    r"domain=(?P<domain>\S+)\s+"
    r"depth=(?P<depth>\S+)\s+"
    r"conf=(?P<conf>[\d.]+)\s+"
    r"sens=(?P<sens>\S+)\s+"
    r"adapter=(?P<adapter>\S+)\s+"
    r"src=(?P<src>\S+)"
)

CONF_BUCKETS = [
    ("<0.50", 0.00, 0.50),
    ("0.50-0.60", 0.50, 0.60),
    ("0.60-0.80", 0.60, 0.80),
    ("0.80-1.00", 0.80, 1.0001),
]


def bucket_conf(c: float) -> str:
    for label, lo, hi in CONF_BUCKETS:
        if lo <= c < hi:
            return label
    return "out_of_range"


def parse_lines(paths: Iterable[Path]) -> list[dict]:
    rows: list[dict] = []
    for p in paths:
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                m = LINE_RE.search(line)
                if not m:
                    continue
                d = m.groupdict()
                try:
                    d["conf"] = float(d["conf"])
                except ValueError:
                    continue
                d["_source_file"] = str(p)
                rows.append(d)
    return rows


def aggregate(rows: list[dict]) -> dict:
    n = len(rows)
    by_endpoint = Counter(r["endpoint"] for r in rows)
    by_domain = Counter(r["domain"] for r in rows)
    by_depth = Counter(r["depth"] for r in rows)
    by_sens = Counter(r["sens"] for r in rows)
    by_adapter = Counter(r["adapter"] for r in rows)
    by_source = Counter(r["src"] for r in rows)
    conf_buckets = Counter(bucket_conf(r["conf"]) for r in rows)
    by_endpoint_domain = Counter((r["endpoint"], r["domain"]) for r in rows)
    by_source_file = Counter(r["_source_file"] for r in rows)

    confs = [r["conf"] for r in rows] or [0.0]
    conf_stats = {
        "min": round(min(confs), 3),
        "max": round(max(confs), 3),
        "mean": round(sum(confs) / max(1, n), 3),
        "p50": round(sorted(confs)[len(confs) // 2], 3) if confs else 0.0,
    }

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "n_total": n,
        "by_endpoint": dict(by_endpoint),
        "by_domain": dict(by_domain),
        "by_depth": dict(by_depth),
        "by_sensitivity": dict(by_sens),
        "by_adapter": dict(by_adapter),
        "by_source": dict(by_source),
        "confidence_buckets": {k: conf_buckets.get(k, 0)
                                for k, _, _ in CONF_BUCKETS},
        "confidence_stats": conf_stats,
        "by_endpoint_domain": {f"{e}|{d}": c
                                for (e, d), c in by_endpoint_domain.items()},
        "by_source_file": dict(by_source_file),
        "schema_version": 1,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", nargs="*", default=[
        "/workspace/web_server.log",
        "logs/web_server.log",
    ])
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ap.add_argument("--out", default=f"eval/intent_live_stats_{date_str}.json")
    args = ap.parse_args()

    paths = [Path(p) for p in args.logs]
    rows = parse_lines(paths)
    if not rows:
        print(f"WARN: no [INTENT] lines found in {args.logs}", file=sys.stderr)
    stats = aggregate(rows)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    print(f"wrote {out_path}: {out_path.stat().st_size} bytes, "
          f"n_total={stats['n_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
