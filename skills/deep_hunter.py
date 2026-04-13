#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deep_hunter.py — Mímir Rannsóknar-Kafari (Deep Hunter)
======================================================
Sprint 15.4 | Smíðað af Per (Yfirverkfræðingur)

Gefur Mímir getu til að leita á netinu í rauntíma,
lesa vefsíður og setja saman svör með heimildum.

ÞRJÚ SKREFA LÓGÍK:
  1. Breiðleit (The Radar)   — DuckDuckGo leit, top 3 URL
  2. Djúplestur (The Deep Dive) — Jina Reader, hreinn Markdown af hverri síðu
  3. Gullvaskur (The Synthesis) — Samantekt með heimildum

AFTURVIRKT SAMHÆFT:
  scrape_url() fallið er óbreytt — agent_core_v4.py notar það.
  DeepHunter klassinn er nýr viðbót.

UPPSETNING:
  pip install duckduckgo-search httpx requests tavily-python

BREYTINGAR V2 (Sprint 16):
  - Tavily sem aðalleit (ferskari, hraðari, LLM-tilbúin)
  - DuckDuckGo sem fallback ef Tavily API vantar
  - TAVILY_API_KEY í .env eða umhverfisbreytu
"""

import os
import time
import requests

# ============================================================
# UPPRUNALEGT FALL — ALDREI BREYTA (agent_core_v4.py notar)
# ============================================================

def scrape_url(url: str) -> str:
    """
    Kafarinn v5.0 (Proxy-Augu): Notar Jina Reader til að brjótast framhjá
    Cloudflare bot-vörnum, rendera JavaScript og sækja faldar töflur.
    Skilar hreinum Markdown texta.
    """
    print(f"🕵️‍♂️ [Proxy-Augu] Kafa í gegnum Jina Reader: {url}")

    jina_url = f"https://r.jina.ai/{url}"
    headers = {"Accept": "text/plain"}

    try:
        resp = requests.get(jina_url, headers=headers, timeout=25)
        resp.raise_for_status()

        texti = resp.text
        if len(texti) < 150 or "Title: " not in texti:
            return "❌ VILLA: Proxy-Augu skiluðu of litlum eða engum gögnum (Bot-vörn)."

        return texti[:30000]

    except requests.exceptions.Timeout:
        return f"❌ VILLA: Proxy-Augu tímuðu út á {url} (Síðan of þung)."
    except Exception as e:
        return f"❌ VILLA við Proxy-skröpun: {e}"


# ============================================================
# DEEP HUNTER KLASSI — NÝR (Sprint 15.4)
# ============================================================

class DeepHunter:
    """
    Rannsóknar-Kafari sem leitar á netinu, les vefsíður og
    setur saman svör með heimildum.

    Notkun:
        hunter = DeepHunter()
        nidurstada = hunter.investigate("Hver er nýjasta stýrivaxtaákvörðun Seðlabankans?")
        print(nidurstada)
    """

    def __init__(self, max_results=3, max_chars_per_page=3000, timeout=25):
        """
        Stillingar:
          max_results       — Fjöldi leitarniðurstaðna (sjálfgefið 3)
          max_chars_per_page — Hámark stafir per síðu (til að sprengja ekki context)
          timeout           — Timeout á HTTP beiðnir í sekúndum
        """
        self.max_results = max_results
        self.max_chars_per_page = max_chars_per_page
        self.timeout = timeout
        self.tavily_key = os.environ.get("TAVILY_API_KEY", "")
        
        if self.tavily_key:
            print("🔑 [DeepHunter] Tavily API lykill fundinn — nota Tavily leit")
        else:
            print("⚠️  [DeepHunter] Enginn Tavily lykill — nota DuckDuckGo (stale results)")

    # ----------------------------------------------------------
    # SKREF 1: Breiðleit (The Radar)
    # ----------------------------------------------------------

    def search(self, query: str) -> list:
        """
        Leitar á netinu og skilar lista af dict:
        [{"title": "...", "url": "...", "snippet": "...", "content": "..."}, ...]

        Notar Tavily ef API lykill er til, annars DuckDuckGo sem fallback.
        """
        if self.tavily_key:
            return self._search_tavily(query)
        else:
            return self._search_ddg(query)

    def _search_tavily(self, query: str) -> list:
        """Tavily leit — fersk, hröð, LLM-tilbúin."""
        print(f"🔍 [Tavily] Leita: '{query}' (max {self.max_results})")

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.tavily_key)

            # Nota advanced leit fyrir ferskustu niðurstöður
            svar = client.search(
                query=query,
                max_results=self.max_results,
                search_depth="advanced",
                include_raw_content=True,
            )

            slodir = []
            for r in svar.get("results", []):
                slodir.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "content": r.get("raw_content", "")[:self.max_chars_per_page] if r.get("raw_content") else "",
                })

            print(f"🔍 [Tavily] Fann {len(slodir)} niðurstöður")
            for i, s in enumerate(slodir, 1):
                print(f"   {i}. {s['title'][:60]} — {s['url'][:80]}")

            return slodir

        except Exception as e:
            print(f"⚠️  [Tavily] Villa: {e} — reyni DuckDuckGo")
            return self._search_ddg(query)

    def _search_ddg(self, query: str) -> list:
        """DuckDuckGo fallback — ókeypis en stale."""
        print(f"📡 [DuckDuckGo] Leita: '{query}' (max {self.max_results})")

        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                print("❌ ddgs pakki vantar — pip install ddgs")
                return []

        try:
            with DDGS() as ddgs:
                nidurstodur = list(ddgs.text(
                    query,
                    max_results=self.max_results,
                    region="is-is",
                ))

            slodir = []
            for r in nidurstodur:
                slodir.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                    "content": "",
                })

            print(f"📡 [DuckDuckGo] Fann {len(slodir)} niðurstöður")
            for i, s in enumerate(slodir, 1):
                print(f"   {i}. {s['title'][:60]} — {s['url'][:80]}")

            return slodir

        except Exception as e:
            print(f"❌ [DuckDuckGo] Villa: {e}")
            return []

    # ----------------------------------------------------------
    # SKREF 2: Djúplestur (The Deep Dive)
    # ----------------------------------------------------------

    def read_page(self, url: str) -> str:
        """
        Les vefsíðu í gegnum Jina Reader (r.jina.ai).
        Skilar hreinum Markdown texta, klipptum niður.
        """
        print(f"🔍 [Djúplestur] Les: {url[:80]}")

        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "Accept": "text/plain",
            "User-Agent": "Mimir-DeepHunter/1.0",
        }

        try:
            # Nota httpx ef til, annars requests
            try:
                import httpx
                resp = httpx.get(jina_url, headers=headers, timeout=self.timeout, follow_redirects=True)
                resp.raise_for_status()
                texti = resp.text
            except ImportError:
                resp = requests.get(jina_url, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                texti = resp.text

            # Athuga hvort við fengum raunverulegt efni
            if len(texti) < 100:
                print(f"⚠️  [Djúplestur] Of lítið efni ({len(texti)} stafir)")
                return ""

            # Klippa niður
            klippt = texti[:self.max_chars_per_page]
            print(f"✅ [Djúplestur] {len(klippt)} stafir lesnir")
            return klippt

        except Exception as e:
            print(f"⚠️  [Djúplestur] Villa á {url[:50]}: {e}")
            return ""

    # ----------------------------------------------------------
    # SKREF 3: Gullvaskur (The Synthesis)
    # ----------------------------------------------------------

    def investigate(self, query: str) -> str:
        """
        Aðalfallið — sameinar leit, lestur og samantekt.

        Flæðið:
          1. DuckDuckGo leit → top 3 URL
          2. Jina Reader les hverja síðu
          3. Setur saman niðurstöður með heimildum

        Skilar strengi með samantekt og heimildum neðst.
        """
        print(f"\n{'='*60}")
        print(f"🕵️ DEEP HUNTER — Rannsókn hafin")
        print(f"   Spurning: {query}")
        print(f"{'='*60}\n")

        timi_byrjun = time.time()

        # --- Skref 1: Leit ---
        slodir = self.search(query)
        if not slodir:
            return (
                "🛑 **Leit skilaði engum niðurstöðum.**\n\n"
                f"Leitarorð: {query}\n"
                "Athugið: Leitarþjónusta gæti verið tímabundið óaðgengileg."
            )

        # --- Skref 2: Djúplestur ---
        print()
        heimildir = []
        textar = []

        for i, slod in enumerate(slodir, 1):
            url = slod.get("url", "")
            title = slod.get("title", f"Heimild {i}")
            if not url:
                continue

            # Tavily skilar content beint — sleppa Jina Reader ef til
            texti = slod.get("content", "")
            if not texti:
                texti = self.read_page(url)
                time.sleep(0.5)  # Kurteisi milli beiðna

            if texti:
                textar.append({
                    "nr": i,
                    "title": title,
                    "url": url,
                    "content": texti,
                })
                heimildir.append(f"[{i}] {title}\n    {url}")

        if not textar:
            return (
                "🛑 **Fann síður en gat ekki lesið þær.**\n\n"
                f"Leitarorð: {query}\n"
                "Slóðir sem reynt var:\n" +
                "\n".join(f"  • {s['url']}" for s in slodir)
            )

        # --- Skref 3: Samantekt ---
        print(f"\n📝 [Gullvaskur] Set saman niðurstöður úr {len(textar)} heimildum...")

        # Búa til samantekt — texti úr öllum síðum með heimildum
        samantekt_hlutar = []
        samantekt_hlutar.append(f"🔎 **Rannsókn: {query}**\n")

        for t in textar:
            # Taka fyrstu 800 stafi úr hverri heimild
            stutt = t["content"][:800].strip()
            # Hreinsa rusl (Title: línur frá Jina)
            linur = stutt.split("\n")
            hreinsad = []
            for lina in linur:
                lina = lina.strip()
                if not lina:
                    continue
                if lina.startswith("Title:") or lina.startswith("URL Source:"):
                    continue
                hreinsad.append(lina)
            hreint = "\n".join(hreinsad[:10])  # Hámark 10 línur per heimild

            samantekt_hlutar.append(f"**[{t['nr']}] {t['title']}**")
            samantekt_hlutar.append(hreint)
            samantekt_hlutar.append("")

        # Heimildalisti neðst
        samantekt_hlutar.append("---")
        samantekt_hlutar.append("📚 **Heimildir:**")
        for h in heimildir:
            samantekt_hlutar.append(f"  {h}")

        timi_lok = time.time()
        samantekt_hlutar.append(f"\n⏱️ Rannsókn tók {timi_lok - timi_byrjun:.1f} sek.")

        nidurstada = "\n".join(samantekt_hlutar)

        print(f"\n✅ [Gullvaskur] Rannsókn lokið ({timi_lok - timi_byrjun:.1f} sek)")
        print(f"{'='*60}\n")

        return nidurstada


# ============================================================
# CLI — Sjálfstæð prófun
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        spurning = " ".join(sys.argv[1:])
    else:
        spurning = "Hvað er nýtt í stjórnarsáttmála ríkisstjórnar Íslands?"

    hunter = DeepHunter()
    nidurstada = hunter.investigate(spurning)
    print("\n" + "=" * 60)
    print("NIÐURSTAÐA:")
    print("=" * 60)
    print(nidurstada)
