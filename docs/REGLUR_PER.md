# 📜 REGLUR_PER — Starfsreglur Yfirverkfræðings
# Dags: 28. apríl 2026 | Byggt á dýrkeyptri reynslu Sprint 71-72

## 1. TVEGGJA MANNA REGLAN
ALDREI senda Bash-skriftu eða flókinn kóða beint til Sigvalda án samþykkis Opus (Yfirarkitekt).
Þú skrifar → Opus rýnir → Sigvaldi keyrir.

## 2. BÖLVAÐIR PYTHON STRENGIR (\n & Escape)
JavaScript eða flókin rökfræði má ALDREI vera inline í Python strengjum (f-strengir).
Allt JS í hreinum `.js` skrám.
Lærdómur: 27. apríl 2026 — `\n` í Python heredoc breyttist í raunverulegt newline og frýs allt DOM.

## 3. FRAMENDINN FYRST
Þegar vefsíða frýs → Console (F12) → JavaScript villur áður en bakendi er skoðaður.

## 4. ÁVALLT .BAK AFRIT
`cp skra.py skra.py.bak` áður en nokkuð er breytt með sed/cat/Python.
Eitt skref í einu. Prófa á milli.
