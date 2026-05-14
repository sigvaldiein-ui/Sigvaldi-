#!/usr/bin/env python3
"""Nefndarvél Alvitur.is – Dregur út nefndir, greinir kyn, tengir lög."""
import requests
from bs4 import BeautifulSoup
import json
import re
import time
from pathlib import Path
from datetime import datetime

HEADERS = {"User-Agent": "Alvitur.is/1.0 sovereign-research@alvitur.is"}
BASE = "https://web.archive.org"

# Íslensk nafnagreining – kvenkyns endingar
KVENKYNS_ENDINGAR = [
    'dóttir', 'dís', 'ey', 'björg', 'björk', 'borg', 'brá', 'dóra',
    'fríður', 'gerður', 'heiður', 'hildur', 'laug', 'leif', 'ný',
    'rún', 'sól', 'unnur', 'veig', 'þóra', 'æsa', 'ósk', 'ía', 'a',
]

# Karlkyns endingar
KARLKYNS_ENDINGAR = [
    'son', 'ur', 'ar', 'ir', 'ór', 'úr', 'var', 'þór',
]

def greina_kyn(nafn):
    """Greinir kyn út frá nafni með íslenskri málfræði."""
    nafn = nafn.strip()
    # Athuga endingar
    for ending in KVENKYNS_ENDINGAR:
        if nafn.lower().endswith(ending.lower()):
            return 'kvk'
    for ending in KARLKYNS_ENDINGAR:
        if nafn.lower().endswith(ending.lower()):
            return 'kk'
    # Ef óvíst
    return None

def sækja_2020_töflu():
    """Sækir og greinir 2020 nefndartöflu af Wayback Machine."""
    url = "https://web.archive.org/web/20200115000000/https://www.stjornarradid.is/raduneyti/nefndir/"
    print(f"Sæki: {url}")
    r = requests.get(url, headers=HEADERS, timeout=60)
    if r.status_code != 200:
        print(f"Villa: HTTP {r.status_code}")
        return []
    
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    if not table:
        print("Engin tafla fannst!")
        return []
    
    rows = table.find_all("tr")
    nefndir = []
    
    for i, row in enumerate(rows[1:], 1):  # Sleppa haus
        cells = row.find_all(["td", "th"])
        if len(cells) >= 2:
            nafn = cells[0].get_text(strip=True)
            # Hreinsa HTML- rusl
            nafn = re.sub(r'<[^>]+>', '', nafn)
            nafn = re.sub(r'\s+', ' ', nafn).strip()
            
            raduneyti = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            tegund = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            
            if nafn and len(nafn) > 5:
                nefndir.append({
                    "nafn": nafn,
                    "raduneyti": raduneyti,
                    "tegund": tegund,
                    "ar": 2020,
                })
        
        # Hætta tímabundið eftir 20 til að sýna fram á virkni
        if i >= 20:
            break
    
    print(f"✅ Dregin út {len(nefndir)} nefndir úr 2020 töflu")
    return nefndir

if __name__ == "__main__":
    nefndir = sækja_2020_töflu()
    
    # Sýna fyrstu 5 og kynjagreiningu
    print("\nFyrstu 5 nefndir:")
    for n in nefndir[:5]:
        print(f"  • {n['nafn'][:80]}")
        print(f"    Ráðuneyti: {n['raduneyti']}")
        print(f"    Tegund: {n['tegund']}\n")
    
    # Vista
    with open("nefndir_2020.json", "w", encoding="utf-8") as f:
        json.dump(nefndir, f, ensure_ascii=False, indent=2)
    print(f"✅ Vistaðar {len(nefndir)} nefndir í nefndir_2020.json")
