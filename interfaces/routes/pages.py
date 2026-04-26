"""HTML page routes for Alvitur web interface.

Sprint 71 Track A.4a — extracted from interfaces/web_server.py.
APIRouter mounted in web_server.py via app.include_router(pages_router).
"""
import logging
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from interfaces.static_content.html_pages import (
    HTML_PAGE, SHARED_HEAD, SHARED_STYLES,
    SVG_LOGO, SVG_LOGO_CHAT, NAV_SCRIPT, CHECK_SVG, ACCENT_CHECK,
)

logger = logging.getLogger("alvitur.web")
router = APIRouter()



# --- home ---
@router.get("/", response_class=HTMLResponse)
async def home():
    """Forsíða — þjónar index.html úr disk."""
    import os
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content=HTML_PAGE)



# --- build_subpage ---
def build_subpage(titill: str, texti: str) -> str:
    """Sprint 21: Hjálparfall — smíðar einföldu undirsíðu með sama grunn og forsíðan."""
    return HTML_PAGE.replace(
        '<main id="main-content" tabindex="-1">',
        f'<main id="main-content" tabindex="-1"><div class="subpage-card"><h1>{titill}</h1>{texti}</div>',
    ).replace(
        '</main>',
        '</main>',
        1
    )


# ─── Sprint 21: Persónuvernd og Skilmálar ─────────────────────────────


# --- personuvernd ---
@router.get("/personuvernd", response_class=HTMLResponse)
async def personuvernd():
    """Persónuverndarstefna — Sprint 21, lagatexti frá Aðal & Sigvalda."""
    page = build_subpage(
        titill="Persónuverndarstefna Alviturs",
        texti="""
        <p class="legal-date">Síðast uppfært: 6. apríl 2026</p>
        <p>Hjá Alvitri byggjum við allar okkar lausnir á einni meginreglu: <strong>Þín gögn eru þín, og aðeins þín.</strong> Við skiljum að upplýsingarðu sem þú treystir okkur fyrir, sem greiningarvél fyrir stjórnsýslu og atvinnulífið, eru oft afar viðkvæmar.</p>

        <h2>1. Engin geymsla gagna (Zero-Retention Policy)</h2>
        <p>Þegar þú nýtir skjalagreiningarvél Alviturs (Alvitur Analyze) til að vinna úr skjölum (svo sem PDF, Word eða texta), eru gögnin aðeins unnin í dulkóðuðu vinnsluminni á meðan greining stendur yfir. Um leið og niðurstaða hefur verið afhent, er frumgögnunum tafarlaust eytt af netþjónum okkar. Við geymum aldrei skjöl þín nema beinlínis sé óskað eftir því í lokuðum Enterprise-samningum um varðveislu gagna.</p>

        <h2>2. Engin þjálfun á þínum gögnum (No-Training Policy)</h2>
        <p>Við notum gögn viðskiptavina okkar <strong>ALDREI</strong> til að þjálfa okkar eigin gervigreindarlíkön, né leyfum við þriðja aðila að gera slíkt. Þegar Alvitur nýtir stór erlend API líkön í gegnum bakenda okkar, tryggja “Zero-Data” API-samningar við þá þjónustuaðila að engin inntaksgögn eru notuð í neins konar þjálfunarskyni.</p>

        <h2>3. Gagnaflutningur og dulkóðun</h2>
        <p>Öll samskipti milli þín og netþjóna okkar fara fram bak við lokaða “Zero-Trust” innviði (Cloudflare Tunnels) með fullkominni TLS 1.3 dulkóðun. Engin kerfi okkar eru opin beint út á internetið.</p>

        <p>Fyrir fyrirspurnir varðandi meðferð gagna, eða til að nýta rétt þinn til að gleymast samkvæmt persónuverndarlögum (GDPR), vinsamlegast hafið samband á <a href="mailto:info@alvitur.is">info@alvitur.is</a>.</p>
        """
    )
    return HTMLResponse(content=page)



