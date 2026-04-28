"""HTML, CSS, JS embedded content for Alvitur web interface.

Extracted from interfaces/web_server.py in Sprint 71 Track A.2 decomposition.
No logic changes — pure code organization.
"""

# Sprint 71 Track A.2a: SHARED_HEAD + SHARED_STYLES
# Sprint 71 Track A.2b: SVG_LOGO, SVG_LOGO_CHAT, CHECK_SVG, ACCENT_CHECK, NAV_SCRIPT, HTML_PAGE

# === Extracted from web_server.py lines 292-1710 ===

SHARED_HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Alvitur – Traust og örugg íslensk gervigreind fyrir lögfræði, fjármál og stjórnsýslu. Við finnum frávik og samhengi á sekúndubrotum í lokuðu Zero-Data umhverfi.">
<meta property="og:title" content="Alvitur – Við greinum gögnin sem skipta máli.">
<meta property="og:description" content="Sérþjálfað gervigreindarkerfi fyrir íslenskar fagstofur. Greindu íslensk lög, samninga og ársreikninga á sekúndum.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://alvitur.is">
<meta property="og:locale" content="is_IS">
<meta property="og:site_name" content="Alvitur">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Alvitur — Íslensk gervigreind">
<meta name="twitter:description" content="Sérþjálfað gervigreindarkerfi fyrir endurskoðendur, lögfræðistofur og fjármálafyrirtæki.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧠</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link href="https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@500,700,800&display=swap" rel="stylesheet">
"""

SHARED_STYLES = """
<style>
  /* ─── Reset & Base ─────────────────────────── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:              #080B12;
    --bg-elevated:     #0F1623;
    --bg-card:         #111827;
    --bg-card-hover:   #1a2436;
    --text-primary:    #F1F5F9;
    --text-secondary:  #94A3B8;
    --text-muted:      #64748B;
    --accent:          #6366F1;
    --accent-light:    #818CF8;
    --accent-glow:     rgba(99, 102, 241, 0.15);
    --accent-glow-strong: rgba(99, 102, 241, 0.25);
    --border:          rgba(148, 163, 184, 0.1);
    --border-strong:   rgba(148, 163, 184, 0.2);
    --green:           #34D399;
    --green-bg:        rgba(52, 211, 153, 0.1);
    --green-border:    rgba(52, 211, 153, 0.2);
    --font-display:    'Cabinet Grotesk', 'Inter', system-ui, sans-serif;
    --font-body:       'Inter', system-ui, sans-serif;
    --font-mono:       'JetBrains Mono', monospace;
    --radius-sm:       0.375rem;
    --radius-md:       0.5rem;
    --radius-lg:       0.75rem;
    --radius-xl:       1rem;
    --transition:      180ms cubic-bezier(0.16, 1, 0.3, 1);
  }

  html {
    scroll-behavior: smooth;
    scroll-padding-top: 5rem;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
  }

  body {
    min-height: 100dvh;
    font-family: var(--font-body);
    font-size: 16px;
    line-height: 1.6;
    color: var(--text-primary);
    background: var(--bg);
  }

  ::selection {
    background: var(--accent-glow-strong);
    color: var(--text-primary);
  }

  :focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 3px;
    border-radius: var(--radius-sm);
  }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }

  img, picture, video, svg { display: block; max-width: 100%; height: auto; }
  a { color: inherit; text-decoration: none; }
  button { cursor: pointer; background: none; border: none; font: inherit; color: inherit; }
  h1, h2, h3, h4, h5, h6 { text-wrap: balance; line-height: 1.15; }
  p, li, figcaption { text-wrap: pretty; max-width: 72ch; }

  /* ─── Skip Link ────────────────────────────── */
  .skip-link {
    position: absolute;
    top: -100%;
    left: 1rem;
    z-index: 100;
    padding: 0.75rem 1.5rem;
    background: var(--accent);
    color: white;
    border-radius: var(--radius-md);
    font-weight: 600;
    font-size: 0.875rem;
  }
  .skip-link:focus {
    top: 1rem;
  }

  /* ─── Container ────────────────────────────── */
  .container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1.5rem;
  }

  /* ─── Nav ───────────────────────────────────── */
  .nav {
    position: sticky;
    top: 0;
    z-index: 50;
    background: rgba(8, 11, 18, 0.85);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    border-bottom: 1px solid var(--border);
    transition: box-shadow var(--transition);
  }
  .nav.scrolled {
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
  }
  .nav-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 4rem;
  }
  .nav-logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--text-primary);
    letter-spacing: -0.02em;
  }
  .nav-logo svg {
    width: 28px;
    height: 28px;
  }
  .nav-links {
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }
  .nav-link {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
    transition: color var(--transition);
  }
  .nav-link:hover { color: var(--text-primary); }

  /* Sprint 19 hotfix: Telegram hraðhnappur í navbar */
  .nav-telegram-btn {
    padding: 0.4rem 0.85rem;
    font-size: 0.8125rem;
    border-radius: var(--radius-md);
  }
  .nav-telegram-btn svg {
    flex-shrink: 0;
  }

  /* ─── Buttons ──────────────────────────────── */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    font-size: 0.875rem;
    font-weight: 600;
    border-radius: var(--radius-md);
    transition: all var(--transition);
    white-space: nowrap;
  }
  .btn-primary {
    background: var(--accent);
    color: white;
    box-shadow: 0 0 0 0 var(--accent-glow);
  }
  .btn-primary:hover {
    background: var(--accent-light);
    box-shadow: 0 0 24px var(--accent-glow-strong);
    transform: translateY(-1px);
  }
  .btn-secondary {
    background: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border-strong);
  }
  .btn-secondary:hover {
    color: var(--text-primary);
    border-color: var(--text-muted);
    background: rgba(255,255,255,0.03);
  }
  .btn-lg {
    padding: 0.875rem 1.75rem;
    font-size: 1rem;
  }

  /* ─── Hero ─────────────────────────────────── */
  /* Sprint 19 hotfix: þéttara hero padding — meira above-the-fold */
  .hero {
    position: relative;
    padding: clamp(3.5rem, 8vw, 7rem) 0 clamp(2.5rem, 5vw, 5rem);
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -200px;
    left: 50%;
    transform: translateX(-50%);
    width: 800px;
    height: 600px;
    background: radial-gradient(ellipse, var(--accent-glow) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }
  .hero-content {
    position: relative;
    z-index: 1;
    text-align: center;
    max-width: 800px;
    margin: 0 auto;
  }
  /* Sprint 19 hotfix: smækkuð status pilla — ýtir minna innihaldi niður */
  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    margin-bottom: 1rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--green);
    background: var(--green-bg);
    border: 1px solid var(--green-border);
    border-radius: var(--radius-xl);
    letter-spacing: 0.03em;
  }
  .hero-badge-dot {
    width: 6px;
    height: 6px;
    background: var(--green);
    border-radius: 50%;
    animation: pulse-dot 2s ease-in-out infinite;
  }
  @keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
  }
  .hero h1 {
    font-family: var(--font-display);
    font-size: clamp(2.5rem, 5vw, 4rem);
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.03em;
    margin-bottom: 1.5rem;
  }
  .hero h1 span {
    background: linear-gradient(135deg, var(--accent-light), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .hero-sub {
    font-size: clamp(1rem, 1.5vw, 1.25rem);
    color: var(--text-secondary);
    max-width: 600px;
    margin: 0 auto 2.5rem;
    line-height: 1.7;
  }
  .hero-actions {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  /* ─── Sections ─────────────────────────────── */
  section {
    padding: clamp(4rem, 8vw, 7rem) 0;
  }
  .section-label {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--accent-light);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 1rem;
  }
  .section-title {
    font-family: var(--font-display);
    font-size: clamp(1.75rem, 3.5vw, 2.5rem);
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    margin-bottom: 1rem;
  }
  .section-desc {
    font-size: 1.0625rem;
    color: var(--text-secondary);
    max-width: 560px;
    line-height: 1.7;
  }
  .section-header {
    text-align: center;
    margin-bottom: clamp(3rem, 5vw, 4rem);
  }
  .section-header .section-desc {
    margin: 0 auto;
  }

  /* ─── Glass Cards ──────────────────────────── */
  .glass-card {
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.8), rgba(15, 22, 35, 0.6));
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 2rem;
    transition: all var(--transition);
    backdrop-filter: blur(8px);
  }
  .glass-card:hover {
    border-color: var(--border-strong);
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.9), rgba(15, 22, 35, 0.7));
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  }

  /* ─── Trust Section ────────────────────────── */
  .trust-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }
  .trust-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-glow);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: var(--radius-lg);
    margin-bottom: 1.25rem;
    color: var(--accent-light);
  }
  .trust-title {
    font-family: var(--font-display);
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }
  .trust-desc {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.6;
  }

  /* ─── Features Section ─────────────────────── */
  .features-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
  .feature-card {
    position: relative;
    overflow: hidden;
  }
  .feature-card.featured {
    grid-column: span 2;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    align-items: center;
  }
  .feature-number {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--accent);
    margin-bottom: 0.75rem;
    font-weight: 500;
  }
  .feature-title {
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }
  .feature-desc {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.6;
  }
  .feature-visual {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    min-height: 200px;
    background: rgba(99, 102, 241, 0.03);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(99, 102, 241, 0.08);
  }
  .code-block {
    font-family: var(--font-mono);
    font-size: 0.8125rem;
    color: var(--text-secondary);
    line-height: 1.8;
    text-align: left;
    white-space: pre;
  }
  .code-block .kw { color: var(--accent-light); }
  .code-block .fn { color: var(--green); }
  .code-block .str { color: #F59E0B; }
  .code-block .cm { color: var(--text-muted); }

  /* ─── Problem/Solution ─────────────────────── */
  .problem-section {
    background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.03), transparent);
  }
  .ps-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3rem;
    align-items: start;
  }
  .ps-card {
    padding: 2.5rem;
    border-radius: var(--radius-xl);
  }
  .ps-card.problem {
    background: rgba(239, 68, 68, 0.03);
    border: 1px solid rgba(239, 68, 68, 0.1);
  }
  .ps-card.solution {
    background: rgba(99, 102, 241, 0.05);
    border: 1px solid rgba(99, 102, 241, 0.15);
  }
  .ps-card h3 {
    font-family: var(--font-display);
    font-size: 1.375rem;
    font-weight: 700;
    margin-bottom: 1rem;
  }
  .ps-card.problem h3 { color: #F87171; }
  .ps-card.solution h3 { color: var(--accent-light); }
  .ps-card p {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.7;
    margin-bottom: 1.25rem;
  }
  .ps-list {
    list-style: none;
    padding: 0;
  }
  .ps-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    font-size: 0.9375rem;
    color: var(--text-secondary);
    margin-bottom: 0.75rem;
    line-height: 1.5;
  }
  .ps-list li svg {
    flex-shrink: 0;
    margin-top: 0.2rem;
  }

  /* ─── Pricing ──────────────────────────────── */
  .pricing-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
    align-items: start;
  }
  .pricing-card {
    position: relative;
    background: linear-gradient(180deg, rgba(17, 24, 39, 0.8), rgba(15, 22, 35, 0.5));
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 2rem;
    transition: all var(--transition);
  }
  .pricing-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  }
  .pricing-card.popular {
    border-color: var(--accent);
    box-shadow: 0 0 40px var(--accent-glow);
  }
  .pricing-card.popular::before {
    content: 'Vinsælast';
    position: absolute;
    top: -0.75rem;
    left: 50%;
    transform: translateX(-50%);
    padding: 0.25rem 1rem;
    background: var(--accent);
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: var(--radius-xl);
    white-space: nowrap;
  }
  .pricing-medal {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
  }
  .pricing-name {
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }
  .pricing-target {
    font-size: 0.8125rem;
    color: var(--text-muted);
    margin-bottom: 1.25rem;
  }
  .pricing-price {
    margin-bottom: 1.5rem;
  }
  .pricing-amount {
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.02em;
  }
  .pricing-period {
    font-size: 0.875rem;
    color: var(--text-muted);
  }
  .pricing-features {
    list-style: none;
    padding: 0;
    margin-bottom: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
  }
  .pricing-features li {
    display: flex;
    align-items: flex-start;
    gap: 0.625rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.5;
  }
  .pricing-features li svg {
    flex-shrink: 0;
    margin-top: 0.15rem;
    color: var(--accent-light);
  }
  .pricing-cta {
    width: 100%;
    text-align: center;
    justify-content: center;
  }

  /* ─── C) Dæmisögur (Testimonials) ─────────────────────── */
  .testimonials-section {
    background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.02), transparent);
  }
  .testimonials-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }
  .testimonial-card {
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.8), rgba(15, 22, 35, 0.6));
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 2rem;
    position: relative;
    transition: all var(--transition);
  }
  .testimonial-card:hover {
    border-color: var(--border-strong);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  }
  .testimonial-quote {
    font-size: 2rem;
    color: var(--accent);
    opacity: 0.4;
    line-height: 1;
    margin-bottom: 1rem;
    font-family: Georgia, serif;
  }
  .testimonial-text {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.75;
    margin-bottom: 1.5rem;
    font-style: italic;
  }
  .testimonial-author {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .testimonial-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--accent-glow);
    border: 1px solid rgba(99, 102, 241, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    font-weight: 700;
    color: var(--accent-light);
    flex-shrink: 0;
    font-family: var(--font-display);
  }
  .testimonial-name {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.125rem;
  }
  .testimonial-role {
    font-size: 0.75rem;
    color: var(--text-muted);
  }
  .testimonial-stars {
    display: flex;
    gap: 2px;
    margin-bottom: 1rem;
  }
  .testimonial-stars svg {
    width: 14px;
    height: 14px;
    color: #F59E0B;
    fill: #F59E0B;
  }

  /* ─── CTA Section ──────────────────────────── */
  .cta-section {
    text-align: center;
    position: relative;
  }
  .cta-section::before {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 400px;
    background: radial-gradient(ellipse, var(--accent-glow) 0%, transparent 70%);
    pointer-events: none;
  }
  .cta-section .section-desc {
    margin: 0 auto 2rem;
  }

  /* ─── Footer ───────────────────────────────── */
  .footer {
    border-top: 1px solid var(--border);
    padding: 3rem 0 2rem;
    color: var(--text-muted);
    font-size: 0.8125rem;
  }
  .footer-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    text-align: center;
  }
  .footer-logo {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1rem;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .footer-links {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }
  .footer-links a {
    color: var(--text-muted);
    transition: color var(--transition);
  }
  .footer-links a:hover { color: var(--text-secondary); }
  .footer-legal {
    color: var(--text-muted);
    line-height: 1.8;
  }
  .footer-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    color: var(--green);
    background: var(--green-bg);
    border: 1px solid var(--green-border);
    border-radius: var(--radius-xl);
  }

  /* ─── Beta Kassi ──────────────────────────── */
  .beta-kassi {
    margin: 0 auto 0;
    padding: clamp(1.25rem, 3vw, 2rem) 0;
  }
  /* Sprint 19 hotfix: fágaður Beta kassi — mildara, premium dökkt útlit */
  .beta-kassi-innði {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.04), rgba(20, 184, 166, 0.03));
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-xl);
    padding: clamp(1.25rem, 3vw, 1.75rem) clamp(1.25rem, 3vw, 2rem);
    position: relative;
    overflow: hidden;
  }
  .beta-kassi-innði::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(99,102,241,0.04) 0%, transparent 60%);
    pointer-events: none;
  }
  /* Sprint 19 hotfix: mildari beta-merki litir */
  .beta-kassi-merki {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    margin-bottom: 0.875rem;
    font-size: 0.6875rem;
    font-weight: 600;
    color: var(--text-muted);
    background: rgba(148, 163, 184, 0.06);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    text-transform: uppercase;
    letter-spacing: 0.07em;
  }
  .beta-kassi-merki-dot {
    width: 5px;
    height: 5px;
    background: var(--accent-light);
    border-radius: 50%;
    animation: pulse-dot 2s ease-in-out infinite;
  }
  .beta-kassi-texti {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.75;
    margin-bottom: 1.25rem;
    max-width: 72ch;
  }
  .beta-kassi-hnappur {
    display: inline-flex;
    align-items: center;
    gap: 0.625rem;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: 700;
    color: white;
    background: linear-gradient(135deg, #6366F1, #14B8A6);
    border-radius: var(--radius-md);
    transition: all var(--transition);
    box-shadow: 0 0 0 0 rgba(99,102,241,0.3);
    white-space: nowrap;
  }
  .beta-kassi-hnappur:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 28px rgba(99,102,241,0.35);
    opacity: 0.93;
  }
  @media (max-width: 640px) {
    .beta-kassi-hnappur {
      width: 100%;
      justify-content: center;
    }
  }

  /* ─── Separator ────────────────────────────── */
  .divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-strong), transparent);
    margin: 0;
  }

  /* ─── Animations ───────────────────────────── */
  .fade-in {
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.6s ease-out, transform 0.6s ease-out;
  }
  .fade-in.visible {
    opacity: 1;
    transform: translateY(0);
  }

  /* ─── Mobile ───────────────────────────────── */
  @media (max-width: 768px) {
    .trust-grid { grid-template-columns: 1fr; }
    .features-grid { grid-template-columns: 1fr; }
    .feature-card.featured {
      grid-column: span 1;
      grid-template-columns: 1fr;
    }
    .ps-grid { grid-template-columns: 1fr; }
    .pricing-grid {
      grid-template-columns: 1fr;
      max-width: 400px;
      margin: 0 auto;
    }
    .testimonials-grid { grid-template-columns: 1fr; }
    .nav-link.desktop-only { display: none; }
    .hero h1 { font-size: clamp(2rem, 7vw, 2.5rem); }
    .container { padding: 0 1rem; }
    .hero-actions { flex-direction: column; align-items: center; }
  }

  @media (min-width: 769px) and (max-width: 1024px) {
    .pricing-grid { grid-template-columns: repeat(2, 1fr); }
    .features-grid { grid-template-columns: 1fr; }
    .feature-card.featured {
      grid-column: span 1;
      grid-template-columns: 1fr;
    }
    .testimonials-grid { grid-template-columns: repeat(2, 1fr); }
  }

  /* ─── Mobile nav menu ──────────────────────── */
  .mobile-menu-btn {
    display: none;
    width: 44px;
    height: 44px;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
  }
  /* Sprint 19 hotfix: mobile nav — Telegram hnappur sýnilegur, textatenglar í valmynd */
  @media (max-width: 768px) {
    .mobile-menu-btn { display: flex; }
    .nav-links {
      display: none;
      position: absolute;
      top: 4rem;
      left: 0;
      right: 0;
      flex-direction: column;
      background: rgba(8, 11, 18, 0.97);
      backdrop-filter: blur(16px);
      padding: 1.5rem;
      border-bottom: 1px solid var(--border);
      gap: 0.5rem;
    }
    .nav-links.open { display: flex; }
    .nav-links .nav-link,
    .nav-links .btn {
      width: 100%;
      text-align: center;
      padding: 0.75rem 1rem;
    }
    /* Telegram hraðhnappur alltaf sýnilegur á mobile */
    .nav-telegram-btn {
      padding: 0.35rem 0.7rem;
      font-size: 0.75rem;
      order: 2;
    }
    .mobile-menu-btn {
      order: 3;
    }
    /* Þéttara hero á mobile */
    .hero {
      padding: 2rem 0 1.5rem;
    }
    .hero-badge {
      font-size: 0.625rem;
      padding: 0.2rem 0.6rem;
      margin-bottom: 0.5rem;
    }
    .hero h1 {
      margin-bottom: 1rem;
    }
    .hero-sub {
      margin-bottom: 1.5rem;
    }
  }

  /* ─── Drag-and-Drop svæði — Sprint 20 V5.1 ─── */
  .dnd-section {
    padding: 2rem 0;
  }
  .dnd-zone {
    border: 2px dashed var(--border-strong);
    border-radius: var(--radius-xl);
    padding: clamp(2.5rem, 6vw, 4rem) clamp(1.5rem, 4vw, 3rem);
    text-align: center;
    background: rgba(99, 102, 241, 0.03);
    transition: border-color var(--transition), background var(--transition);
    cursor: default;
    user-select: none;
    position: relative;
  }
  .dnd-zone::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius-xl);
    background: radial-gradient(ellipse at 50% 0%, rgba(99,102,241,0.06) 0%, transparent 70%);
    pointer-events: none;
  }
  .dnd-icon {
    color: var(--accent-light);
    opacity: 0.6;
    margin-bottom: 1.25rem;
  }
  .dnd-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }
  .dnd-sub {
    font-size: 0.9375rem;
    color: var(--text-muted);
    max-width: 480px;
    margin: 0 auto 1.25rem;
    line-height: 1.6;
  }
  .dnd-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    background: rgba(148, 163, 184, 0.06);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  @media (max-width: 768px) {
    .dnd-zone { padding: 2rem 1rem; }
    .dnd-title { font-size: 1.0625rem; }
  }

  /* ─── Legal page styles — Sprint 21 ─────────── */
  .legal-date {
    font-size: 0.8125rem;
    color: var(--text-muted);
    margin-bottom: 1.5rem;
    font-style: italic;
  }
  .subpage-card h2 {
    font-size: 1.0625rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 2rem 0 0.625rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
  }
  .subpage-card h2:first-of-type { border-top: none; margin-top: 1.5rem; }
  .subpage-card p { color: var(--text-secondary); line-height: 1.75; margin-bottom: 1rem; }
  .subpage-card a { color: var(--accent-light); text-decoration: underline; text-underline-offset: 2px; }

  /* ─── Subpage styles ───────────────────────── */
  .subpage-center {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100dvh;
    text-align: center;
    padding: 2rem;
  }
  .subpage-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 3rem;
    max-width: 500px;
    width: 100%;
  }
  .subpage-card h1 {
    font-family: var(--font-display);
    font-size: 1.75rem;
    font-weight: 700;
    margin-bottom: 1rem;
  }
  .subpage-card p {
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
    line-height: 1.7;
  }
  .input-field {
    width: 100%;
    padding: 0.75rem 1rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: 0.9375rem;
    margin-bottom: 0.75rem;
    transition: border-color var(--transition);
  }
  .input-field:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
  .input-field::placeholder { color: var(--text-muted); }
  .checkout-summary {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    text-align: left;
  }
  .checkout-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.9375rem;
    margin-bottom: 0.5rem;
  }
  .checkout-row .label { color: var(--text-secondary); }
  .checkout-row .value { color: var(--text-primary); font-weight: 600; }
  .checkout-total {
    border-top: 1px solid var(--border);
    padding-top: 0.75rem;
    margin-top: 0.75rem;
    font-size: 1.0625rem;
    font-weight: 700;
  }
  .success-check {
    width: 64px;
    height: 64px;
    margin: 0 auto 1.5rem;
    background: var(--green-bg);
    border: 2px solid var(--green-border);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--green);
  }

  /* ─── A) Web Chat stílar ─────────────────────── */
  /* Notuð á /minarsidur síðunni */
  .chat-page body {
    overflow: hidden;
  }
  .chat-haus {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    height: 3.75rem;
    background: rgba(8, 11, 18, 0.92);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 1.25rem;
    gap: 0.75rem;
  }
  .chat-til-baka {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text-secondary);
    text-decoration: none;
    padding: 0.375rem 0.625rem;
    border-radius: var(--radius-sm);
    transition: all var(--transition);
    white-space: nowrap;
  }
  .chat-til-baka:hover {
    color: var(--text-primary);
    background: rgba(255,255,255,0.05);
  }
  .chat-aðskilir {
    width: 1px;
    height: 1.25rem;
    background: var(--border-strong);
    flex-shrink: 0;
  }
  .chat-logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    font-size: 1.0625rem;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    flex: 1;
  }
  .chat-merki {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--green);
    background: var(--green-bg);
    border: 1px solid var(--green-border);
    border-radius: 999px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .chat-merki-dot {
    width: 6px;
    height: 6px;
    background: var(--green);
    border-radius: 50%;
    animation: þreifa 2s ease-in-out infinite;
  }
  @keyframes þreifa {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
  }
  .chat-skipulag {
    display: flex;
    flex-direction: column;
    height: 100dvh;
    padding-top: 3.75rem;
  }
  .chat-saga {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem 0;
    scroll-behavior: smooth;
  }
  .chat-saga::-webkit-scrollbar { width: 6px; }
  .chat-saga::-webkit-scrollbar-track { background: transparent; }
  .chat-saga::-webkit-scrollbar-thumb {
    background: var(--border-strong);
    border-radius: 3px;
  }
  .chat-innri {
    max-width: 800px;
    margin: 0 auto;
    padding: 0 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .boð-lína {
    display: flex;
    gap: 0.75rem;
    animation: renna-inn 0.25s ease-out;
  }
  @keyframes renna-inn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .boð-lína.ai-boð { justify-content: flex-start; }
  .boð-lína.ai-boð .boð-bubble {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 0 var(--radius-lg) var(--radius-lg) var(--radius-lg);
    padding: 0.875rem 1rem;
    max-width: 80%;
    color: var(--text-primary);
  }
  .boð-lína.notenda-boð { justify-content: flex-end; }
  .boð-lína.notenda-boð .boð-bubble {
    background: #3730A3;
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: var(--radius-lg) 0 var(--radius-lg) var(--radius-lg);
    padding: 0.875rem 1rem;
    max-width: 80%;
    color: white;
    word-break: break-word;
  }
  .boð-merki {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
  }
  .ai-merki {
    background: linear-gradient(135deg, var(--accent), #7c3aed);
    box-shadow: 0 0 12px var(--accent-glow);
  }
  .boð-tími {
    font-size: 0.6875rem;
    color: var(--text-muted);
    margin-top: 0.375rem;
    display: block;
  }
  .ai-boð .boð-tími { text-align: left; }
  .notenda-boð .boð-tími { text-align: right; }
  .boð-texti strong { font-weight: 600; }
  .boð-texti em { font-style: italic; color: var(--text-secondary); }
  .boð-texti code {
    font-family: var(--font-mono);
    font-size: 0.8125em;
    background: rgba(255,255,255,0.08);
    padding: 0.125em 0.375em;
    border-radius: 3px;
  }
  .boð-texti pre {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.875rem;
    overflow-x: auto;
    margin: 0.625rem 0;
  }
  .boð-texti pre code { background: none; padding: 0; font-size: 0.8125em; }
  .boð-texti ul, .boð-texti ol {
    padding-left: 1.375rem;
    margin: 0.375rem 0;
  }
  .boð-texti li { margin: 0.25rem 0; }
  .boð-texti a { color: var(--accent-light); text-decoration: underline; text-underline-offset: 2px; }
  .boð-texti p { margin: 0.375rem 0; }
  .boð-texti p:first-child { margin-top: 0; }
  .boð-texti p:last-child { margin-bottom: 0; }
  .boð-texti table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.75rem 0;
    font-size: 0.875em;
  }
  .boð-texti th, .boð-texti td {
    border: 1px solid var(--border-strong);
    padding: 0.5rem 0.75rem;
    text-align: left;
  }
  .boð-texti th {
    background: rgba(255,255,255,0.05);
    font-weight: 600;
    color: var(--text-secondary);
  }
  .boð-texti tr:nth-child(even) { background: rgba(255,255,255,0.02); }
  .hladning-rowr {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 0.375rem 0;
    min-height: 1.5rem;
  }
  .hladning-dot {
    width: 7px;
    height: 7px;
    background: var(--text-muted);
    border-radius: 50%;
    animation: bopp 1.2s ease-in-out infinite;
  }
  .hladning-dot:nth-child(2) { animation-delay: 0.2s; }
  .hladning-dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bopp {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30%            { transform: translateY(-8px); opacity: 1; background: var(--accent-light); }
  }
  .inntak-sviði {
    flex-shrink: 0;
    background: rgba(8, 11, 18, 0.96);
    border-top: 1px solid var(--border);
    padding: 0.875rem 1.25rem 1rem;
  }
  .inntak-innri {
    max-width: 800px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .inntak-rowr {
    display: flex;
    gap: 0.625rem;
    align-items: flex-end;
  }
  .inntak-skrá-hnappurinn {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    color: var(--text-muted);
    cursor: not-allowed;
    opacity: 0.5;
    transition: all var(--transition);
  }
  .inntak-þekja { flex: 1; position: relative; }
  .inntak-textarea {
    width: 100%;
    background: var(--bg-elevated);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-lg);
    padding: 0.625rem 0.875rem;
    color: var(--text-primary);
    font-family: var(--font-body);
    font-size: 0.9375rem;
    line-height: 1.5;
    resize: none;
    min-height: 40px;
    max-height: 200px;
    overflow-y: auto;
    transition: border-color var(--transition), box-shadow var(--transition);
  }
  .inntak-textarea:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
  .inntak-textarea::placeholder { color: var(--text-muted); }
  .inntak-textarea:disabled { opacity: 0.5; cursor: not-allowed; }
  .inntak-senda-hnappurinn {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent);
    border-radius: var(--radius-md);
    color: white;
    cursor: pointer;
    border: none;
    transition: all var(--transition);
  }
  .inntak-senda-hnappurinn:hover:not(:disabled) {
    background: var(--accent-light);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px var(--accent-glow-strong);
  }
  .inntak-senda-hnappurinn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
  .inntak-leiðbeiningar {
    font-size: 0.6875rem;
    color: var(--text-muted);
    text-align: center;
  }
  @media (max-width: 640px) {
    .chat-innri { padding: 0 0.75rem; }
    .inntak-sviði { padding: 0.75rem 0.75rem 0.875rem; }
    .boð-lína.ai-boð .boð-bubble,
    .boð-lína.notenda-boð .boð-bubble { max-width: 92%; }
    .chat-til-baka span { display: none; }
    .chat-merki { display: none; }
  }

  /* Sprint 28: K4/K5 — Mobile polish for intake + results */
  @media (max-width: 640px) {
    /* Intake area */
    .intake-section { padding: 1.5rem 1rem 2rem; }
    .tier-toggle { flex-direction: column; gap: .375rem; }
    .tier-btn { padding: .7rem 1rem; font-size: .875rem; }
    .input-wrap { border-radius: .75rem; }
    .textarea-area { padding: .875rem 1rem .75rem; }
    .intake-textarea { font-size: 1rem; min-height: 5rem; }
    .input-toolbar { padding: .625rem 1rem; gap: .5rem; flex-wrap: wrap; }
    .attach-btn { font-size: .8125rem; padding: .4rem .75rem; }
    .file-hint { display: none; }
    .submit-row { padding: .625rem 1rem .875rem; }
    .greina-btn { width: 100%; padding: .7rem 1rem; font-size: .9375rem; }
    .vault-strip { font-size: .8125rem; padding: .625rem .875rem; }
    /* Results on mobile */
    #v7-results { font-size: .875rem; }
    #v7-results > div { padding: .75rem .875rem; border-radius: .625rem; }
    #v7-status { font-size: .8125rem; padding: .625rem .875rem; }
    /* Section header */
    .section-label { font-size: .625rem; }
    .section-title { font-size: 1.375rem; }
    .section-desc { font-size: .875rem; }
    /* Trust strip */
    .trust-grid { gap: .75rem; }
    .glass-card { padding: 1.25rem; }
    .trust-title { font-size: .9375rem; }
    .trust-desc { font-size: .8125rem; }
  }
