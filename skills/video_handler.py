"""
video_handler.py — Mímir Video/Audio Pipeline
=============================================
Sprint 7 | Smíðað af Per (Yfirverkfræðingur)

Safnar íslensku hljóð/myndbandaefni frá RÚV, Alþingi og öðrum
íslenskum uppsprettum. Notar yt-dlp til að hlaða niður og
faster-whisper til að gera þetta að texta (JSONL).

FLÆÐI:
  1. fetch_ruv_schedule()  → list[dict]   # dagskrá í dag
  2. download_audio()       → wav_path     # yt-dlp → ffmpeg → wav
  3. transcribe()           → str          # faster-whisper-large-v3
  4. save_to_jsonl()        → str          # vistar í /workspace/mimir_net/data/
  5. run_pipeline()         → dict         # keyrir allt
"""

import os
import re
import json
import time
import logging
import subprocess
import tempfile
from datetime import datetime, date
from pathlib import Path

import requests

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [video_handler] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Stillingar ────────────────────────────────────────────────────────────────
MODELS_DIR = os.getenv("MODELS_DIR", "/workspace/models")
DATA_DIR   = os.getenv("DATA_DIR",   "/workspace/mimir_net/data")
AUDIO_TMP  = os.getenv("AUDIO_TMP",  "/tmp/mimir_audio")
WHISPER_MODEL = "large-v3"

# Whisper model path (already downloaded)
WHISPER_PATH = os.path.join(
    MODELS_DIR,
    "models--Systran--faster-whisper-large-v3",
    "snapshots"
)

# Jina reader prefix
JINA_PREFIX = "https://r.jina.ai/"

# Hámarks sekúndur per klip (forðumst mjög löng myndskeið)
MAX_DURATION_SEC = 3600  # 1 klst


# ── 1. DAGSKRÁ ────────────────────────────────────────────────────────────────

def fetch_ruv_schedule(target_date: str | None = None) -> list[dict]:
    """
    Sækir dagskrá frá RÚV fyrir ákveðinn dag (YYYY-MM-DD).
    Skilar lista af {'title': str, 'url': str, 'time': str}.
    """
    if target_date is None:
        target_date = date.today().isoformat()

    jina_url = f"{JINA_PREFIX}https://www.ruv.is/dagskra"
    log.info(f"Sæki dagskrá: {jina_url}")

    try:
        resp = requests.get(jina_url, timeout=30)
        resp.raise_for_status()
        text = resp.text
    except Exception as e:
        log.error(f"Gat ekki sótt dagskrá: {e}")
        return []

    # Finnur spila-slóðir og titla
    # Dæmi: [13:00 Fréttir](https://www.ruv.is/sjonvarp/dagskra/ruv/2026-03-27/5462563)
    #        [https://www.ruv.is/sjonvarp/spila/.../bfcsod]
    entries = []

    # Finn dagskrá items með dagsetningunni
    dagskra_pattern = re.compile(
        r'\[(\d{2}:\d{2} [^\]]+)\]\(https://www\.ruv\.is/sjonvarp/dagskra/ruv/' +
        re.escape(target_date) + r'/\d+\).*?\n\[(https://www\.ruv\.is/sjonvarp/spila/[^\)]+)\]',
        re.DOTALL
    )

    for m in dagskra_pattern.finditer(text):
        time_title = m.group(1).strip()
        spila_url  = m.group(2).strip()
        parts = time_title.split(" ", 1)
        entries.append({
            "time":  parts[0] if len(parts) > 1 else "",
            "title": parts[1] if len(parts) > 1 else time_title,
            "url":   spila_url,
        })

    log.info(f"Fann {len(entries)} klip á dagskrá {target_date}")
    return entries


# ── 2. NIÐURHAL ──────────────────────────────────────────────────────────────

def _find_whisper_snapshot() -> str:
    """Finnur rétta snapshot möppuna fyrir faster-whisper-large-v3."""
    snap_dir = Path(WHISPER_PATH)
    if not snap_dir.exists():
        raise FileNotFoundError(f"Whisper snapshots not found: {WHISPER_PATH}")
    snapshots = sorted(snap_dir.iterdir())
    if not snapshots:
        raise FileNotFoundError("No snapshots in whisper directory")
    return str(snapshots[-1])  # nýjasta snapshot