# --- skilmalar ---
@router.get("/skilmalar", response_class=HTMLResponse)
async def skilmalar():
    """Notkunarskilmálar — Sprint 21, lagatexti frá Aðal & Sigvalda."""
    page = build_subpage(
        titill="Notkunarskilmálar Alvitur.is",
        texti="""
        <p class="legal-date">Síðast uppfært: 6. apríl 2026</p>
        <p>Með þ ví að heimsækja eða nota þ jónustu Alvitur.is samþykkir þú eftirfarandi skilmála. Alvitur er ætlað sem B2B og B2G greiningartól, hannað til vinnslu gagna, skjala og texta.</p>

        <h2>1. Takmörkun ábyrgðar</h2>
        <p>Alvitur beitir háþróuðum gervigreindarlíkönum til að greina gögn og draga saman samhengi. Notandi samþykkir og gerir sér grein fyrir því að gervigreind er hugbúnaður sem byggir á líkindareikningi og getur sætt svokölluðum “ofskynjunum” (hallucinations) eða rangtúlkunum.</p>
        <p>Allar niðurstöður frá Alvitri eru <strong>EINGÖNGU</strong> til stuðnings við ákvarðanaatöku. Alvitur getur aldrei komið í stað formlegrar faglegar, lögfræðilegrar, læknisfræðilegrar eða fjárhagslegrar ráðgjafar. Notandi ber einn og alfarið alla ábyrgð á því að yfirfara og staðfesta upplýsingar áður en þær eru nýttar. Alvitur.is ehf. ber enga fjárhagslega eða lagalega ábyrgð á beinni eða óbeinni tjóni sem kann að hljótast af notkun þjónustunnar.</p>

        <h2>2. Uppruni gagna og höfundarréttur</h2>
        <p>Notandi ábyrgist að hann hafi fullan og lögmætan rétt til að hlaða upp og vinna með þau gögn sem hann setur í kerfi Alviturs.</p>

        <h2>3. Umgengni og misnotkun</h2>
        <p>Það er með öllu óheimilt að reyna að afhjúpa eða bakfæra (reverse engineer) kerfisarkitektúr Alviturs. Óheimilt er að beita árásum eða inngripum (svo sem “Prompt Injection”) á gervigreindina eða nýta API lykla okkar utan viðskiptasamninga. Slík brot varða umsvifalausri lokun reiknings og hugsanlegum skaðabótakröfum.</p>

        <p>Spurningar: <a href="mailto:info@alvitur.is">info@alvitur.is</a></p>
        """
    )
    return HTMLResponse(content=page)


# @router.get("/minarsidur", response_class=HTMLResponse)
# async def minarsidur():
#     """A) Web Chat Fasi 1 — v1 minimal (sér .js skrá, engin inline JS)"""
#     html_path = "/workspace/mimir_net/static/minarsidur_v1.html"
#     try:
#         with open(html_path, "r", encoding="utf-8") as f:
#             return HTMLResponse(content=f.read())
#     except FileNotFoundError:
#         return HTMLResponse(content=build_minarsidur_page())
# 



# --- oryggi_page ---
@router.get("/oryggi", response_class=HTMLResponse)
async def oryggi_page():
    """Sprint 29 T1 — Trust Center"""
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="is">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Öryggi | Alvitur</title>
  <meta name="description" content="Hvernig Alvitur meðhöndlar gögn, trúnað og skjalasendingar.">
  <meta property="og:title" content="Öryggi | Alvitur">
  <meta property="og:description" content="Ekkert vistast í trúnaðarham. Sjálfvirk gagnaeyðing. GDPR-samræmt.">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600&display=swap">
  <style>
