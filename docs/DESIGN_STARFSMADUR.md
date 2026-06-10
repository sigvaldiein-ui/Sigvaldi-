# DESIGN_STARFSMADUR — Sjálfstæði stafræni starfsmaðurinn

**Frá:** Opus 4.8 (gatekeeper / strategisti)
**Til:** Sigvaldi (CTO/HITL), Per (bakendi), Hönnuður (framendi)
**Staða:** DESIGN — GREEN-að af CTO 10. júní 2026
**Byggir á:** GATE_STARFSMADUR_OG_VITI3.md (GREEN)

## 1. Kjarnahugmynd
Starfsmaðurinn er framkvæmdadeildin. Hann tekur verk + viðhengi, gerir plan, framkvæmir örugg skref sjálfur, og setur aðgerðir með afleiðingum í Samþykktir-biðröðina.

**Lykilregla:** Starfsmaðurinn leitar EKKI sjálfur. Hann kallar í Vitann. Ein hurð út = ein PII-gátt.

## 2. Geta í þremur þrepum
| Þrep | Lýsing | Dæmi |
|------|--------|------|
| Örugg | Sjálfvirk innan autonomy-dial | Lesa, greina, skrifa drög, kóða, töflur |
| Egress | Krefst samþykkis | Senda póst/skjöl fyrir hönd notanda |
| Auðkennt | Samþykki + sér-auth | Ísland.is og opinber kerfi |

## 3. Viðhengi — notandinn velur vinnslustað
- Trúnaðarskjal → Hvelfingin (RAM, sealed, ekkert út)
- Almennt skjal → Vitinn/Starfsmaður (má nýta vef/Stórmeistara)

## 4. Tool registry — öryggislíkanið
| Áhættuþrep | Stig | Regla |
|------------|------|-------|
| Öruggt | 0 | Sjálfvirkt innan dial |
| Egress | 1 | PII Sentry skylda |
| Auðkennt | 2 | Sér-auth per notanda |
| Stone-floor | 3 | ALLTAF í biðröð, aldrei sjálfvirkt |

**Stone-floor:** peningar, eyðing gagna, réttindabreytingar, undirritun.

## 5. Samþykktir-biðröð
- Viðvarandi, ekki RAM
- **ALDREI geymir trúnaðargögn** — aðeins sanitized forskoðun + tilvísun
- Per notanda, með autonomy-dial

## 6. Fasar og gáttir
| Fasi | Verk | Gátt |
|------|------|------|
| F-STARF-0 | Discovery: /api/analyze-document | Opus GREEN |
| F-STARF-1 | Agent-loop + örugg tól | Opus GREEN |
| F-STARF-2 | Samþykktir-biðröð + autonomy-dial | Opus GREEN |
| F-STARF-3 | Egress-tól (háð F1) | Opus GREEN |
| F-STARF-4 | Auðkennd tól (Ísland.is) | Opus GREEN |
| F-STARF-5 | Kill-switch + red-team | Opus GREEN |

## 7. Acceptance
- Örugg tól → ekkert fer út (núll útumferð)
- Hvert egress-tól → PII-scrub fail-closed + consent + audit
- Samþykktir-biðröð → aldrei Hvelfingar-gögn
- Kill-switch → stöðvar alla umferð
