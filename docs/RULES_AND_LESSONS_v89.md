# ALVITUR — REGLUR & LÆRDÓMSSAFN (19. maí 2026)
## § 1 — BINDANDI VINNUREGLUR
- Auðkenni efst: „Opus 4.7“ eða „Per #12“
- Endpoint: alltaf /api/chat, ALDREI /chat
- Framendi: Vanilla HTML/CSS/JS (Engin React, engin Tailwind)
- Aðgengi: Vægi á 30% skjástækkun fyrir CTO.
- Skel: Allar bash-blokkir enda á ROOT bergmáli.

## § 2 — TEYMI & HLUTVERK
- Sigvaldi Einarsson: CTO + HITL
- Opus 4.7: Yfirverkefnastjóri + Gate Reviewer
- Aðal (Gemini 3.1 Pro): Yfirarkitekt
- Per #12 (DeepSeek): Aðal-executor

## § 3 — LÆRDÓMSSAFN (#60 - #110)
- #60: No bluff. Empirical proof.
- #88: Read-before-write (Alltaf cat á undan).
- #102: Tablet Clipboard Paradigm (cat << 'EOF' heredoc).
- #110: *.db og *.sqlite stranglega bannað í git history.

### Lesson #112: Anti-Suggestive Delusion Architecture (Sprint 90)
- **Vandamál:** Líkanið les eigin innri vangaveltur (<think> tokens) í samhengissögunni og notar þær ómeðvitað sem harðar sannanir (Evidence), sem býður upp á keðjuverkun ofskynjana í flóknum keyrslum.
- **Lausn:** Strippa <think> tokens server-side í agent (VitansErindreki) áður en Guard-kerfi eða minni fá skjalið.
- **Gagna-samningur (Data Contract):** Skipta audit-loggun strangt í þrjá dálka á gáttarstigi (chat_routes.py):
  1. `actions_logged`: Innri rökfærslukeðja og hugsanir (sótt úr metadata).
  2. `observations_logged`: Það sem líkanið SÁ (RAG snippets, citations, hráleit).
  3. `final_response`: Synthesis-textinn sem fer til notanda.