</style>
"""

# === End of A.2a extraction ===


# === A.2b extraction ===

# --- SVG_LOGO ---
SVG_LOGO = """<svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Alvitur logo">
  <path d="M14 2L4 24h6l1.5-4h5l1.5 4h6L14 2zm0 8l2.5 7h-5L14 10z" fill="currentColor" opacity="0.9"/>
  <circle cx="14" cy="7" r="2.5" fill="#6366F1"/>
</svg>"""

# SVG logo fyrir chat haus (hexagon útgáfa)

# --- SVG_LOGO_CHAT ---
SVG_LOGO_CHAT = """<svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="width:24px;height:24px;">
  <path d="M16 2L28.7 9.5V24.5L16 32L3.3 24.5V9.5L16 2Z"
        fill="rgba(99,102,241,0.15)"
        stroke="#6366F1"
        stroke-width="1.5"/>
  <path d="M11 22L16 10L21 22M13 19H19"
        stroke="#818CF8"
        stroke-width="1.75"
        stroke-linecap="round"
        stroke-linejoin="round"/>
</svg>"""

# --- CHECK_SVG ---
CHECK_SVG = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'

# --- ACCENT_CHECK ---
ACCENT_CHECK = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'

# --- NAV_SCRIPT ---
NAV_SCRIPT = """
<script data-version="99">
// Scroll-aware nav
const nav = document.querySelector('.nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 20);
}, {passive: true});