/* Alvitur.is Design System */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { -webkit-font-smoothing: antialiased; scroll-behavior: smooth; scroll-padding-top: 5rem; }
:root {
  --font-display: 'General Sans', 'Helvetica Neue', sans-serif;
  --font-body: 'Inter', 'Helvetica Neue', sans-serif;
  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
  --text-sm: clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
  --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --text-lg: clamp(1.125rem, 1rem + 0.75vw, 1.375rem);
  --text-hero: clamp(2.5rem, 1rem + 4vw, 4rem);
  --space-1: 0.25rem; --space-2: 0.5rem; --space-3: 0.75rem; --space-4: 1rem;
  --space-5: 1.25rem; --space-6: 1.5rem; --space-8: 2rem; --space-10: 2.5rem;
  --space-12: 3rem; --space-16: 4rem; --space-20: 5rem;
  --color-bg: #F5F4F0;
  --color-surface: #FFFFFF;
  --color-text: #1A1A1A;
  --color-text-muted: #6B6B6B;
  --color-text-faint: #A3A3A3;
  --color-accent: #0A6B6E;
  --color-accent-hover: #085456;
  --color-accent-light: rgba(10, 107, 110, 0.08);
  --color-accent-border: rgba(10, 107, 110, 0.25);
  --color-border: #E2E0DA;
  --color-border-light: #ECEAE5;
  --color-error: #B5364B;
  --color-success: #2D7A3E;
  --radius-sm: 0.375rem; --radius-md: 0.625rem; --radius-lg: 0.875rem; --radius-xl: 1rem;
  --shadow-card: 0 1px 3px rgba(26,26,26,0.04), 0 4px 16px rgba(26,26,26,0.06);
  --shadow-card-hover: 0 2px 8px rgba(26,26,26,0.06), 0 8px 24px rgba(26,26,26,0.08);
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --transition-fast: 150ms var(--ease-out);
  --transition-normal: 250ms var(--ease-out);
  --content-max: 680px;
  --content-wide: 960px;
  --nav-height: 3.75rem;
}
body { min-height: 100dvh; line-height: 1.6; font-family: var(--font-body); font-size: var(--text-base); color: var(--color-text); background-color: var(--color-bg); }
h1,h2,h3,h4,h5,h6 { text-wrap: balance; line-height: 1.15; }
p,li { text-wrap: pretty; max-width: 72ch; }
button { cursor: pointer; background: none; border: none; font: inherit; color: inherit; }
/* NAV */
.nav { position: fixed; top: 0; left: 0; right: 0; z-index: 50; height: var(--nav-height); background: rgba(245,244,240,0.92); backdrop-filter: blur(12px); border-bottom: 1px solid var(--color-border-light); }
.nav__inner { max-width: var(--content-wide); margin: 0 auto; padding: 0 var(--space-6); height: 100%; display: flex; align-items: center; justify-content: space-between; }
.nav__logo { display: flex; align-items: center; gap: var(--space-2); text-decoration: none; color: var(--color-text); }
.nav__logo-text { font-family: var(--font-display); font-weight: 600; font-size: 1.25rem; letter-spacing: -0.02em; }
.nav__links { display: flex; align-items: center; gap: var(--space-6); }
.nav__link { font-size: var(--text-sm); font-weight: 500; color: var(--color-text-muted); text-decoration: none; }
.nav__link:hover { color: var(--color-accent); }
/* ORYGGI PAGE */
.oryggi-main { max-width: var(--content-max); margin: 0 auto; padding: calc(var(--nav-height) + var(--space-12)) var(--space-6) var(--space-16); }
.oryggi-main h1 { font-family: var(--font-display); font-size: clamp(1.75rem, 3vw, 2.25rem); font-weight: 600; letter-spacing: -0.02em; margin-bottom: var(--space-8); }
.oryggi-section { margin-bottom: var(--space-10); }
.oryggi-section h2 { font-family: var(--font-display); font-size: var(--text-lg); font-weight: 600; margin-bottom: var(--space-4); }
.oryggi-section p { font-size: var(--text-base); color: var(--color-text-muted); line-height: 1.7; margin-bottom: var(--space-4); }
.oryggi-cta { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-6); background: var(--color-accent); color: #FFFFFF; font-size: var(--text-sm); font-weight: 600; text-decoration: none; border-radius: var(--radius-md); margin-top: var(--space-4); }
.oryggi-cta:hover { background: var(--color-accent-hover); }
.oryggi-trust { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-xs); color: var(--color-text-faint); margin-top: var(--space-3); }
/* FOOTER */
.footer { padding: var(--space-8) var(--space-6); border-top: 1px solid var(--color-border-light); }
.footer__inner { max-width: var(--content-wide); margin: 0 auto; text-align: center; }
.footer__copy { font-size: var(--text-xs); color: var(--color-text-muted); margin-bottom: var(--space-2); }
.footer__copy a, .footer__links a { color: var(--color-text-muted); text-decoration: none; }
.footer__copy a:hover, .footer__links a:hover { color: var(--color-accent); }
.footer__links { font-size: var(--text-xs); color: var(--color-text-muted); margin-bottom: var(--space-2); }
.footer__links span { margin: 0 var(--space-2); }
.footer__eea { font-size: var(--text-xs); color: var(--color-text-faint); }
@media (max-width: 640px) {
  :root { --nav-height: 3.25rem; }
  .oryggi-main { padding-top: calc(var(--nav-height) + var(--space-8)); }
}
  </style>
