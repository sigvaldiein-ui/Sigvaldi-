# 🏛️ ADR-014: SAMRÆMDUR VEGVÍSIR AÐ FRAMLEIÐSLU (ROADMAP)

**Staða:** Bindandi (Samþykkt af Opus - 22. maí 2026)
**Markmið:** Að festa í stein sprettaröðun fyrir lokafasa Beta-útgáfunnar og framtíðarþróun, og loka á misræmi í númerun.

## FASI 1: PRODUCTION CUTOVER (Sprettir 98–104)
Þessi fasi klárar innviði og gerir kerfið tilbúið fyrir fyrstu B2B viðskiptavinina.
* **Sprettur 98: Frontend Cutover.** Innleiðing á UI fyrir `202 Accepted` status og HITL samþykktarborði fyrir Starfsmanninn.
* **Sprettur 99: Token Lifecycle & Multi-tenant Hardening.** Rauntíma JWT Blacklist, Refresh Tokens og Qdrant `org_id` einangrun.
* **Sprettur 100: Real Tools & Cost.** Útfærsla á `MAIL_SEND` (SMTP), `API_EXEC` (Sandbox) og LLM Token kostnaðarvöktun per fyrirtæki.
* **Sprettur 101: Operational Security.** CSP öryggishausar og sjálfvirk S3 gagnagrunnsafritun (Cron-stýrð).
* **Sprettur 102 & 103: Commercial & Compliance.** Vinnslusamningar (DPA), verðskrármódel og GDPR ROPA frágangur.
* **Sprettur 104: Beta Customer Onboarding.** Fyrsta raunkeyrsla með Auðkenni OIDC og lifandi notendum.

## FASI 2: ALHLIÐA VÉLARGREIND (Sprettir 105–107)
Þessi fasi tekur við eftir Beta-sjósetningu til að dýpka greind og sjálfstæði kerfisins.
* **Sprettur 105: Crypto-Shredding Engine.** Innleiðing á KEK & DEK hjúpdulkóðun til að mæta kröfum um eyðingu (ADR-016).
* **Sprettur 106: Semantic Sovereignty.** Íslensk lögfræðiorðabók (106a), Knowledge Graph bygging (106b) og SLM þjálfun (106c).
* **Sprettur 107: Autonomous Agentic Loop.** Fjölþrepa (multi-step) sjálfstýring Starfsmannsins með samsettu HITL eftirliti (ADR-015).
