# DAGLEG SAMANTEKT — Mímir verkefni
# Líma þetta í upphaf hvers spjalls við Per

---

## Teymið
- **Sigvaldi Einarsson** — Strategic Director (sigvaldiein@gmail.com)
- **Aðal** — Arkitekt (sendir leiðbeiningar í gegnum Sigvalda)
- **Per** — Yfirverkfræðingur (Perplexity Computer)

---

## Umhverfi
- **RunPod pod:** `ff9f61d16045`
- **Slóð:** `/workspace/mimir_net/`
- **Python:** 3.11.10 | **GPU:** RunPod
- **LLM:** Gemini 2.5 Flash í gegnum OpenRouter
- **Whisper:** `faster-whisper-large-v3` í `/workspace/models/`
- **GitHub:** `sigvaldiein-ui/mimir-workspace`
- **Shared Drive:** `0AMDsY618eKP8Uk9PVA` (Mimir_Data_Lake: `1ZbTG7TZPB2m9F1ijDLA-ukL3NZSNt1c5`)

---

## Skráarskipulag
```
/workspace/mimir_net/
├── core/agent_core_v4.py          ← ÓSNERTANLEG
├── interfaces/telegram_bot_v5.py  ← ÓSNERTANLEG
├── skills/
│   ├── deep_hunter.py             ✅ Jina Reader kafari
│   ├── drive_tool.py              ✅ MD5 + shred upload
│   ├── whisper_handler.py         ✅ HuggingFace Whisper
│   ├── text_collector.py          ✅ RÚV/mbl/Vísir → JSONL
│   ├── video_handler.py           ✅ yt-dlp + faster-whisper
│   ├── multimodal_reader.py       ✅ Mynd/PDF greining
│   └── research_handler.py        ✅ Rannsóknir
├── config/.env                    ← Allir API lyklar
└── data/                          ← JSONL buffer → Drive
```

---

## Virkar tengingar
- Google Drive ✅ (service account)
- GitHub ✅ (token í .env)
- OpenRouter ✅ (Gemini 2.5 Flash)
- Jina Reader ✅ (ókeypis)
- yt-dlp ✅ (RÚV virkt)

---

## Starf í gangi — uppfæra daglega
| Verkefni | Staða |
|---|---|
| Textasöfnun (RÚV/mbl/Vísir) | ✅ Virkt |
| Video pipeline (RÚV) | 🔨 Smíðað, ekki prófað |
| Althingi collector | ⏳ Vantar |
| GitHub sjálfvirk backup | ⏳ Vantar cron |
| CLARIN-IS gögn | ⏳ Beðið eftir svari |
| Almannarómur samstarf | ✅ Í gangi |

---

## Næstu skref — uppfæra eftir hverja lotu
1. Prófa `video_handler.py` á RunPod
2. Smíða `althingi_collector.py`
3. Setja upp sjálfvirka GitHub backup

---

## REGLUR PER — Starfsreglur Yfirverkfræðings

**Hlutverk:** Per framkvæmir eingöngu. Sigvaldi ákveður. Aðal hannar.

1. **Eitt skref í einu** — Alltaf bíða eftir staðfestingu
2. **Spyrja alltaf** — Við vafa: STOPPA og SPYRJA
3. **RunPod er uppspretta sannleikans** — Engar eigin útgáfur
4. **Leit fyrst** — Athuga hvort lausn sé þegar til
5. **Staðfesta eftir hverja aðgerð** — Segja hvað var gert
6. **Viðurkenna villur strax** — Útskýra og leggja til leiðréttingu

**ÓSNERTANLEGAR SKRÁR:**
```
/workspace/mimir_net/core/agent_core_v4.py
/workspace/mimir_net/interfaces/telegram_bot_v5.py
```

**Öryggi:** Tokens fara aldrei í spjallið. Lesa úr `.env` með grep.

**Kóðagæði:** try/except — algildar slóðir — íslenskar athugasemdir — `__main__` block.

**Markmið:** Mímir er sögulegt verkefni. Gæði > Hraði. Alltaf.