</head>
<body>
  <nav class="nav" role="navigation" aria-label="Aðalvalmynd">
    <div class="nav__inner">
      <a href="/" class="nav__logo" aria-label="Alvitur forsíða">
        <svg class="nav__logo-mark" viewBox="0 0 28 28" fill="none" aria-hidden="true" width="28" height="28">
          <rect width="28" height="28" rx="6" fill="currentColor" opacity="0.1"/>
          <path d="M7 21L14 7L21 21M10.5 16h7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span class="nav__logo-text">Alvitur</span>
      </a>
      <div class="nav__links">
        <a href="/oryggi" class="nav__link">Öryggi</a>
        <a href="/" class="nav__link">&larr; Til baka</a>
      </div>
    </div>
  </nav>

  <main class="oryggi-main">
    <h1>Öryggi og gagnaforræði</h1>

    <section class="oryggi-section">
      <h2>Engin þjálfun á þínum gögnum</h2>
      <p>Hjá Alvitri teljum við að stofnanir og fyrirtæki eigi ekki að þurfa að velja á milli þess að nýta kraft öflugustu gervigreindar heims og þess að vernda viðkvæm gögn. Við höfum smíðað íslenskt vinnsluumhverfi og arkitektúr sem tryggir fullt gagnaforræði í hverju skrefi.</p>
      <p>Við nýtum eingöngu lokuð fyrirtækjaskil (Enterprise APIs) við stærstu mállíkön heims, þar sem gilda ströng skilyrði um gagnavernd. Við ábyrgjumst lagalega og tæknilega að hvorki skjöl né fyrirspurnir sem fara í gegnum Alvitur verði nokkurn tímann nýtt til að þjálfa, fínstilla eða bæta gervigreindarlíkön birgja okkar. Hugverkið þitt er varið.</p>
    </section>

    <section class="oryggi-section">
      <h2>Sjálfvirk gagnaeyðing í trúnaðarham</h2>
      <p>Fyrir viðkvæmustu upplýsingarnar krefst kerfið þess að notandi velji Trúnaðarvinnslu (Leið B). Undir þessu vinnslulagi eru skjöl lesin beint inn í vinnsluminni (RAM) á netþjónum okkar &mdash; þau snerta aldrei varanlegan harðan disk.</p>
      <p>Að greiningu lokinni er minnið hreinsað og gögnin eyðast sjálfkrafa. Engin varanleg afrit verða til. Það er ekki hægt að ná í gögn sem eru ekki lengur til.</p>
    </section>

    <section class="oryggi-section">
      <h2>Lögsaga og evrópskir innviðir</h2>
      <p>Allur vélbúnaður sem knýr gagnagátt Alviturs er hýstur í vottuðum gagnaverum innan Evrópska efnahagssvæðisins (EES). Kerfið lútur persónuverndarlögum (GDPR) að fullu.</p>
      <p>Með innbyggðri gagnaflokkun styður Alvitur við kröfur ISO 42001 og komandi löggjöf Evrópusambandsins (EU AI Act) um ábyrga og rekjanlega notkun gervigreindar.</p>
    </section>

    <section class="oryggi-section">
      <h2>Sannanlegur rekjanleiki</h2>
      <p>Til að styðja við örugga skjalavörslu og innri endurskoðun heldur kerfið utan um dulkóðaða atvikaskrá (Audit Trail). Við skráum að vinnsla á ákveðnu öryggisstigi fór fram, ásamt metadata og tímasetningu, en innihald gagnanna eða skjalsins sjálfs er aldrei varðveitt á Trúnaðarleiðinni.</p>
    </section>

    <div style="text-align: center; padding: var(--space-8) 0;">
      <a href="/" class="oryggi-cta">
        Hefja örugga greiningu
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M3.75 9h10.5M9.75 4.5L14.25 9l-4.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </a>
      <div class="oryggi-trust">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M7 1L2 3.25v4C2 10.2 4.2 12.75 7 13.5c2.8-.75 5-3.3 5-6.25v-4L7 1z" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/></svg>
        Styður við kröfur ISO 42001 og GDPR
      </div>
    </div>
  </main>

  <footer class="footer" role="contentinfo">
    <div class="footer__inner">
      <p class="footer__copy">&copy; 2026 Orkuskipti ehf &middot; <a href="mailto:info@alvitur.is">info@alvitur.is</a></p>
      <p class="footer__links"><a href="/personuvernd">Persónuverndarstefna</a><span>&middot;</span><a href="/skilmalar">Skilmálar</a></p>
      <p class="footer__eea">Gögn unnin innan EES</p>
    </div>
  </footer>