// Mobile menu
const menuBtn = document.querySelector('.mobile-menu-btn');
const navLinks = document.querySelector('.nav-links');
if (menuBtn) {
  menuBtn.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    const isOpen = navLinks.classList.contains('open');
    menuBtn.setAttribute('aria-expanded', isOpen);
    menuBtn.innerHTML = isOpen
      ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>'
      : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';
  });
}

// Intersection Observer for fade-in
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
</script>
"""

# --- HTML_PAGE ---
HTML_PAGE = """<!DOCTYPE html>
<html lang="is">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Alvitur | Örugg skjalagreining og gervigreind á stjórnsýslustigi</title>
  <meta name="description" content="Greindu flókin skjöl og spurningar á sekúndum. Þín gögn, þín stjórn. Engin vistun í trúnaðarham.">
  <meta property="og:title" content="Alvitur | Örugg skjalagreining á stjórnsýslustigi">
  <meta property="og:description" content="Íslensk gervigreindarlausn fyrir stjórnsýslu og fyrirtæki. Þín gögn, þín stjórn.">
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
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); }
/* NAV */
.nav { position: fixed; top: 0; left: 0; right: 0; z-index: 50; height: var(--nav-height); background: rgba(245,244,240,0.92); backdrop-filter: blur(12px); border-bottom: 1px solid var(--color-border-light); }
.nav__inner { max-width: var(--content-wide); margin: 0 auto; padding: 0 var(--space-6); height: 100%; display: flex; align-items: center; justify-content: space-between; }
.nav__logo { display: flex; align-items: center; gap: var(--space-2); text-decoration: none; color: var(--color-text); }
.nav__logo-text { font-family: var(--font-display); font-weight: 600; font-size: 1.25rem; letter-spacing: -0.02em; }
.nav__links { display: flex; align-items: center; gap: var(--space-6); }
.nav__link { font-size: var(--text-sm); font-weight: 500; color: var(--color-text-muted); text-decoration: none; }
.nav__link:hover { color: var(--color-accent); }
/* HERO */
.hero { padding-top: calc(var(--nav-height) + var(--space-16)); padding-bottom: var(--space-12); text-align: center; }
.hero__inner { max-width: var(--content-max); margin: 0 auto; padding: 0 var(--space-6); }
.hero__heading { font-family: var(--font-display); font-size: var(--text-hero); font-weight: 600; letter-spacing: -0.03em; line-height: 1.08; color: var(--color-text); margin-bottom: var(--space-5); }
.hero__subtext { font-size: var(--text-base); color: var(--color-text-muted); line-height: 1.65; max-width: 520px; margin: 0 auto var(--space-8); }
.hero__cta { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-6); background: var(--color-accent); color: #FFFFFF; font-size: var(--text-sm); font-weight: 600; text-decoration: none; border-radius: var(--radius-md); }
.hero__cta:hover { background: var(--color-accent-hover); }
/* INTAKE */
.intake-section { padding: 0 var(--space-6) var(--space-16); }
.intake-card { max-width: var(--content-max); margin: 0 auto; background: var(--color-surface); border-radius: var(--radius-xl); box-shadow: var(--shadow-card); border: 1px solid var(--color-border-light); padding: var(--space-6); }
.intake-card--dragover { border-color: var(--color-accent); border-style: dashed; box-shadow: var(--shadow-card-hover); }
.intake-tabs { display: flex; border-bottom: 1px solid var(--color-border-light); margin-bottom: var(--space-5); }
.intake-tab { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); font-size: var(--text-sm); font-weight: 500; color: var(--color-text-muted); background: none; border: none; border-bottom: 2px solid transparent; margin-bottom: -1px; cursor: pointer; }
.intake-tab:hover { color: var(--color-text); }
.intake-tab--active { color: var(--color-accent); border-bottom-color: var(--color-accent); font-weight: 600; }

