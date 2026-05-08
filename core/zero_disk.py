"""
Sprint 80b — Zero-Disk Hvelfingin
Zero-Disk utility module for Alvitur.is
Replaces disk writes with /dev/shm (tmpfs) for GENERAL PDF processing.
Implements session cleanup, pressure monitoring, and swap assertions.
"""
import os
import time
import asyncio
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("alvitur.zero_disk")

# Constants
ZERO_DISK_ROOT = Path("/dev/shm/alvitur_zero_disk")
MAX_PER_SESSION_BYTES = 100 * 1024 * 1024  # 100 MB
SHM_PRESSURE_THRESHOLD = 0.80  # 80% of /dev/shm
SESSION_IDLE_SECONDS = 5 * 60  # 5 minutes
SESSION_MAX_AGE_SECONDS_VAULT = 30 * 60  # 30 minutes VAULT (Gate 10)
SESSION_MAX_AGE_SECONDS_GENERAL = 60 * 60  # 60 minutes GENERAL

# Session tracking: {session_id: last_activity_timestamp}
_session_activity: Dict[str, float] = {}


def _get_shm_usage() -> tuple:
    """Returns (used_bytes, total_bytes) for /dev/shm."""
    stat = os.statvfs("/dev/shm")
    total = stat.f_frsize * stat.f_blocks
    available = stat.f_frsize * stat.f_bavail
    used = total - available
    return used, total


def check_pressure() -> bool:
    """Returns True if /dev/shm is above pressure threshold (Gate 11)."""
    used, total = _get_shm_usage()
    if total == 0:
        return False
    ratio = used / total
    if ratio > SHM_PRESSURE_THRESHOLD:
        logger.warning(f"/dev/shm pressure HIGH: {ratio:.1%} ({used}/{total})")
        return True
    return False


def setup_zero_disk():
    """Gate 9: Assert swap is off, create zero-disk directory."""
    # Verify swap is off
    try:
        with open("/proc/swaps", "r") as f:
            lines = f.readlines()
        if len(lines) > 1:  # Header + at least one swap entry
            swap_info = lines[1].strip()
            if swap_info:
                logger.critical("SWAP IS ACTIVE! Zero-Disk refusing to start.")
                logger.critical(f"Swap entry: {swap_info}")
                raise RuntimeError(
                    "Swap is active. Zero-Disk Hvelfingin requires swapoff -a. "
                    "Refusing to start for data security."
                )
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Could not read /proc/swaps: {e}")

    logger.info("Swap check passed — no active swap.")

    # Create zero-disk root
    ZERO_DISK_ROOT.mkdir(parents=True, exist_ok=True)
    logger.info(f"Zero-Disk root created at {ZERO_DISK_ROOT}")


def touch_session(session_id: str):
    """Update last activity timestamp for a session."""
    _session_activity[session_id] = time.time()


def get_session_dir(session_id: str) -> Path:
    """Get or create per-session directory."""
    session_dir = ZERO_DISK_ROOT / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def get_session_size(session_id: str) -> int:
    """Return total bytes used by a session directory."""
    session_dir = ZERO_DISK_ROOT / session_id
    if not session_dir.exists():
        return 0
    total = 0
    for f in session_dir.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total


def session_can_accept(session_id: str, incoming_bytes: int) -> bool:
    """Check if a session can accept an upload of given size (per-session quota)."""
    current = get_session_size(session_id)
    return (current + incoming_bytes) <= MAX_PER_SESSION_BYTES


def cleanup_session(session_id: str):
    """Remove all files for a session."""
    session_dir = ZERO_DISK_ROOT / session_id
    if session_dir.exists():
        shutil.rmtree(session_dir)
        logger.info(f"Cleaned up session {session_id}")
    _session_activity.pop(session_id, None)


async def idle_cleanup_loop():
    """Background task: clean up sessions idle > 5 min or older than tier max age (Gate 10)."""
    while True:
        try:
            now = time.time()
            expired = []
            for sid, last_active in list(_session_activity.items()):
                age = now - last_active
                # Determine max age from tier (stored in session metadata)
                if sid.startswith("vault:"):
                    max_age = SESSION_MAX_AGE_SECONDS_VAULT
                else:
                    max_age = SESSION_MAX_AGE_SECONDS_GENERAL
                if age > max_age:
                    logger.info(f"Session {sid[:12]}... expired (max age {age:.0f}s, tier max {max_age}s)")
                    expired.append(sid)
                elif age > SESSION_IDLE_SECONDS:
                    logger.info(f"Session {sid[:12]}... idle cleanup ({age:.0f}s)")
                    expired.append(sid)

            for sid in expired:
                cleanup_session(sid)

            # Log pressure status periodically
            if check_pressure():
                logger.warning("/dev/shm pressure high — backpressure active")
        except Exception as e:
            logger.error(f"Cleanup loop error: {e}")

        await asyncio.sleep(60)  # Run every 60 seconds
