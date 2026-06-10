"""Gazetteer — deterministic nafnavörn."""
import os
from typing import List, Tuple, Set
_GAZETTEER: Set[str] = set()
def _load_gazetteer():
    global _GAZETTEER
    if _GAZETTEER: return _GAZETTEER
    path = "/workspace/Sigvaldi-/data/safety/mannanofn_beygingar.txt"
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f:
            _GAZETTEER = {line.strip() for line in f if line.strip()}
    return _GAZETTEER
AMBIGUOUS = {"vörn","bára","frosti","logi","svala","björk","steinn","höfn","hafnar","dómur","rétti","skjöldur","stormur"}
def find_nofn_gazetteer(text: str) -> List[Tuple[int,int,str]]:
    gaz = _load_gazetteer()
    found = []
    for m in __import__("re").finditer(r'\b[A-ZÁÉÍÓÚÝÞÆÖa-záéíóúýðþæö]+\b', text):
        w = m.group()
        if w.lower() in gaz:
            found.append((m.start(), m.end(), w))
    return found
