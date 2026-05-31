# SPRINT — DISCOVERY: Forsíðu-refactor (Hönnuður)

**Höfundur:** Hönnuður (Claude, Sonnet 4.6) — framendi/útlit
**Staða:** Discovery → bíður Opus GREEN
**Dagsetning:** 31. maí 2026

## 1. Upphafsstaða

Forsíða úr interfaces/index.html. Núverandi: token-loginbox + hero + 4 tabs + trust-strip + footer.
Auth: OIDC í bakenda en EKKI notað í framenda.
Token-gate virkur: app_v3.js L28 + web_server.py L282. Síðan er LOKUÐ.

## 2. Staðfest villa (Android)
Loginbox-hnappur virkar ekki. Orsök: CSP blokkar inline onclick, fallback bindur við rangt id.

## 3. Scope
A: Vinstri stika — samþykkt
B: Hero-texti fjarlægður — samþykkt
C: Trust-strip færður — samþykkt
D: OIDC login-hnappur — Opus GREEN
E: Notandanafn/lykilorð — DEFERRAÐ

## 4. Opin ákvörðun: Token-veggurinn
(i) Halda token-vegg — status quo, lokuð síða
(ii) Fjarlægja fyrir opna beta — hááhætta, krefst

## 5. Hönnunarmat
Halda: trust-strip, BEM, aðgengi
Laga: token-loginbox lítur út sem dev-tól, tabs faldar, hero endurtekur

## 6. Næsta gate
Discovery → Opus GREEN → strategy doc → implementation
