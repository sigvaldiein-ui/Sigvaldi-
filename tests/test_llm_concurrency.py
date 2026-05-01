"""Unit tests for core/llm_concurrency.py (Sprint 66 A1-ii).

7 test scenarios:
  1. acquire/release happy path
  2. timeout when full (N+1th caller)
  3. bypass flag no-op
  4. feature flag disabled no-op
  5. concurrent N threads respect cap
  6. startup validation: _MAX_CONCURRENT < 1 rejected
  7. startup validation: _TIMEOUT <= 0 rejected

Tests run the module in subprocesses for env-driven config.
"""
import os
import sys
import time
import threading
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run_py_with_env(code: str, env_extra: dict) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(env_extra)
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestHappyPath(unittest.TestCase):
    def test_01_acquire_release(self):
        """Basic acquire + release must succeed and update active_count."""
        code = """
from core.llm_concurrency import llm_guard, active_count
assert active_count() == 0
with llm_guard(caller="test"):
    assert active_count() == 1
assert active_count() == 0
print("OK")
"""
        r = _run_py_with_env(code, {"INTENT_LLM_MAX_CONCURRENT": "2"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK", r.stdout)


class TestTimeout(unittest.TestCase):
    def test_02_timeout_when_full(self):
        """N+1th caller must raise TimeoutError after _TIMEOUT sec."""
        code = """
import threading, time
from core.llm_concurrency import llm_guard
holder_ready = threading.Event()
def hold():
    with llm_guard(caller="holder"):
        holder_ready.set()
        time.sleep(3)
t = threading.Thread(target=hold)
t.start()
holder_ready.wait(2)
try:
    with llm_guard(caller="late"):
        print("FAIL_should_have_timed_out")
except TimeoutError as e:
    print(f"OK_timeout: {e}")
t.join()
"""
        r = _run_py_with_env(code, {
            "INTENT_LLM_MAX_CONCURRENT": "1",
            "LLM_CONCURRENCY_TIMEOUT": "0.5",
        })
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK_timeout", r.stdout)


class TestBypass(unittest.TestCase):
    def test_03_bypass_flag(self):
        """bypass=True must skip semaphore entirely."""
        code = """
from core.llm_concurrency import llm_guard, active_count
# Fill semaphore with 1 holder
import threading, time
evt = threading.Event()
def hold():
    with llm_guard(caller="holder"):
        evt.set()
        time.sleep(2)
t = threading.Thread(target=hold)
t.start()
evt.wait(1)
# Bypass should work despite full semaphore
with llm_guard(caller="bypass_test", bypass=True):
    print("OK_bypass")
t.join()
"""
        r = _run_py_with_env(code, {"INTENT_LLM_MAX_CONCURRENT": "1"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK_bypass", r.stdout)


class TestFeatureFlag(unittest.TestCase):
    def test_04_disabled_is_noop(self):
        """When LLM_CONCURRENCY_ENABLED=false, guard is no-op."""
        code = """
from core.llm_concurrency import llm_guard, is_enabled
assert is_enabled() is False
# Should not block even with nested calls
with llm_guard(caller="a"):
    with llm_guard(caller="b"):
        with llm_guard(caller="c"):
            print("OK_nested_noop")
"""
        r = _run_py_with_env(code, {
            "INTENT_LLM_MAX_CONCURRENT": "1",
            "LLM_CONCURRENCY_ENABLED": "false",
        })
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK_nested_noop", r.stdout)


class TestConcurrentCap(unittest.TestCase):
    def test_05_concurrent_cap_respected(self):
        """N threads simultaneously must see active_count <= _MAX_CONCURRENT."""
        code = """
import threading, time
from core.llm_concurrency import llm_guard, active_count
peak = [0]
lock = threading.Lock()
def worker(i):
    with llm_guard(caller=f"w{i}"):
        with lock:
            c = active_count()
            if c > peak[0]:
                peak[0] = c
        time.sleep(0.3)
threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads: t.start()
for t in threads: t.join()
assert peak[0] <= 3, f"peak={peak[0]} exceeded cap=3"
print(f"OK_peak={peak[0]}")
"""
        r = _run_py_with_env(code, {
            "INTENT_LLM_MAX_CONCURRENT": "3",
            "LLM_CONCURRENCY_TIMEOUT": "10.0",
        })
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK_peak=", r.stdout)
        # peak should equal cap under load
        self.assertIn("OK_peak=3", r.stdout)


class TestStartupValidation(unittest.TestCase):
    def test_06_max_concurrent_must_be_ge_1(self):
        """INTENT_LLM_MAX_CONCURRENT=0 must fail-fast with ValueError."""
        code = "from core import llm_concurrency"
        r = _run_py_with_env(code, {"INTENT_LLM_MAX_CONCURRENT": "0"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("INTENT_LLM_MAX_CONCURRENT must be >= 1", r.stderr)

    def test_07_timeout_must_be_positive(self):
        """LLM_CONCURRENCY_TIMEOUT=0 must fail-fast with ValueError."""
        code = "from core import llm_concurrency"
        r = _run_py_with_env(code, {"LLM_CONCURRENCY_TIMEOUT": "0"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("LLM_CONCURRENCY_TIMEOUT must be > 0", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
