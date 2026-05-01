"""Synthetic concurrency eval for S66 A1 (no live OpenRouter calls).

Each configuration runs in isolated subprocess to prevent module caching
issues with mock.patch and re-imports.
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


RUNNER_CODE = r"""
import os, sys, time, threading, json
from unittest.mock import patch, MagicMock

sys.path.insert(0, ".")
from core import llm_concurrency, llm_client

N_CALLS = int(os.environ["EVAL_N_CALLS"])
SLEEP_MS = int(os.environ["EVAL_SLEEP_MS"])

peak_active = [0]
peak_lock = threading.Lock()

def fake_post(*args, **kwargs):
    with peak_lock:
        c = llm_concurrency.active_count()
        if c > peak_active[0]:
            peak_active[0] = c
    time.sleep(SLEEP_MS / 1000.0)
    m = MagicMock()
    m.status_code = 200
    m.json.return_value = {
        "choices": [{"message": {"content": '{"domain":"test","reasoning_depth":"shallow","confidence_score":0.9}'}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10},
    }
    m.text = '{}'
    return m

latencies = []
errors = []
lat_lock = threading.Lock()

def worker(i):
    t0 = time.monotonic()
    try:
        llm_client.call_openrouter(
            model="test-model", prompt="test", timeout=5.0,
            caller=f"eval-{i}", request_id=f"req-{i}",
        )
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        with lat_lock:
            latencies.append(elapsed_ms)
    except Exception as e:
        with lat_lock:
            errors.append(f"{type(e).__name__}: {e}")

with patch("core.llm_client.requests.post", side_effect=fake_post):
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(N_CALLS)]
    t_start = time.monotonic()
    for t in threads: t.start()
    for t in threads: t.join()
    total_s = time.monotonic() - t_start

latencies.sort()
n = len(latencies)
def pct(p):
    return latencies[min(n-1, int(n*p))] if latencies else 0

result = {
    "config": {
        "max_concurrent": llm_concurrency.max_concurrent(),
        "enabled": llm_concurrency.is_enabled(),
        "n_calls": N_CALLS,
        "sleep_ms": SLEEP_MS,
    },
    "results": {
        "n_success": n,
        "n_error": len(errors),
        "total_wall_s": round(total_s, 3),
        "latency_p50_ms": pct(0.50),
        "latency_p95_ms": pct(0.95),
        "latency_p99_ms": pct(0.99),
        "latency_min_ms": latencies[0] if latencies else 0,
        "latency_max_ms": latencies[-1] if latencies else 0,
        "peak_active_count": peak_active[0],
        "errors": errors[:5],
    },
}
print("RESULT_JSON_START")
print(json.dumps(result))
print("RESULT_JSON_END")
"""


def run_eval_subprocess(max_concurrent: int, enabled: bool, n_calls: int = 20,
                         sleep_ms: int = 500) -> dict:
    env = os.environ.copy()
    env["INTENT_LLM_MAX_CONCURRENT"] = str(max_concurrent)
    env["LLM_CONCURRENCY_ENABLED"] = "true" if enabled else "false"
    env["LLM_CONCURRENCY_TIMEOUT"] = "30.0"
    env["OPENROUTER_API_KEY"] = "fake-key-for-eval"
    env["EVAL_N_CALLS"] = str(n_calls)
    env["EVAL_SLEEP_MS"] = str(sleep_ms)
    env["PYTHONPATH"] = str(ROOT)

    r = subprocess.run(
        [sys.executable, "-c", RUNNER_CODE],
        env=env, capture_output=True, text=True, timeout=60,
        cwd=str(ROOT),
    )
    if r.returncode != 0:
        print(f"SUBPROCESS FAILED:\n{r.stderr}")
        raise RuntimeError("eval subprocess failed")
    start = r.stdout.find("RESULT_JSON_START\n")
    end = r.stdout.find("RESULT_JSON_END")
    if start < 0 or end < 0:
        raise RuntimeError(f"could not find result markers in output:\n{r.stdout}")
    js = r.stdout[start + len("RESULT_JSON_START\n"):end].strip()
    return json.loads(js)


def main():
    print("=" * 60)
    print("S66 A1 synthetic concurrency eval (subprocess-isolated)")
    print("=" * 60)

    baseline = run_eval_subprocess(max_concurrent=20, enabled=False)
    print("\n--- BASELINE (guard disabled) ---")
    print(json.dumps(baseline, indent=2))

    guarded_n2 = run_eval_subprocess(max_concurrent=2, enabled=True)
    print("\n--- GUARDED N=2 ---")
    print(json.dumps(guarded_n2, indent=2))

    guarded_n4 = run_eval_subprocess(max_concurrent=4, enabled=True)
    print("\n--- GUARDED N=4 ---")
    print(json.dumps(guarded_n4, indent=2))

    assert baseline["results"]["n_error"] == 0, "baseline errors"
    assert guarded_n2["results"]["n_error"] == 0, "N=2 errors"
    assert guarded_n4["results"]["n_error"] == 0, "N=4 errors"
    assert guarded_n2["results"]["peak_active_count"] <= 2, \
        f"N=2 cap breached: peak={guarded_n2['results']['peak_active_count']}"
    assert guarded_n2["results"]["peak_active_count"] >= 2, \
        f"N=2 cap not reached: peak={guarded_n2['results']['peak_active_count']} (should saturate at 2)"
    assert guarded_n4["results"]["peak_active_count"] <= 4, \
        f"N=4 cap breached: peak={guarded_n4['results']['peak_active_count']}"
    assert guarded_n4["results"]["peak_active_count"] >= 3, \
        f"N=4 cap not saturated: peak={guarded_n4['results']['peak_active_count']} (expected >=3)"
    # Timing sanity: N=2 must take significantly longer than baseline
    assert guarded_n2["results"]["total_wall_s"] > baseline["results"]["total_wall_s"] * 3, \
        f"N=2 wall ({guarded_n2['results']['total_wall_s']}s) should be >3x baseline ({baseline['results']['total_wall_s']}s)"
    print("\n✅ ALL ASSERTIONS PASSED")

    out = {
        "sprint": "S66-A1",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "baseline_no_guard": baseline,
        "guarded_n2": guarded_n2,
        "guarded_n4": guarded_n4,
    }
    Path("eval/s66_a1_concurrency.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    print("saved to eval/s66_a1_concurrency.json")


if __name__ == "__main__":
    main()
