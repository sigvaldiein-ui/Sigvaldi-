#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent_core_v5.py — Mímir Supervisor / Router
=============================================
Sprint 15.4 | Smíðað af Per (Yfirverkfræðingur)
Samþykkt af Aðal Arkitekt (Valkostur C)

HLUTVERK:
  Fyrsti Supervisor Agent — flokkar beiðnir og beinir á rétt verkfæri.
  Leggur grunn að Multi-Agent framtíðinni (LangGraph).

ARKITEKTÚR:
  ┌─────────────────────────────┐
  │   MimirCoreV5 (Supervisor)  │
  │   - Tekur við skilaboðum    │
  │   - Flokkar: SEARCH / CHAT  │
  │   - Beinir á rétt verkfæri  │
  └──────────┬──────────────────┘
             │
    ┌────────┴────────┐
    ↓                 ↓
  SEARCH            CHAT/RAG
  DeepHunter        agent_core_v4
  (investigate)     (analyze_query / ask_llm)

REGLUR:
  - agent_core_v4.py er ÓSNERTANLEG — v5 importar hana, breytir henni ekki
  - Allar gáfur eru í kjarnanum (Headless AI), ekki í viðmóti
  - Viðmót (Telegram, Web) kallar á process_message() og fær svar

NOTKUN:
  from core.agent_core_v5 import MimirCoreV5

  mimir = MimirCoreV5()
  svar = mimir.process_message("Hvað eru nýjustu stýrivextir?", user_id=12345)
  print(svar)
