# 🏛️ ADR-013: TIER MAPPING POLICY & BOUNDARY RULES (STARFSMAÐUR)

**Staða:** Bindandi stefnuskjal (GREEN frá Opus)
**Markmið:** Að skilgreina nákvæm landamæri milli greiningarfrelsis og framkvæmdarvalds fyrir aðgangsstigið „Starfsmaður“.

* **Samhengi:** Ef Starfsmaður fær sama opna aðgang og Vitinn, auk aðgangs að gögnum Hvelfingarinnar og framkvæmdarvalds (API/Mail), myndast hætta á sjálfvirkum gagnaleka.
* **Ákvörðun:**
    1. **Innbundin greining:** Starfsmaðurinn hefur yfirgripsmikinn aðgang að gögnum bæði úr opnum og lokuðum gagnlindum stofnunarinnar til greiningar.
    2. **Útbundin framkvæmd:** Öll verkfæri sem breyta stöðu kerfa eða senda gögn út flokkast sem `Critical`. Starfsmaðurinn hefur engin sjálfstæð völd til að ljúka þessum aðgerðum án HITL.
* **Framfylgd:** Verkfæri í `CRITICAL_TOOLS` krefjast þess að manneskja yfirfari pakkann og skili dulkóðaðri samþykkt áður en aðgerðin fer í loftið.
* **Afleiðing:** Nýting á fullri greind (General Machine Intelligence) án áhættu á gagnaleka.