def download_audio(url: str, out_dir: str | None = None) -> str | None:
    """
    Notar yt-dlp til að hlaða niður audio frá RÚV spila URL.
    Skilar slóð á .wav skrá (16kHz mono) eða None ef mistókst.

    Args:
        url:     https://www.ruv.is/sjonvarp/spila/...
        out_dir: möppu til að vista í (default: AUDIO_TMP)

    Returns:
        Slóð á .wav skrá eða None
    """
    if out_dir is None:
        out_dir = AUDIO_TMP
    os.makedirs(out_dir, exist_ok=True)

    # Búum til temp skrá
    tmp_file = os.path.join(out_dir, f"ruv_{int(time.time())}")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--postprocessor-args", "ffmpeg:-ar 16000 -ac 1",  # 16kHz mono
        "--max-filesize", "500m",
        "-o", tmp_file + ".%(ext)s",
        "--no-progress",
        url,
    ]

    log.info(f"Hleð niður: {url}")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            log.error(f"yt-dlp villa: {result.stderr[-500:]}")
            return None
    except subprocess.TimeoutExpired:
        log.error("yt-dlp tímaði út (300s)")
        return None
    except Exception as e:
        log.error(f"yt-dlp undantekningarvilla: {e}")
        return None

    # Finnur úttak .wav skrá
    wav_path = tmp_file + ".wav"
    if not os.path.exists(wav_path):
        # Leita að öðrum .wav skrám í möppunni
        found = list(Path(out_dir).glob(f"ruv_*.wav"))
        if found:
            wav_path = str(sorted(found)[-1])
        else:
            log.error(f"WAV skrá finnst ekki eftir niðurhal")
            return None

    size_mb = os.path.getsize(wav_path) / 1024 / 1024
    log.info(f"Niðurhal tókst: {wav_path} ({size_mb:.1f} MB)")
    return wav_path


# ── 3. ÞÝÐING (TRANSCRIPTION) ─────────────────────────────────────────────────

