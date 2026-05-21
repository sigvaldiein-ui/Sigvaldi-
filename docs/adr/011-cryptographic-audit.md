# 🏛️ ADR-011: PERSISTENT CRYPTOGRAPHIC AUDIT CHAIN

**Staða:** Innleitt og sannprófað (Sprettir 104 & 97.7)
**Markmið:** Að tryggja órækni logga og vörn gegn minnistapi við endurræsingu.

* **Samhengi:** Upphafleg in-memory útfærsla á SHA-256 keðjunni byrjaði upp á nýtt (með núll-hash) við hverja endurræsingu þjónsins. Þetta eyðilagði órækni logganna og féll á ISO-27001 kröfum.
* **Ákvörðun:** 1. Stofna töfluna `audit_chain` í SQLite (`state_store.db`) sem geymir tímastimpil, `jti`, `user_sub`, `tool_name`, `action`, `prev_hash`, og `this_hash`.
    2. Við ræsingu (startup) keyrir kerfið `load_last_hash` sem tryggir að dulkóðunarkeðjan haldi áfram nákvæmlega þar sem frá var horfið.
* **Afleiðing:** Algjörlega órækir og restart-safe stjórnsýsluloggar. Ekki einu sinni kerfisstjóri getur átt við gögnin án þess að brjóta keðjuna.
