# 🏛️ ADR-016: KEK & DEK HJÚPDULKÓÐUN (ENVELOPE ENCRYPTION)

**Staða:** Drög (Fyrir Sprett 105)
**Ábyrgðamaður:** Aðal (Yfirarkítekt)

## 1. Samhengi og Rökstuðningur
Til að uppfylla "Right to Erasure" (GDPR) án þess að eyðileggja stærðfræðilega samfelldni `audit_chain` töflunnar, þurfum við að innleiða hjúpdulkóðun (Envelope Encryption). Opus flaggaði tveimur kröfum áður en kóðun gæti hafist: 
1. `Per-user` DEK lyklar valda of miklu álagi (performance hit) við lestur á stórum loggum.
2. Staðsetning KEK (Master lykils) krefst formlegrar ákvörðunar út frá ógnanalíkani.

## 2. Ákvörðun 1: DEK Granularity (Upplausn dulkóðunarlykla)
* **Hönnun:** Við notum DEK (Data Encryption Key) upplausnina **`(org_id, month_bucket)`**. 
* **Framkvæmd:** Allar loggfærslur fyrirtækis "A" fyrir maí 2026 eru dulkóðaðar með sama DEK lykli. Við lestur úttektarskýrslu yfir mánuðinn þarf aðeins að afkóða *einn* lykil úr minni til að lesa þúsundir færslna, sem leysir afkastavandamálið algjörlega.
* **Crypto-Shredding útfærsla:** Þar sem DEK lykillinn spannar heilan mánuð fyrir heilt fyrirtæki getum við *ekki* eytt DEK lyklinum til að eyða einum notanda. Þess í stað verða öll PII gögn (Nafn, Kennitala) inni í loggfærslunni hösjuð (One-Way Hash með Salti) eða tengd við aðskilda PII-vörpunartöflu (Tokenization). Við eyðingarkröfu eyðum við tengingunni í vörpunartöflunni, sem gerir PII gögnin í loggnum órekjanleg, en viðheldur DEK lyklinum fyrir restina af mánuðinum.

## 3. Ákvörðun 2: KEK Storage Decision (Geymsla Master Lykils)
* **Hönnun:** KEK (Key Encryption Key) mun lifa í **Local Encrypted Vault** (t.d. HashiCorp Vault hýst innan sömu netgirðingar og RunPod/Alvitur), en *ekki* hjá erlendum skýjaþjónustuaðila eins og AWS KMS.
* **Ógnanalíkan (Threat Model):**
    * *AWS KMS áhætta:* Ef við notum bandaríska skýjaþjónustu falla lyklarnir undir *US CLOUD Act*, sem grefur undan "Gagnaheimili stjórnsýslunnar" (Data Sovereignty).
    * *Local Vault áhætta:* Ef RunPod þjónninn er yfirtekinn líkamlega, gætu lyklar komist í hendur þriðja aðila.
* **Mótvægisaðgerð:** KEK lyklarnir verða aftur á móti dulkóðaðir í hvíld og ræstir með "Auto-Unseal" ferli við ræsingu, og lyklavélin verður algjörlega aðskilin frá `web_server.py` netlaginu. Þetta hámarkar íslenskt gagnaforræði.
