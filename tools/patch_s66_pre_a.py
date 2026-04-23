"""Sprint 66 pre-A hotfix patcher (v2, UTF-8 hardened)."""
import re
import sys
from pathlib import Path

TARGET = Path("interfaces/web_server.py")

PERSIST_BLOCK = '''
# -- Sprint 66 pre-A hotfix: persist _beta_tracker across restarts --
import json as _json_bt
import os as _os_bt
import time as _time_bt
from pathlib import Path as _Path_bt

_BETA_TRACKER_FILE = _Path_bt(_os_bt.getenv("BETA_TRACKER_PATH", "data/beta_tracker.json"))

def _load_beta_tracker_from_disk() -> dict:
    try:
        if not _BETA_TRACKER_FILE.exists():
            return {}
        raw = _json_bt.loads(_BETA_TRACKER_FILE.read_text(encoding="utf-8"))
        now = _time_bt.time()
        # TODO(S66-A): replace with BETA_DURATION_SEC module const (defined below)
        _DUR = int(_os_bt.getenv("BETA_DURATION_SEC_OVERRIDE", 7 * 24 * 3600))
        return {ip: float(ts) for ip, ts in raw.items() if now - float(ts) <= _DUR}
    except Exception as e:
        try:
            logger.warning(f"[BETA] load failed: {type(e).__name__}: {e}")
        except Exception:
            pass
        return {}

def _save_beta_tracker_to_disk(tracker: dict) -> None:
    try:
        _BETA_TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _BETA_TRACKER_FILE.with_suffix(".tmp")
        tmp.write_text(_json_bt.dumps(tracker, indent=2), encoding="utf-8")
        tmp.replace(_BETA_TRACKER_FILE)
    except Exception as e:
        try:
            logger.warning(f"[BETA] save failed: {type(e).__name__}: {e}")
        except Exception:
            pass
# -- /persist helpers --

'''

PIDLOCK_BLOCK = '''    # -- Sprint 66 pre-A hotfix: single-instance PID lock --
    global _pid_lock_fp
    import fcntl as _fcntl_pl
    import sys as _sys_pl
    import os as _os_pl
    _PID_LOCK_PATH = _os_pl.getenv("ALVITUR_PID_LOCK", "/tmp/alvitur_web_server.lock")
    _pid_lock_fp = open(_PID_LOCK_PATH, "w", encoding="utf-8")
    try:
        _fcntl_pl.flock(_pid_lock_fp, _fcntl_pl.LOCK_EX | _fcntl_pl.LOCK_NB)
        _pid_lock_fp.write(str(_os_pl.getpid()))
        _pid_lock_fp.flush()
    except BlockingIOError:
        print(
            "[FATAL] web_server.py already running (lock: "
            + _PID_LOCK_PATH + ")",
            file=_sys_pl.stderr,
        )
        _sys_pl.exit(1)
    # -- /PID lock --
'''

PIDLOCK_GLOBAL_DECL = '''# -- Sprint 66 pre-A: module-level PID lock file pointer (so refactor-safe) --
_pid_lock_fp = None
# -- /PID lock global --

'''


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: {TARGET} not found", file=sys.stderr)
        return 1

    src = TARGET.read_text(encoding="utf-8")

    # ── Patch 1: persist block before Sprint 62 anchor ──
    if "Sprint 66 pre-A hotfix: persist _beta_tracker" in src:
        print("SKIP: persist block already applied")
    else:
        m = re.search(
            r"#\s*[\u2500\-]{2,}\s*Sprint 62:\s*Beta tracker\s*[\u2500\-]{2,}",
            src,
        )
        if not m:
            print("ERROR: Sprint 62 Beta tracker anchor not found", file=sys.stderr)
            return 2
        anchor = m.group(0)
        src = src.replace(anchor, PERSIST_BLOCK + anchor, 1)
        print(f"OK: inserted persist block (anchor: {anchor!r})")

    # ── Patch 2: _promota_beta adds save call ──
    if "_save_beta_tracker_to_disk(_beta_tracker)" in src:
        print("SKIP: _promota_beta already patched")
    else:
        m = re.search(
            r"(def _promota_beta\(ip: str\) -> None:\s*\n"
            r"(?:[ \t]*\"\"\"[^\"]*\"\"\"\s*\n)?"
            r"[ \t]*import time as _t\s*\n"
            r"[ \t]*_beta_tracker\[ip\] = _t\.time\(\)\s*\n)",
            src,
        )
        if not m:
            print("ERROR: _promota_beta body not matched", file=sys.stderr)
            return 3
        original = m.group(1)
        patched = original.rstrip() + "\n    _save_beta_tracker_to_disk(_beta_tracker)\n"
        src = src.replace(original, patched, 1)
        print("OK: patched _promota_beta")

    # ── Patch 3: load-at-startup after end anchor ──
    if "_beta_tracker.update(_load_beta_tracker_from_disk())" in src:
        print("SKIP: load-at-startup already present")
    else:
        m = re.search(
            r"#\s*[\u2500\-]{2,}\s*/Sprint 62 Beta tracker\s*[\u2500\-]{2,}\s*\n",
            src,
        )
        if not m:
            print("WARN: end anchor not found, load call skipped")
        else:
            end_line = m.group(0)
            replacement = end_line + "_beta_tracker.update(_load_beta_tracker_from_disk())\n"
            src = src.replace(end_line, replacement, 1)
            print("OK: inserted load-at-startup call")

    # ── Patch 4a: module-level _pid_lock_fp declaration (for global refactor-safety) ──
    if "_pid_lock_fp = None" in src:
        print("SKIP: _pid_lock_fp global already declared")
    else:
        # Insert right before "if __name__ == ..." block
        m = re.search(r"(\nif __name__ == ['\"]__main__['\"]:\s*\n)", src)
        if m:
            src = src.replace(m.group(1), "\n" + PIDLOCK_GLOBAL_DECL + m.group(1), 1)
            print("OK: inserted _pid_lock_fp global declaration")

    # ── Patch 4b: PID lock inside __main__ ──
    if "Sprint 66 pre-A hotfix: single-instance PID lock" in src:
        print("SKIP: PID lock already applied")
    else:
        m = re.search(r"(if __name__ == ['\"]__main__['\"]:\s*\n)", src)
        if not m:
            print("WARN: no __main__ block; PID lock skipped")
        else:
            src = src.replace(m.group(1), m.group(1) + PIDLOCK_BLOCK, 1)
            print("OK: inserted PID lock")

    TARGET.write_text(src, encoding="utf-8")
    print("WRITE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
