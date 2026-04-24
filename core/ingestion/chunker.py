"""Sprint 68 C.2 — Legal Document Chunker.

Memory note (Opus C.1 GREEN):
  Self-hosted Qdrant á RunPod (ekki Cloud free tier).
  480K vectors x 1024 dim x float32 = ~2 GB RAM.
  Faktor: plan fyrir 4+ GB RAM á Qdrant pod.

kafli_int=None fyrir greinar a undan fyrsta kafla marker.
Empirical null-kafli count: sjá test_parse_bokhald_chunk_count.

token_counter: pluggable fyrir S69 embedding model val.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Literal, Optional
import tiktoken

from core.schemas.legal_reference import LegalReference

_ENC = tiktoken.get_encoding("cl100k_base")

def _tok(text: str) -> int:
    return len(_ENC.encode(text))

GREIN_PAT  = re.compile(
    r"(?:(?:^|\n)\s*\[?)(\d+)\.\s*gr\.(?:\s+([a-z]{1,2}))?(?=[\s.,;<\]]|$)",
    re.MULTILINE
)
MGR_PAT    = re.compile(r"(\d+)\.\s*mgr\.", re.IGNORECASE)
KAFLI_PAT  = re.compile(r"(I{1,3}V?|IV|V?I{0,3}|IX|X{1,3})\.\s*kafl[ia]", re.IGNORECASE)
REF_PAT    = re.compile(
    r"(\d+)\.\s*(?:tl|t\xf6lul)\.\s*"
    r"(?:(\d+)\.\s*mgr\.\s*)?(\d+)\.\s*gr\.(?:\s+([a-z]{1,2}))?"
    r"(?:\s+(?:laga\s+nr\.|l\.?)\s*(\d+)/(\d{4}))?",
    re.IGNORECASE
)

STRIP_PATS = [
    re.compile(r"Lagasafn[^\n]*", re.IGNORECASE),
    re.compile(r"\butg\xE1fa\s+\w+", re.IGNORECASE),
    re.compile(r"Prenta\s+\xED\s+tveimur\s+d\xE1lkum", re.IGNORECASE),
    re.compile(r"Athugu\xF0[^.]+\.", re.IGNORECASE),
    re.compile(r"\[Breytt\s+me\xF0[^\]]+\]"),
]

ROMAN = {"I":1,"II":2,"III":3,"IV":4,"V":5,"VI":6,
         "VII":7,"VIII":8,"IX":9,"X":10,"XI":11,"XII":12}


@dataclass
class Chunk:
    chunk_id: str
    law_nr: int
    law_year: int
    law_title: str
    kafli_roman: Optional[str]
    kafli_int: Optional[int]
    grein: int
    grein_suffix: Optional[str]
    malsgrein: Optional[int]
    text: str
    token_count: int
    chunk_level: Literal["grein", "malsgrein"]
    parent_chunk_id: Optional[str]
    related_refs: List[dict] = field(default_factory=list)
    source_url: str = ""
    snapshot_version: str = "157a"
    snapshot_date: str = "2026-04-24"
    token_counter: str = "tiktoken_cl100k"


class LegalDocumentChunker:
    def __init__(self, token_counter: str = "tiktoken_cl100k"):
        self.token_counter = token_counter

    def _strip(self, text: str) -> str:
        BLOCK = re.compile(r"<(?:p|div|br|h[1-6]|li|tr|td)[^>]*>", re.IGNORECASE)
        text = BLOCK.sub("\n", text)
        text = re.sub(r"<[^>]+>", " ", text)
        for pat in STRIP_PATS:
            text = pat.sub(" ", text)
        return re.sub(r"  +", " ", text).strip()

    def _extract_refs(self, text: str, law_nr: int, law_year: int) -> list:
        refs = []
        for m in REF_PAT.finditer(text):
            try:
                ext = m.group(5) is not None
                ref = LegalReference(
                    tolulidur=int(m.group(1)) if m.group(1) else None,
                    malsgrein=int(m.group(2)) if m.group(2) else None,
                    grein=int(m.group(3)),
                    grein_suffix=m.group(4),
                    law_nr=int(m.group(5)) if ext else law_nr,
                    law_year=int(m.group(6)) if ext else law_year,
                    reference_type="external_pinpoint" if ext else "internal_pinpoint",
                    raw_form=m.group(0).strip(),
                )
                refs.append(ref.model_dump())
            except Exception:
                pass
        return refs

    def _make_id(self, law_nr, law_year, grein, suffix, mgr):
        cid = f"{law_nr}_{law_year}_g{grein}"
        if suffix:
            cid += f"_{suffix}"
        if mgr:
            cid += f"_m{mgr}"
        return cid

    def parse_html(self, html: str, law_metadata: dict) -> List[Chunk]:
        nr    = law_metadata["law_nr"]
        yr    = law_metadata["law_year"]
        title = law_metadata.get("law_title", "")
        url   = law_metadata.get("source_url", "")
        clean = self._strip(html)

        # Kafli boundaries
        kafli_map = {}
        cur_kafli_roman = None
        cur_kafli_int   = None
        for km in KAFLI_PAT.finditer(clean):
            cur_kafli_roman = km.group(1).upper()
            cur_kafli_int   = ROMAN.get(cur_kafli_roman)
            kafli_map[km.start()] = (cur_kafli_roman, cur_kafli_int)
        kafli_positions = sorted(kafli_map.keys())

        def kafli_at(pos):
            roman, kint = None, None
            for kp in kafli_positions:
                if kp <= pos:
                    roman, kint = kafli_map[kp]
            return roman, kint

        chunks = []
        for gm in GREIN_PAT.finditer(clean):
            g_num = int(gm.group(1))
            g_suf = gm.group(2)
            g_start = gm.start()
            next_gm = GREIN_PAT.search(clean, gm.end())
            g_text = clean[gm.end(): next_gm.start() if next_gm else len(clean)].strip()
            k_roman, k_int = kafli_at(g_start)
            tok = _tok(g_text)
            cid = self._make_id(nr, yr, g_num, g_suf, None)
            refs = self._extract_refs(g_text, nr, yr)

            if tok > 400:
                # sub-split a malsgreinar
                mgr_splits = MGR_PAT.split(g_text)
                mgr_num = None
                for i, seg in enumerate(mgr_splits):
                    mg = re.match(r"^\d+$", seg.strip())
                    if mg:
                        mgr_num = int(seg.strip())
                        continue
                    if len(seg.strip()) < 20:
                        continue
                    mid = self._make_id(nr, yr, g_num, g_suf, mgr_num)
                    mtok = _tok(seg)
                    chunks.append(Chunk(
                        chunk_id=mid, law_nr=nr, law_year=yr,
                        law_title=title, kafli_roman=k_roman, kafli_int=k_int,
                        grein=g_num, grein_suffix=g_suf, malsgrein=mgr_num,
                        text=seg.strip(), token_count=mtok,
                        chunk_level="malsgrein", parent_chunk_id=cid,
                        related_refs=self._extract_refs(seg, nr, yr),
                        source_url=url, token_counter=self.token_counter,
                    ))
            else:
                chunks.append(Chunk(
                    chunk_id=cid, law_nr=nr, law_year=yr,
                    law_title=title, kafli_roman=k_roman, kafli_int=k_int,
                    grein=g_num, grein_suffix=g_suf, malsgrein=None,
                    text=g_text, token_count=tok,
                    chunk_level="grein", parent_chunk_id=None,
                    related_refs=refs, source_url=url,
                    token_counter=self.token_counter,
                ))
        return chunks