/* ── Valspjöld (Selectable Cards) ── */
.intake-cards { display: flex; gap: var(--space-4); margin-bottom: var(--space-5); }
.intake-card-option { flex: 1; display: flex; flex-direction: column; align-items: flex-start; padding: var(--space-4); border: 2px solid var(--color-border-light); border-radius: var(--radius-lg); background: var(--color-surface); cursor: pointer; text-align: left; font-family: var(--font-body); transition: all var(--transition-fast); }
.intake-card-option:hover { border-color: var(--color-accent-border); }
.intake-card-option--active { border-color: var(--color-accent); background: var(--color-accent-light); }
.intake-card-option__icon { display: block; font-size: 1.5rem; margin-bottom: var(--space-2); }
.intake-card-option__title { display: block; font-weight: 600; font-size: var(--text-base); color: var(--color-text); margin-bottom: var(--space-1); }
.intake-card-option__desc { display: block; font-size: var(--text-xs); color: var(--color-text-muted); line-height: 1.5; }
.intake-card-option__security { display: block; margin-top: var(--space-3); padding-top: var(--space-3); border-top: 1px solid var(--color-border-light); font-size: var(--text-xs); color: var(--color-text-faint); }
@media (max-width: 600px) { .intake-cards { flex-direction: column; } }
.intake-trust { display: flex; align-items: flex-start; gap: var(--space-3); padding: var(--space-3) var(--space-4); background: var(--color-accent-light); border-radius: var(--radius-md); margin-bottom: var(--space-4); }
.intake-trust p { font-size: var(--text-sm); color: var(--color-accent); line-height: 1.5; }
.intake-textarea { width: 100%; min-height: 120px; padding: var(--space-4); background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-md); font-family: var(--font-body); font-size: var(--text-base); line-height: 1.6; color: var(--color-text); resize: vertical; }
.intake-textarea::placeholder { color: var(--color-text-faint); }
.intake-textarea:focus { outline: none; border-color: var(--color-accent); box-shadow: 0 0 0 3px var(--color-accent-light); }
.intake-body { margin-bottom: var(--space-4); }
.intake-file-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-4); }
.intake-file-left { display: flex; align-items: center; gap: var(--space-2); }
.intake-file-btn { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-2) var(--space-3); font-size: var(--text-sm); font-weight: 500; color: var(--color-text-muted); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: none; cursor: pointer; }
.intake-file-btn:hover { color: var(--color-accent); border-color: var(--color-accent-border); background: var(--color-accent-light); }
.intake-file-hint { font-size: var(--text-xs); color: var(--color-text-faint); }
.intake-attached { display: flex; align-items: center; justify-content: space-between; padding: var(--space-3) var(--space-4); background: var(--color-accent-light); border: 1px solid var(--color-accent-border); border-radius: var(--radius-md); margin-bottom: var(--space-4); }
.intake-attached__name { font-size: var(--text-sm); font-weight: 500; color: var(--color-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240px; }
.intake-attached__size { font-size: var(--text-xs); color: var(--color-text-muted); }
.intake-attached__remove { display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: var(--radius-sm); color: var(--color-text-muted); }
.intake-attached__remove:hover { background: rgba(181,54,75,0.1); color: var(--color-error); }
.intake-submit { display: flex; align-items: center; justify-content: center; gap: var(--space-2); width: 100%; padding: var(--space-3) var(--space-6); background: var(--color-accent); color: #FFFFFF; font-size: var(--text-sm); font-weight: 600; border: none; border-radius: var(--radius-md); cursor: pointer; }
.intake-submit:hover { background: var(--color-accent-hover); }
.intake-submit:disabled { opacity: 0.6; cursor: not-allowed; }
@keyframes fadeSlideIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
@keyframes spin { to { transform: rotate(360deg); } }
.spinner { width: 16px; height: 16px; border: 2px solid var(--color-accent-border); border-top-color: var(--color-accent); border-radius: 50%; animation: spin 0.7s linear infinite; }
.intake-status { max-width: var(--content-max); margin: var(--space-4) auto 0; text-align: center; }
.status-message { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); border-radius: var(--radius-md); font-size: var(--text-sm); }
.status-message--loading { color: var(--color-accent); background: var(--color-accent-light); }
.status-message--error { color: var(--color-error); background: rgba(181,54,75,0.08); }
.status-message--success { color: var(--color-success); background: rgba(45,122,62,0.08); }
.intake-results { max-width: var(--content-max); margin: var(--space-6) auto 0; }
.results-card { background: var(--color-surface); border: 1px solid var(--color-border-light); border-radius: var(--radius-xl); box-shadow: var(--shadow-card); overflow: hidden; animation: fadeSlideIn 400ms var(--ease-out) both; }
.results-header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-4) var(--space-6); border-bottom: 1px solid var(--color-border-light); }
.results-title { font-family: var(--font-display); font-size: var(--text-lg); font-weight: 600; }
.results-badge { display: inline-flex; align-items: center; padding: var(--space-1) var(--space-3); font-size: var(--text-xs); font-weight: 600; color: var(--color-success); background: rgba(45,122,62,0.08); border-radius: var(--radius-sm); }
.results-body { padding: var(--space-6); font-size: var(--text-base); line-height: 1.7; }
.results-body p { margin-bottom: var(--space-4); }
/* TRUST STRIP */
.trust-strip { padding: var(--space-12) var(--space-6) var(--space-8); }
.trust-strip__inner { max-width: var(--content-wide); margin: 0 auto; display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: var(--space-3); }
.trust-strip__item { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-xs); color: var(--color-text-faint); }
.trust-strip__dot { color: var(--color-text-faint); font-size: var(--text-xs); }
.trust-strip__link { text-align: center; margin-top: var(--space-3); }
.trust-strip__link a { font-size: var(--text-xs); font-weight: 600; color: var(--color-accent); text-decoration: none; }
/* BETA NOTE */
.beta-note { padding: 0 var(--space-6) var(--space-10); text-align: center; }
.beta-note p { font-size: var(--text-xs); color: var(--color-text-faint); margin: 0 auto; }
/* FOOTER */
.footer { padding: var(--space-8) var(--space-6); border-top: 1px solid var(--color-border-light); }
.footer__inner { max-width: var(--content-wide); margin: 0 auto; text-align: center; }
.footer__copy { font-size: var(--text-xs); color: var(--color-text-muted); margin-bottom: var(--space-2); }
.footer__copy a, .footer__links a { color: var(--color-text-muted); text-decoration: none; }
.footer__copy a:hover, .footer__links a:hover { color: var(--color-accent); }
.footer__links { font-size: var(--text-xs); color: var(--color-text-muted); margin-bottom: var(--space-2); }
.footer__links span { margin: 0 var(--space-2); }
.footer__eea { font-size: var(--text-xs); color: var(--color-text-faint); }
/* SUBPAGE (for build_subpage compatibility) */
.subpage-card { max-width: var(--content-max); margin: calc(var(--nav-height) + var(--space-8)) auto var(--space-8); padding: var(--space-6); background: var(--color-surface); border-radius: var(--radius-xl); box-shadow: var(--shadow-card); border: 1px solid var(--color-border-light); }
.subpage-card h1 { font-family: var(--font-display); font-size: var(--text-lg); font-weight: 600; margin-bottom: var(--space-4); }
.subpage-card h2 { font-family: var(--font-display); font-size: var(--text-base); font-weight: 600; margin-top: var(--space-6); margin-bottom: var(--space-3); }
.subpage-card p { font-size: var(--text-sm); color: var(--color-text-muted); margin-bottom: var(--space-3); line-height: 1.65; }
.subpage-card a { color: var(--color-accent); }
.legal-date { font-size: var(--text-xs); color: var(--color-text-faint); }
@media (max-width: 640px) {
  :root { --nav-height: 3.25rem; }
  .hero { padding-top: calc(var(--nav-height) + var(--space-10)); padding-bottom: var(--space-8); }
  .intake-card { padding: var(--space-4); }
  .intake-file-row { flex-direction: column; align-items: flex-start; gap: var(--space-2); }
  .trust-strip__inner { flex-direction: column; gap: var(--space-2); }
  .trust-strip__dot { display: none; }
}
  </style>
