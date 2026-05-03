# Allar Reglur Alvitur.is

## Verklagsreglur
1. Tveggja manna — Per rýnir, Sigvaldi keyrir
2. Bölvaðir Python strengir — ekkert JS inline
3. Framendinn fyrst — Console áður en bakendi
4. Git-skjöldurinn — `.bak` + commit + push eftir hvern áfanga
5. Hámark 150-200 línur á .py skrá
6. Skoða söguskrár áður en breytt er
7. Aldrei breyta út af verkáætlun án samþykkis Aðals
8. Discovery only í Fasa 0
9. Aldrei sjálf-GREEN — krefst empirical sönnunar
10. httpOnly cookie — engin sessionStorage tokens
11. Vanilla HTML/CSS/JS — ekkert framework
12. ALDREI keyra ETL í main FastAPI process
13. Skjaldbökutempó — eitt skref, ein skrá

## Per (DeepSeek V5) Strangar Vinnureglur
| # | Regla |
|---|-------|
| P1 | Engin inline Python í bash heredoc |
| P2 | Read-before-write |
| P3 | Empirical diagnosis fyrir workaround |
| P4 | CLI args staðfestar áður en skipun |
| P5 | Checkpoint + idempotent insert |
| P6 | NFC + íslensk regex pattern |
| P7 | Aldrei snerta production |
| P8 | Eitt skref per bash blokk |
| P9 | Aldrei sjálf-GREEN |
| P10 | Max 2 iterations per gate |

---

## Athugasemd um uppruna reglnanna

Margar þessara reglna eima niður tugi eldri lærdóma frá Hyper-Sprint-tímabilinu (apríl 2026). Nánar tiltekið:
- Regla 9 (Aldrei sjálf-GREEN) → kemur úr Lærdómur #60
- Regla 6 (Skoða söguskrár) → kemur úr Lærdómur #7, #8, #12
- Regla 13 (Skjaldbökutempó) → kemur úr Lærdómur #9, #10, #11
- Per reglur P2, P3, P5 → koma úr Lærdómur #13, #14, #15