</body>
</html>""")
# ── Sprint 43b: /askrift pricing page ──────────────────────────────────────────

# --- askrift_page ---
@router.get("/askrift", response_class=HTMLResponse)
async def askrift_page():
    """Sprint 43b — Pricing / subscription page."""
    try:
        from sprint43.pricing_page import render_pricing_page
        return HTMLResponse(content=render_pricing_page())
    except ImportError:
        return HTMLResponse(content="""<!DOCTYPE html>
<html lang="is"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Áskrift — Alvitur</title>
<style>body{font-family:system-ui,sans-serif;background:#0F1117;color:#E2E8F0;display:flex;justify-content:center;padding:3rem}
.c{max-width:600px;text-align:center}h1{margin-bottom:1rem}p{color:#94A3B8;margin-bottom:.5rem}
a{color:#6366F1}</style></head><body><div class="c">
<h1>Áskrift — Alvitur</h1>
<p>Brons: 990 kr/mán — 100 fyrirspurnir</p>
<p>Silfur: 4.990 kr/mán — 1.000 fyrirspurnir</p>
<p>Gull: 14.990 kr/mán — 5.000 fyrirspurnir</p>
<p style="margin-top:1.5rem"><a href="mailto:info@alvitur.is">Hafðu samband</a></p>
</div></body></html>""")


# ─────────────────────────────────────────────────────────────────────────────



# --- serve_v2 ---
@router.get("/alvitur-v2", response_class=HTMLResponse)
async def serve_v2():
    return HTMLResponse(content=HTML_PAGE)


# --- serve_demo ---
@router.get("/mimir-demo", response_class=HTMLResponse)
async def serve_demo():
    return HTMLResponse(content=HTML_PAGE)


# ═══════════════════════════════════════════════════════════════════════
# Sprint 61 - Leid A/B helpers (sovereign separation)
# ═══════════════════════════════════════════════════════════════════════

