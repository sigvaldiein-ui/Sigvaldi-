# 🏛️ ADR-010: HITL ENGINE & FJÖGURRA AUGNA REGLAN

**Staða:** Innleitt og sannprófað (Sprettir 102 & 97.8)
**Markmið:** Að koma í veg fyrir sjálfs-samþykktir á viðkvæmum aðgerðum Starfsmannsins.

* **Samhengi:** Stjórnsýsla krefst rekjanleika og ábyrgðar. Ef sami aðili getur búið til beiðni (t.d. póstsendingu) og samþykkt hana sjálfur, er öryggiskeðjan brotin.
* **Ákvörðun:**
    1. Innleiða `requester_sub` dálk í `pending_tasks` schema.
    2. Beita stærðfræðilegri lokun í `/api/approve`: Ef `task.get("requester_sub") == approver_sub`, þá skilar kerfið `403 Forbidden`.
* **Afleiðing:** Fjögurra augna reglan (Two-Person Rule) er nú tryggð í kóða. Þetta gerir Starfsmanninn hæfan til að starfa innan ríkisgeirans þar sem alhliða vélargreind þarf alltaf mannlegan bakhjarl.