</head>
<body>
  <a href="#intake-card" class="skip-link">Fara beint í efni</a>
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
        <a href="#um-alvitur" class="nav__link">Um Alvitur</a>
      </div>
    </div>
  </nav>

  <main id="main-content" tabindex="-1">
    <section class="hero" aria-labelledby="hero-heading">
      <div class="hero__inner">
        <h1 class="hero__heading" id="hero-heading">Greindu flókin skjöl og spurningar á sekúndum.</h1>
        <p class="hero__subtext">Íslensk gervigreindarlausn, byggð fyrir stjórnsýslu og fyrirtæki sem gera ströngustu kröfur um upplýsingaöryggi. <strong>Þín gögn, þín stjórn.</strong></p>
        <a href="#intake-card" class="hero__cta">
          Spyrja Alvitur
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M3.75 9h10.5M9.75 4.5L14.25 9l-4.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </a>
      </div>
    </section>

    <section class="intake-section" aria-label="Greiningarsvæði">
      <div class="intake-card" id="intake-card" role="region" aria-label="Inntakssvæði">
        <div class="intake-cards" role="radiogroup" aria-label="Veldu greiningarleið">
          <button class="intake-card-option intake-card-option--active" id="card-vitinn" role="radio" aria-checked="true" data-mode="general">
            <span class="intake-card-option__icon">☀️</span>
            <span class="intake-card-option__title">Vitinn</span>
            <span class="intake-card-option__desc">Fyrir dagleg mál, lögfræði og rannsóknir. Þín spurning, öll þekking netsins — ein niðurstaða.</span>
          </button>
          <button class="intake-card-option" id="card-hvelfing" role="radio" aria-checked="false" data-mode="confidential">
            <span class="intake-card-option__icon">🔒</span>
            <span class="intake-card-option__title">Hvelfingin</span>
            <span class="intake-card-option__desc">Fyrir trúnaðarmálin þín. Þú færð svarið — kerfið gleymir spurningunni.</span>
            <span class="intake-card-option__security">Gögnin þín eyðast sjálfkrafa að vinnslu lokinni. Ekkert stafrænt fótspor verður til.</span>
          </button>
        </div>



        

        <div class="intake-body" id="intake-body">
          <textarea id="query-input" class="intake-textarea" placeholder="Skrifaðu fyrirspurn eða dragðu skjal hingað..." rows="5" aria-label="Fyrirspurn"></textarea>
        </div>

        <div class="intake-file-row">
          <div class="intake-file-left">
            <button class="intake-file-btn" id="file-trigger" type="button" aria-label="Hengja við skjal">
              <svg class="intake-file-btn__icon" viewBox="0 0 16 16" fill="none" aria-hidden="true" width="16" height="16"><path d="M3 10V5a5 5 0 0110 0v5.5a3.5 3.5 0 01-7 0V5.5a2 2 0 014 0V10" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/></svg>
              Hengja við PDF
            </button>
            <input type="file" id="file-input" accept=".pdf,.docx,.xlsx" hidden aria-label="Veldu skjal">
            <span id="attached-file" class="intake-attached" hidden aria-live="polite">
              <span class="intake-attached__info">
                <svg class="intake-attached__icon" viewBox="0 0 16 16" fill="none" aria-hidden="true" width="16" height="16"><path d="M4 4h5l3 3v7H4V4z" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/><path d="M9 4v3h3" stroke="currentColor" stroke-width="1.25"/></svg>
                <span id="attached-name" class="intake-attached__name"></span>
              </span>
              <span id="attached-size" class="intake-attached__size"></span>
              <button id="remove-file" class="intake-attached__remove" type="button" aria-label="Fjarlægja skjal">
                <svg viewBox="0 0 14 14" fill="none" width="14" height="14"><path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              </button>
            </span>
          </div>
          <span class="intake-file-hint">PDF, Word eða Excel</span>
        </div>

        <button class="intake-submit" id="submit-btn" type="button">
          Greina
          <svg class="intake-submit__arrow" viewBox="0 0 18 18" fill="none" aria-hidden="true" width="18" height="18"><path d="M3.75 9h10.5M9.75 4.5L14.25 9l-4.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>

      <div id="status-area" class="intake-status" aria-live="polite"></div>
      <div id="results-area" class="intake-results" hidden aria-live="polite">
        <div class="results-card">
          <div class="results-header">
            <span class="results-title">Niðurstöður greiningar</span>
            <span class="results-badge">Lokið</span>
          </div>
          <div class="results-body" id="results-body"></div>
        </div>
      </div>
    </section>

    <div class="trust-strip" aria-label="Öryggisupplýsingar">
      <div class="trust-strip__inner">
        <span class="trust-strip__item">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M7 1L2 3.25v4C2 10.2 4.2 12.75 7 13.5c2.8-.75 5-3.3 5-6.25v-4L7 1z" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/></svg>
          Engin þjálfun á þínum gögnum
        </span>
        <span class="trust-strip__dot" aria-hidden="true">&middot;</span>
        <span class="trust-strip__item">Hýst innan EES</span>
        <span class="trust-strip__dot" aria-hidden="true">&middot;</span>
        <span class="trust-strip__item">Ekkert vistast í trúnaðarham</span>
        <span class="trust-strip__dot" aria-hidden="true">&middot;</span>
        <span class="trust-strip__item">GDPR &middot; EU AI Act</span>
      </div>
      <div class="trust-strip__link">
        <a href="/oryggi">Sjá öryggisstefnu og gagnaforræði &rarr;</a>
      </div>
    </div>

    <div class="beta-note">
      <p>Alvitur er í prufufasa. Nýjar umbætur birtast reglulega.</p>
    </div>
  </main>

  <footer class="footer" role="contentinfo">
    <div class="footer__inner">
      <p class="footer__copy">&copy; 2026 Orkuskipti ehf. &middot; Kt. 510919-0330 &middot; Kópavogur &middot; <a href="mailto:info@alvitur.is">info@alvitur.is</a></p>
      <p class="footer__links"><a href="/personuvernd">Persónuverndarstefna</a><span>&middot;</span><a href="/skilmalar">Skilmálar</a></p>
      <p class="footer__eea">Gögn unnin innan EES</p>
    </div>
  </footer>

  <script src="/static/app.js?v=20260427"></script>
</body>
</html>"""