"""

import os
import sys
import time

# Tryggja rétta slóð
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

# Importa v4 kjarna (ÓSNERTANLEGAN)
from core.agent_core_v4 import ask_llm, analyze_query

# Importa Deep Hunter
from skills.deep_hunter import DeepHunter


# ============================================================
# FLOKKUNAR PROMPT — ákveður hvort leita þarf á netinu
# ============================================================

FLOKKUN_PROMPT = (
    "Þú ert flokkunarkerfi. Þitt EINA verkefni er að ákveða hvort spurning "
    "krefst þess að leitað sé á internetinu.\n\n"
    "Svaraðu AÐEINS einu orði: JÁ eða NEI.\n\n"
    "JÁ ef spurningin:\n"
    "- Spyr um nýlega atburði, fréttir, eða hvað gerðist nýlega\n"
    "- Krefst rauntíma gagna (verð, gengi, tölur, stöðu)\n"
    "- Spyr um markaðsupplýsingar, hlutabréf, stýrivexti\n"
    "- Vísar í nýleg lög, reglugerðir, eða opinberar ákvarðanir\n"
    "- Notar orð eins og 'nýjast', 'síðast', 'í dag', 'nýlega', 'núna'\n\n"
    "NEI ef spurningin:\n"
    "- Er almenn þekkingarspurning sem breytist ekki\n"
    "- Biður um ráðgjöf, útskýringu eða skoðun\n"
    "- Er persónuleg (nafn, minni, samtal)\n"
    "- Er um sögulega atburði sem þegar eru þekktir\n\n"
    "Spurning: {spurning}\n"
    "Svar (JÁ eða NEI):"
)


class MimirCoreV5:
    """
    Mímir Supervisor / Router — fyrsti Multi-Agent grunnurinn.

    Flokkar beiðnir og beinir á rétt verkfæri:
      - SEARCH → DeepHunter (rauntímaleit á netinu)
      - CHAT   → agent_core_v4 (spjall, RAG, almenn þekking)
    """

    def __init__(self):
        """Frumstilli Supervisor með Deep Hunter."""
        self.hunter = DeepHunter(
            max_results=3,
            max_chars_per_page=3000,
            timeout=25,
        )
        print("🧠 MimirCoreV5 (Supervisor) frumstilltur")
        print("   └── DeepHunter: tilbúinn")
        print("   └── agent_core_v4: tilbúinn")

    # ----------------------------------------------------------
    # FLOKKUNARFALL — "Krefst þetta rauntímaleit?"
    # ----------------------------------------------------------

    def _flokka(self, spurning: str) -> str:
        """
        Notar ofurhratt LLM kall til að flokka: JÁ (SEARCH) eða NEI (CHAT).
        Skilar 'SEARCH' eða 'CHAT'.
        """
        prompt = FLOKKUN_PROMPT.format(spurning=spurning)
        try:
            svar = ask_llm(
                "Svaraðu AÐEINS: JÁ eða NEI",
                prompt,
                temp=0.0,
            )
            svar_hreint = svar.strip().upper()

            if "JÁ" in svar_hreint or "JA" in svar_hreint or "YES" in svar_hreint:
                return "SEARCH"
            else:
                return "CHAT"
        except Exception as e:
            print(f"⚠️  Flokkunarvilla: {e} — nota CHAT sem sjálfgefið")
            return "CHAT"

    # ----------------------------------------------------------
    # AÐALFALL — process_message()
    # ----------------------------------------------------------

    def process_message(self, message: str, user_id: int = 0) -> str:
        """
        Aðalfallið sem viðmót (Telegram/Web) kallar á.

        Flæðið:
          1. Flokka: SEARCH eða CHAT
          2. Ef SEARCH → Deep Hunter investigate
          3. Ef CHAT → v4 analyze_query eða ask_llm

        Parametrar:
          message  — Skilaboð frá notanda
          user_id  — Notandaauðkenni (chat_id)

        Skilar: Strengur með svari Mímis
        """
        timi_byrjun = time.time()

        # --- Skref 1: Flokkun ---
        flokkun = self._flokka(message)
        print(f"🧠 [V5 Supervisor] Flokkun: {flokkun} | Spurning: {message[:60]}...")

        # --- Skref 2: Beina á rétt verkfæri ---
        if flokkun == "SEARCH":
            # Deep Hunter — rauntímaleit
            print("🕵️ [V5] → Deep Hunter (investigate)")
            try:
                nidurstada = self.hunter.investigate(message)

                # Ef Deep Hunter skilar niðurstöðum, blanda við Mímir persónuleika
                if nidurstada and "🛑" not in nidurstada:
                    # Láta Mímir draga saman og svara á íslensku
                    samantekt_prompt = (
                        "Þú ert Mímir, íslenskur AI rannsóknarfulltrúi. "
                        "Hér eru niðurstöður úr rauntímaleit á netinu. "
                        "Dragðu saman helstu atriði á fágaðri íslensku. "
                        "Hafðu svarið hnitmiðað og faglegt. "
                        "Viðhaltu heimildum (URL) neðst í svarinu."
                    )
                    svar = ask_llm(samantekt_prompt, nidurstada, temp=0.3)

                    if "VILLA" not in svar:
                        timi = time.time() - timi_byrjun
                        print(f"✅ [V5] Svar tilbúið ({timi:.1f} sek)")
                        return svar

                # Fallback — skila hráum niðurstöðum ef samantekt mistókst
                return nidurstada

            except Exception as e:
                print(f"⚠️  [V5] Deep Hunter villa: {e}")
                # Falla til baka á v4
                print("🔄 [V5] Fell til baka á v4 analyze_query")
                return analyze_query(message)

        else:
            # CHAT — v4 kjarni
            print("💬 [V5] → agent_core_v4 (analyze_query)")
            try:
                return analyze_query(message)
            except Exception as e:
                print(f"⚠️  [V5] v4 villa: {e}")
                return f"Villa í Mímir kjarna: {e}"


# ============================================================
# CLI — Sjálfstæð prófun
# ============================================================

if __name__ == "__main__":
    import sys as _sys

    mimir = MimirCoreV5()

    if len(_sys.argv) > 1:
        spurning = " ".join(_sys.argv[1:])
    else:
        spurning = "Hvaða stýrivextir eru á Íslandi núna?"

    print(f"\n{'='*60}")
    print(f"📩 Spurning: {spurning}")
    print(f"{'='*60}\n")

    svar = mimir.process_message(spurning, user_id=8547098998)

    print(f"\n{'='*60}")
    print(f"🤖 SVAR MÍMIS:")
    print(f"{'='*60}")
    print(svar)
