#!/usr/bin/env python3
"""Endurkvæmur trjáskanni fyrir stjornarradid.is/raduneyti/nefndir/"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path
import html as html_module

BASE = "https://www.stjornarradid.is"
ROOT_URL = f"{BASE}/raduneyti/nefndir/"
HEADERS = {
    "User-Agent": "Alvitur.is/1.0 sovereign-research bot — info@alvitur.is",
    "Accept-Language": "is, en;q=0.5",
}
RATE_LIMIT_SEC = 1.5
TREE_FILE = "tree.json"
LEAVES_FILE = "leaves.json"
CHECKPOINT = "crawl_checkpoint.json"


def fetch(url, retries=3):
    """GET síðu með kurteislegu hraðatakmarki og endurtekningu."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            time.sleep(RATE_LIMIT_SEC)
            return r.text
        except Exception as e:
            print(f"  Endurtek {attempt+1}: {e}")
            time.sleep(5 * (attempt + 1))
    return None


def parse_node(html_text):
    """Greinir stækkunarhlekki af hnútasíðu."""
    if not html_text:
        return []
    soup = BeautifulSoup(html_text, "html.parser")
    links = []
    
    for a in soup.find_all("a", class_="expand-link"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        text = html_module.unescape(text)
        
        is_inner = text.startswith("Next level for")
        clean_text = re.sub(r"^Next level for\s+", "", text)
        
        full_url = href if href.startswith("http") else BASE + href
        full_url = full_url.replace("&amp;", "&")
        
        links.append({
            "url": full_url,
            "text": clean_text,
            "is_inner": is_inner,
        })
    
    return links


def crawl(url, depth=0, max_depth=6, visited=None):
    """Endurkvæmur skanni, skilar trjágrein."""
    if visited is None:
        visited = set()
    
    if url in visited:
        return None
    visited.add(url)
    
    if depth > max_depth:
        print(f"  Hámarksdýpt við {url}")
        return None
    
    indent = "  " * depth
    print(f"{indent}[{depth}] Sæki...")
    
    html_text = fetch(url)
    if not html_text:
        return {"url": url, "error": "sókn mistókst"}
    
    children_links = parse_node(html_text)
    
    node = {
        "url": url,
        "depth": depth,
        "children": [],
        "leaf_links": [],
    }
    
    for link in children_links:
        if link["is_inner"]:
            print(f"{indent}  ↳ Innri: {link['text']}")
            child = crawl(link["url"], depth + 1, max_depth, visited)
            if child:
                child["category"] = link["text"]
                node["children"].append(child)
        else:
            print(f"{indent}  ★ LAUF: {link['text']}")
            node["leaf_links"].append({
                "name": link["text"],
                "url": link["url"],
            })
    
    # Vista áfangaskrá eftir hvern hnút
    Path(CHECKPOINT).write_text(
        json.dumps({"visited": list(visited), "last_url": url}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    return node


def collect_leaves(tree, leaves=None):
    """Gengur um tré og safnar öllum laufum."""
    if leaves is None:
        leaves = []
    if not tree:
        return leaves
    leaves.extend(tree.get("leaf_links", []))
    for child in tree.get("children", []):
        collect_leaves(child, leaves)
    return leaves


if __name__ == "__main__":
    print("=" * 50)
    print("  TRJÁSKAN — ræsi")
    print("=" * 50)
    
    tree = crawl(ROOT_URL)
    
    Path(TREE_FILE).write_text(
        json.dumps(tree, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    leaves = collect_leaves(tree)
    Path(LEAVES_FILE).write_text(
        json.dumps(leaves, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"\n✅ Tré: {TREE_FILE}")
    print(f"✅ Lauf: {LEAVES_FILE} ({len(leaves)} færslur)")
