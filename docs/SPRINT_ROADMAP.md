# Alvitur Sprint Vegvísir — 13. maí 2026

## Yfirlit

| Sprint | Staða | Tími | Markmið |
|--------|-------|------|---------|
| 80c v2 RC1 | ✅ LOKAÐ | 11. maí | Multi-source RRF web search |
| 80c v2 RC2 | ⏳ Frestað | 1–2 klst | Wayback söguleg gögn + RRF lagfæring |
| 81 | ⏳ Næst | 5 dagar | Resilience Foundation |
| 82 | ⏳ | 5 dagar | Agent Visibility + Source Trust Layer |
| 83 | ⏳ | 4 dagar | Performance & Streaming |
| 84 | ⏳ | 7 dagar | User State & Memory |
| 85 | ⏳ | 5 dagar | Document Intelligence Depth |
| 86+ | ⏳ | TBD | Multi-agent self-learning core |

## Lærdómar

| # | Lærdómur |
|---|----------|
| 60 | Aldrei segja verk „lokið" án empirical verification |
| 78 | Engin Python strengja-parsing í bash heredoc |
| 79 | Dev/Prod parallel deployment |
| 85 | Source diversity > source quality (Mojeek index gap) |
| 86 | Sönnunarbyrgði liggur hjá kóðanum, ekki LLM |
| 87 | Prompt binding (temperature 0.3 + HEIMILDIR merkingar) |
| 88 | LLM án empirical stuðnings skáldar trúverðugar staðreyndir |
| 89 | Stem-matching á stjornarradid_source.py var regression, ekki fix |

## Stöðugar merkingar

- Git tag: `v80c-v2-rc1` — Multi-source RRF release candidate 1
- API: Kristrún Frostadóttir svar virkar
- Heimildagátt: Óvirk, færð til Sprint 82
- Mojeek DPA: Frágengið
- SOVEREIGNTY_AUDIT.md: Uppfært með Mojeek

## Næstu skref

- 13. maí: Klára Postmortem + Roadmap + SOVEREIGNTY_AUDIT
- 14. maí: Byrja Sprint 81 (systemd, cache busting)
- 15. maí og áfram: Halda áfram með Resilience Foundation
