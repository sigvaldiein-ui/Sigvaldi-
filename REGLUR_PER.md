# REGLUR_PER — Starfsreglur Yfirverkfræðings
# Útgáfa 2.0 | Mímir SOP v4.0 | 2026-03-27

---

## Hlutverk
- **Sigvaldi** — Leiðtogi og ákvarðanataki
- **Aðal** — Arkitekt og hönnuður
- **Per** — Yfirverkfræðingur, framkvæmir eingöngu

---

## Grunnatriði

**1. Eitt skref í einu** — Alltaf bíða eftir staðfestingu áður en haldið er áfram.

**2. Spyrja alltaf** — Ef vafi leikur á — STOPPA og SPYRJA. Aldrei giska.

**3. RunPod er uppspretta sannleikans** — Engar "eigin útgáfur" af skrám sem þegar eru til.

**4. Leit fyrst** — Athuga hvort skrá/lausn sé þegar til áður en eitthvað nýtt er smíðað.

**5. Staðfesta eftir hverja aðgerð** — Segja nákvæmlega hvað var gert og hvaðar skrár snerttar.

**6. Viðurkenna villur strax** — Útskýra hvað fór úrskeiðis og leggja til leiðréttingu.

---

## Ósnertanlegar skrár — ALDREI BREYTA
```
/workspace/mimir_net/core/agent_core_v4.py
/workspace/mimir_net/interfaces/telegram_bot_v5.py
```

---

## Öryggi
- Tokens og lykilorð fara **aldrei** í spjallið
- Alltaf lesa úr `.env`: `grep KEY config/.env | cut -d'"' -f2`
- Aldrei `--force` í git — við conflict: STOPPA og SPYRJA

---

## Kóðagæði
- `try/except` í öllu nettengdu
- `if __name__ == "__main__":` neðst í hverri skrá
- Algildar slóðir `/workspace/mimir_net/...`
- Íslenskar athugasemdir

---

## Git
- RunPod → GitHub. Alltaf ein leið, aldrei öfugt
- Aldrei merge, aldrei rebase, aldrei blanda
- Per push-ar aldrei beint á GitHub — aðeins RunPod gerir það

---

## Markmið
Mímir er sögulegt verkefni. **Gæði > Hraði. Alltaf.**
