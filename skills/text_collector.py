"""
text_collector.py — Mímir Skill v1.1
Sprint 7: Íslenskt textaefni → Mimir_Data_Lake
"""

import os, sys, json, time, re, requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "config" / ".env")
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

SOURCES = [
    {"name": "ruv",   "url": "https://www.ruv.is/frettir"},
    {"name": "mbl",   "url": "https://www.mbl.is/frettir/"},
    {"name": "visir", "url": "https://www.visir.is/"},
]

ICELANDIC_CHARS = set("áéíóúýðþæöÁÉÍÓÚÝÐÞÆÖ")

def fetch_page(url: str) -> str:
    try:
        resp = requests.get(f"https://r.jina.ai/{url}", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  ⚠️  {e}")
        return ""

def clean_line(line: str) -> str:
    line = re.sub(r'!\[.*?\]\(.*?\)', '', line)
    line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
    line = re.sub(r'https?://\S+', '', line)
    line = re.sub(r'^#+\s*', '', line)
    return line.strip()

def is_icelandic(text: str) -> bool:
    if len(text) < 20:
        return False
    ic_count = sum(1 for c in text if c in ICELANDIC_CHARS)
    return ic_count >= 2

def is_garbage(line: str) -> bool:
    garbage_patterns = [
        'vafrakök', 'cookie', 'javascript', 'function()',
        'eyJidWNrZXQi', 'localStorage', 'getElementById', 'addEventListener',
        'Hoppa í', 'Lesa meira', 'Deila', 'Prenta', 'Höfundur:', 'Mynd:', 'Ljósmynd'
    ]
    lower = line.lower()
    return any(p.lower() in lower for p in garbage_patterns)

def extract_articles(raw_text: str, source_url: str) -> list:
    articles = []
    lines = raw_text.split('\n')
    
    current_title = ""
    current_body = []
    
    for line in lines:
        line = clean_line(line)
        if not line or len(line) < 15:
            continue
        if is_garbage(line):
            continue
        if not is_icelandic(line):
            continue
            
        is_title = (
            20 <= len(line) <= 180 and
            line.count('.') <= 1 and
            not line.startswith('•') and
            any(c in line for c in ICELANDIC_CHARS)
        )
        
        if is_title and len(current_body) >= 2:
            body_text = " ".join(current_body)
            if len(body_text) > 80:
                articles.append({
                    "titill": current_title,
                    "texti": body_text,
                    "heimild": source_url
                })
            current_title = line
            current_body = []
        elif is_title and not current_title:
            current_title = line
        elif current_title and len(line) > 30:
            current_body.append(line)
    
    if current_title and len(" ".join(current_body)) > 80:
        articles.append({
            "titill": current_title,
            "texti": " ".join(current_body),
            "heimild": source_url
        })
    
    return articles

def save_batch(articles: list, source_name: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATA_DIR / f"{source_name}_{timestamp}.jsonl"
    written = 0
    with open(filename, "w", encoding="utf-8") as f:
        for a in articles:
            record = {
                "id": f"{source_name}_{written}_{timestamp}",
                "titill": a["titill"],
                "texti": a["texti"],
                "heimild": a["heimild"],
                "tungumál": "is",
                "dagsetning": datetime.now().isoformat(),
                "tegund": "frétt"
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
    print(f"  💾 {written} greinar → {filename.name}")
    return str(filename)

def collect_all():
    print("🇮🇸 Mímir Text Collector v1.1")
    print("=" * 45)
    total = 0
    for source in SOURCES:
        print(f"\n📡 {source['name']}: {source['url']}")
        raw = fetch_page(source["url"])
        if not raw:
            continue
        print(f"  ✅ {len(raw):,} stafir")
        articles = extract_articles(raw, source["url"])
        print(f"  📰 {len(articles)} greinar fundnar")
        if articles:
            save_batch(articles, source["name"])
            total += len(articles)
        time.sleep(2)
    print(f"\n{'='*45}")
    print(f"✅ Samtals: {total} greinar")

if __name__ == "__main__":
    collect_all()