def transcribe(wav_path: str, language: str = "is") -> dict | None:
    """
    Keyrir faster-whisper-large-v3 á .wav skrá.
    Skilar {'text': str, 'segments': list, 'duration': float}.

    Args:
        wav_path: slóð á 16kHz mono WAV
        language: ISO kóði ('is' = íslenska)

    Returns:
        dict með text og segments eða None ef villa
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        log.error("faster_whisper er ekki uppsett: pip install faster-whisper")
        return None

    # Finna model
    try:
        model_path = _find_whisper_snapshot()
        log.info(f"Hleð Whisper model: {model_path}")
    except FileNotFoundError as e:
        log.error(str(e))
        return None

    try:
        model = WhisperModel(
            model_path,
            device="cuda",          # GPU á RunPod
            compute_type="float16", # hraðast á A100/H100
        )
    except Exception:
        log.warning("CUDA mistókst, prófar CPU")
        model = WhisperModel(model_path, device="cpu", compute_type="int8")

    log.info(f"Þýði: {wav_path}")
    try:
        segments_gen, info = model.transcribe(
            wav_path,
            language=language,
            beam_size=5,
            vad_filter=True,        # hreinsar þögn
            vad_parameters={"min_silence_duration_ms": 500},
        )

        segments = []
        full_text = []
        for seg in segments_gen:
            segments.append({
                "start": round(seg.start, 2),
                "end":   round(seg.end, 2),
                "text":  seg.text.strip(),
            })
            full_text.append(seg.text.strip())

        result = {
            "text":     " ".join(full_text),
            "segments": segments,
            "duration": round(info.duration, 1),
            "language": info.language,
        }
        log.info(f"Þýðing tókst: {len(segments)} hlutar, {info.duration:.0f}s")
        return result

    except Exception as e:
        log.error(f"Whisper villa: {e}")
        return None


# ── 4. VISTA SEM JSONL ────────────────────────────────────────────────────────

def save_video_jsonl(
    title: str,
    url: str,
    transcript: dict,
    source: str = "ruv",
    out_dir: str | None = None,
) -> str | None:
    """
    Vistar þýðingu sem JSONL í Mímir gagnasafni.

    Snið:
      {"id": "...", "source": "ruv", "title": "...", "url": "...",
       "text": "...", "segments": [...], "duration": ...,
       "language": "is", "collected_at": "..."}

    Returns:
        Slóð á JSONL skrá eða None
    """
    if out_dir is None:
        out_dir = DATA_DIR
    os.makedirs(out_dir, exist_ok=True)

    today = date.today().isoformat()
    filename = f"video_{source}_{today}.jsonl"
    filepath = os.path.join(out_dir, filename)

    record = {
        "id":           f"{source}_{int(time.time())}",
        "source":       source,
        "title":        title,
        "url":          url,
        "text":         transcript.get("text", ""),
        "segments":     transcript.get("segments", []),
        "duration":     transcript.get("duration", 0),
        "language":     transcript.get("language", "is"),
        "collected_at": datetime.utcnow().isoformat() + "Z",
    }

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    size_kb = os.path.getsize(filepath) / 1024
    log.info(f"Vistað → {filepath} ({size_kb:.1f} KB)")
    return filepath


# ── 5. MEGINFLÆÐI ─────────────────────────────────────────────────────────────

def run_pipeline(
    max_clips: int = 5,
    target_date: str | None = None,
    upload_to_drive: bool = True,
) -> dict:
    """
    Keyrir heildarleiðsluna:
      dagskrá → niðurhal → þýðing → JSONL → Drive

    Args:
        max_clips:       hámark klip í einni keyrslu
        target_date:     YYYY-MM-DD (default: í dag)
        upload_to_drive: hleður upp á Shared Drive eftir keyrslu

    Returns:
        {'processed': int, 'failed': int, 'files': list[str]}
    """
    stats = {"processed": 0, "failed": 0, "files": []}

    # 1. Dagskrá
    schedule = fetch_ruv_schedule(target_date)
    if not schedule:
        log.warning("Engin dagskrá fannst")
        return stats

    # Takmarkar við max_clips
    clips = schedule[:max_clips]
    log.info(f"Keyri pipeline á {len(clips)} klipum")

    for clip in clips:
        title = clip["title"]
        url   = clip["url"]
        log.info(f"── Vinn: {title} ({url})")

        # 2. Niðurhal
        wav_path = download_audio(url)
        if not wav_path:
            log.warning(f"Sleppi: {title}")
            stats["failed"] += 1
            continue

        # 3. Þýðing
        transcript = transcribe(wav_path)

        # Hreinsa upp WAV
        try:
            os.remove(wav_path)
        except Exception:
            pass

        if not transcript:
            log.warning(f"Þýðing mistókst: {title}")
            stats["failed"] += 1
            continue

        # 4. Vista
        out_file = save_video_jsonl(
            title=title,
            url=url,
            transcript=transcript,
            source="ruv",
        )
        if out_file:
            stats["processed"] += 1
            if out_file not in stats["files"]:
                stats["files"].append(out_file)

    # 5. Drive upload
    if upload_to_drive and stats["files"]:
        try:
            import sys
            sys.path.insert(0, "/workspace/mimir_net")
            from skills.drive_tool import sync_to_drive
            FOLDER_ID = "0AMDsY618eKP8Uk9PVA"
            for f in stats["files"]:
                sync_to_drive(f, FOLDER_ID)
                log.info(f"Hlaðið upp á Drive: {f}")
        except Exception as e:
            log.warning(f"Drive upload mistókst: {e}")

    log.info(
        f"Pipeline lokið: {stats['processed']} unnin, "
        f"{stats['failed']} mistókust"
    )
    return stats


# ── KEYRSLA ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mímir Video Handler")
    parser.add_argument("--clips",  type=int, default=3,    help="Fjöldi klipa")
    parser.add_argument("--date",   type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--no-drive", action="store_true",  help="Sleppa Drive upload")
    args = parser.parse_args()

    result = run_pipeline(
        max_clips=args.clips,
        target_date=args.date,
        upload_to_drive=not args.no_drive,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
