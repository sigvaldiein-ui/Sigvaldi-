# GATE_ISL_MALBLAER.md — Íslenskur málblær / formfræði fyrir fullvalda RAG
**Ákvörðun:** 7. júní 2026 · **Af:** Opus 4.8 (gatekeeper) · **Staða:** 🟢 GREEN sem rannsóknargrunnur — innleiðing hvers íhlutar háð mælingar-gátt
**Inntak:** Gemini deep-research + Opus gate-review + Per #15 executor-review

## 1. Niðurstaða
Stefnan er rétt og skorðurnar virtar. EN hver íhlutur háður mælingu: **mæla → Opus review → GREEN → innleiða.** Max 2 iterations.

## 2. Læst umfang
**INN (mælt fyrst):**
- **D — BÍN-lexísk útvíkkun fyrirspurnar** — framlengir `bin_wrapper.py`. Öruggast, engin latency-áhrif.
- **A — Cross-encoder reranker (`bge-reranker-v2-m3`)** á topp-50. Líklega stærsti vogarstöngull. Innleitt aðeins ef mæling styður.

**SKILYRT / SÍÐAST:**
- **B — HyDE/MUGI** — mælt á ~5 fyrirspurnum FYRST. Há áhætta (ofskynjun + ~2-5s).
- **C — NER** — frestað. Aðeins ef mæling sýnir að nafna-árekstrar skaða heimt.

**ÚT (parkað):**
- **GreynirEngine djúpþáttun** — ofurengine fyrir brotakenndar fyrirspurnir.

## 3. Útfærslu-skorður (H20)
- GPU fullur (89/96GB) → reranker á **CPU**; mæla +100-500ms.
- HyDE á sama vLLM = ~2-5s.
- BÍN-útvíkkun = engin latency-áhrif.

## 4. Verifíkeringar-gátt
- Allar tölur staðfestar úr frumheimild/model-card.
- Öll leyfi staðfest. BÍN CC BY-SA 4.0: innanhúss í lagi.
- Hugtök: `bge-reranker-v2-m3` er **cross-encoder**, EKKI late-interaction.

## 5. Mæli- og samþykktarviðmið
- Mælt á 10-20 raunverulegum íslenskum lögfræði-fyrirspurnum.
- Fyrir/eftir á **V1-RAG-001** + **WinoGrande-IS**.

## 6. Röðun og forgangur
**Post-launch.** Per klárar launch-critical fyrst (1.3, 1.4, 2.1).
Röð: 1) BÍN-útvíkkun → 2) mæla reranker → 3) innleiða reranker (ef stutt) → 4) mæla HyDE → 5) meta NER.
