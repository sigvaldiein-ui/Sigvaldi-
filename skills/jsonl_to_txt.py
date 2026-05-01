#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jsonl_to_txt.py
---------------
Umbreytir JSONL skrár frá Mímir/Whisper í lesanlegar TXT skrár
til notkunar í Google Drive og annars staðar.

Höfundur: Mímir-kerfið
Dagsetning: 2026-03-28
"""

import json
import os
import glob
from datetime import date
from pathlib import Path


# --- Stillingar ---
# Algild slóð að JSONL gagnaskrám
JSONL_MAPPA = Path("/workspace/mimir_net/data")

# Algild slóð að úttaksmöppu fyrir TXT skrár
TXT_MAPPA = JSONL_MAPPA / "txt"


def telja_ord(texti: str) -> int:
    if not texti:
        return 0
    return len(texti.split())


def lesa_jsonl_skra(slod: Path) -> list:
    hlutir = []
    with open(slod, "r", encoding="utf-8") as f:
        for linunumer, lina in enumerate(f, start=1):
            lina = lina.strip()
            if not lina:
                continue
            try:
                hlutur = json.loads(lina)
                hlutir.append(hlutur)
            except json.JSONDecodeError as villa:
                print(f"  [Viðvörun] Lína {linunumer} í '{slod.name}' er ekki gilt JSON: {villa}")
    return hlutir


def smida_txt_innihald(segments: list, upprunaskra: str) -> str:
    textalisti = []
    heildarord = 0
    for segment in segments:
        texti = segment.get("text", "").strip()
        if texti:
            textalisti.append(texti)
            heildarord += telja_ord(texti)
    dagsetning = date.today().isoformat()
    fjoldi_segments = len(segments)
    fyrirsogn = (
        f"=== Mímir RÚV gagnasafn ===\n"
        f"Upprunaleg skrá: {upprunaskra}\n"
        f"Dagsetning: {dagsetning}\n"
        f"Segments: {fjoldi_segments}\n"
        f"Heildarorð: ~{heildarord:,}\n"
        f"\n---\n\n"
    )
    meginmal = "\n".join(textalisti)
    return fyrirsogn + meginmal


def umbreyta_einni_skra(jsonl_slod: Path) -> bool:
    try:
        txt_nafn = jsonl_slod.stem + ".txt"
        txt_slod = TXT_MAPPA / txt_nafn
        segments = lesa_jsonl_skra(jsonl_slod)
        if not segments:
            print(f"  [Viðvörun] '{jsonl_slod.name}' er tóm — sleppt.")
            return False
        innihald = smida_txt_innihald(segments, jsonl_slod.name)
        with open(txt_slod, "w", encoding="utf-8") as f:
            f.write(innihald)
        heildarord = telja_ord(" ".join(seg.get("text", "") for seg in segments))
        print(f"  Umbreytti {jsonl_slod.name} → {txt_nafn} ({len(segments)} segments, ~{heildarord:,} orð)")
        return True
    except Exception as villa:
        print(f"  [Villa] '{jsonl_slod.name}': {villa}")
        return False


def keyra_umbreytingu() -> None:
    print("=" * 50)
    print("  Mímir JSONL → TXT umbreytir")
    print("=" * 50)
    if not JSONL_MAPPA.exists():
        print(f"[Villa] Gagnamappa finnst ekki: {JSONL_MAPPA}")
        return
    try:
        TXT_MAPPA.mkdir(parents=True, exist_ok=True)
        print(f"Úttaksmappa: {TXT_MAPPA}")
    except OSError as villa:
        print(f"[Villa] Gat ekki búið til úttaksmöppu: {villa}")
        return
    jsonl_skrar = sorted(JSONL_MAPPA.glob("*.jsonl"))
    if not jsonl_skrar:
        print(f"\n[Upplýsing] Engar *.jsonl skrár fundust í: {JSONL_MAPPA}")
        return
    print(f"\nFann {len(jsonl_skrar)} JSONL skrár — byrja umbreytingu...\n")
    tokst = 0
    mistokst = 0
    for jsonl_slod in jsonl_skrar:
        if umbreyta_einni_skra(jsonl_slod):
            tokst += 1
        else:
            mistokst += 1
    print("\n" + "=" * 50)
    print(f"  Lokið! Umbreytt: {tokst}  |  Mistókst: {mistokst}")
    print(f"  TXT skrár vistaðar í: {TXT_MAPPA}")
    print("=" * 50)


if __name__ == "__main__":
    keyra_umbreytingu()
