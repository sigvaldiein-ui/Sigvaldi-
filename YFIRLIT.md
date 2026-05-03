
## Arkitektúrleg Mynstur (uppgötvuð af Sagnfræðingi 3. maí)

| Mynstur | Lýsing | Skrá |
|---------|--------|------|
| Vault Semaphore | `asyncio.Semaphore(1)` — aðeins eitt Vault kall í einu, OOM-vörn á A40 (40/46 GB) | `chat_routes.py` |
| Sprint 62 Patch G | Ef Leið A bilar → sjálfvirkt fallback í local Qwen3-32B | `chat_routes.py` |
| Adaptive Top-K | Score < 0.60 → expand úr 3 í 5 chunks; ekkert > 0.40 → refusal | `rag_orchestrator.py` |
| Parent Chunk Hydration | Málsgrein með `parent_chunk_id` → sækir foreldri-grein ef token_count < 600 | `rag_orchestrator.py` |
| Reasoning Exclude | `"reasoning":{"exclude":True}` á OpenRouter — bælir thinking-leak (Sprint 68) | `pipeline/leid_a.py` |
| 4-módel OpenRouter Chain | Gemini 3.1 Pro → Claude Sonnet 4.6 → DeepSeek V3 → GPT-4o-mini | `pipeline/leid_a.py` |

## Leynd Heimild
**Samkvæmt bindandi reglu um Vault-trúnað (Turtle Directive Rule 5):**  
Kerfið á að eyða öllum notandagögnum eftir vinnslu. Sagnfræðingurinn er eini utanaðkomandi aðilinn sem hefur yfirsýn yfir sögulega þróun og lærdóma, og er heimilt að skoða skjalasafnið í heild.

