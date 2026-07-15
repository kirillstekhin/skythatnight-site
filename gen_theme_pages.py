#!/usr/bin/env python3
"""Генерит 4 theme-лендинга skythatnight.com («Four moods»). Клик по теме → страница
с той же структурой, что occasion-страницы, но конфигуратор предвыбирает кликнутую тему
(window.SM_PRESET={theme}). Запуск: python3 gen_theme_pages.py"""
import re, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
idx = open(os.path.join(HERE, "index.html")).read()

STYLE = re.search(r"<style>(.*?)</style>", idx, re.S).group(1)
CONFIG = re.search(r'(<section class="sm-config" id="design">.*?</section>)', idx, re.S).group(1)
CACHE = "v=11"

ORDER = ["midnight", "luxe", "porcelain", "dense"]

TH = {
    "midnight": dict(
        title="Midnight", label="Midnight",
        story="Deep navy and starlight — our signature finish. Bright stars glow above a midnight-blue sky, the Milky Way drifting across it. The classic that suits every room.",
        hero="hero-midnight.jpg", room="occ-met.jpg", theme="midnight",
        metatitle="Midnight Star Map — Deep Navy & Starlight",
        metadesc="The Midnight star map: deep navy sky, glowing stars, the Milky Way. Museum-grade print of your exact sky, from £39, free UK delivery."),
    "luxe": dict(
        title="Luxe · gold &amp; silver", label="Luxe",
        story="The night sky finished in precious metal — a gold or silver horizon ring and lettering against deep navy. For an anniversary, a wedding, a milestone worth marking. Switch between gold and silver in the panel.",
        hero="hero-luxe.jpg", room="occ-proposal.jpg", theme="luxegold",
        metatitle="Luxe Gold &amp; Silver Star Map",
        metadesc="The Luxe star map: deep navy sky with a gold or silver horizon ring and lettering. Museum-grade print of your exact sky, from £39, free UK delivery."),
    "porcelain": dict(
        title="Porcelain", label="Porcelain",
        story="Ink on warm ivory — an engraved, almost antique look. Light, airy and quietly striking on a pale wall. The bright alternative to midnight.",
        hero="hero-porcelain.jpg", room="occ-wedding.jpg", theme="porcelain",
        metatitle="Porcelain Star Map — Ink on Ivory",
        metadesc="The Porcelain star map: engraved ink constellations on warm ivory paper. Museum-grade print of your exact sky, from £39, free UK delivery."),
    "dense": dict(
        title="Deep sky detail", label="Deep sky",
        story="Every print carries the full sky — over 11,000 stars and the Milky Way, rendered in fine deep-sky detail. Choose Midnight and the whole galaxy comes with it.",
        hero="hero-dense.jpg", room="occ-born.jpg", theme="midnight",
        metatitle="Deep-Sky Detail Star Map — 11,000 Stars",
        metadesc="Deep-sky detail: over 11,000 stars and the Milky Way on every print. Museum-grade star map of your exact sky, from £39, free UK delivery."),
}

EXTRA_CSS = """
/* theme / occasion landing */
.occ-hero { padding: clamp(2.4rem,5vw,4.5rem) 0 clamp(1.5rem,3vw,2.5rem); position:relative; overflow:hidden; }
.occ-hero .container { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:clamp(2rem,4vw,4rem); align-items:center; }
@media (max-width:860px){ .occ-hero .container { grid-template-columns:1fr; } }
.occ-back { display:inline-block; font-family:var(--sans); font-size:.78rem; letter-spacing:.12em; text-transform:uppercase; color:var(--moon-faint); text-decoration:none; margin-bottom:1.4rem; }
.occ-back:hover { color:var(--gold); }
.occ-kicker { font-family:var(--sans); font-size:.78rem; letter-spacing:.32em; text-transform:uppercase; color:var(--gold); margin-bottom:1.1rem; }
.occ-h1 { font-family:var(--serif); font-weight:500; font-size:clamp(2.2rem,4.6vw,3.6rem); line-height:1.08; color:var(--moon); margin:0 0 1.3rem; }
.occ-story { font-family:var(--sans); font-weight:300; font-size:clamp(1rem,1.4vw,1.12rem); line-height:1.7; color:var(--moon-sub); max-width:34rem; margin-bottom:2rem; }
.occ-hero img { width:100%; height:auto; display:block; border-radius:4px; box-shadow:0 30px 80px rgba(0,0,0,.6), 0 0 0 1px rgba(201,169,97,.14); }
.occ-room { margin-top:2.4rem; }
.occ-room img { width:100%; height:auto; display:block; border-radius:4px; box-shadow:0 30px 80px rgba(0,0,0,.6), 0 0 0 1px rgba(201,169,97,.14); }
.occ-more-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:1.1rem; margin-top:2.2rem; }
@media (max-width:860px){ .occ-more-grid { grid-template-columns:repeat(2,1fr); } }
.occ-more-grid a { text-decoration:none; }
.occ-more-grid img { width:100%; height:auto; display:block; border-radius:3px; box-shadow:0 16px 40px rgba(0,0,0,.45), 0 0 0 1px rgba(201,169,97,.12); }
.occ-more-grid figcaption { font-family:var(--serif); font-size:.98rem; color:var(--moon); margin-top:.6rem; }
.occ-more-grid a:hover figcaption { color:var(--gold); }
"""

HEADER = """<header>
  <div class="container header-inner">
    <a href="./" class="logo sm-wordmark" aria-label="Sky, That Night — home">
      <span aria-hidden="true">✦</span>&nbsp;SKY, THAT NIGHT
    </a>
    <button class="mobile-menu-btn" aria-label="Open menu">&#9776;</button>
    <nav class="nav" id="main-nav">
      <a href="./#design">Design yours</a>
      <a href="./#craft">How it works</a>
      <a href="./#faq">FAQ</a>
      <a href="mailto:admin@shopcienty.com">Contact</a>
    </nav>
  </div>
</header>"""

FOOTER = """<footer>
  <div class="container footer-links">
    <div class="foot-link-col">
      <div class="foot-rule">Sky, That Night</div>
      <a href="./#design">Design your sky</a>
      <a href="./#craft">How it works</a>
      <a href="./#faq">FAQ</a>
    </div>
    <div class="foot-link-col">
      <div class="foot-rule">Help</div>
      <a href="mailto:admin@shopcienty.com">admin@shopcienty.com</a>
      <a href="privacy.html">Privacy Policy</a>
      <a href="terms.html">Terms &amp; Conditions</a>
    </div>
  </div>
  <div class="container foot-bottom">
    <p style="font-family:var(--sans);font-size:.75rem;">
      SkyThatNight.com is a trading style of SHOPCIENTY LIMITED · Company No. 14960765 · VAT GB483349856 · 7 Bell Yard, London WC2A 2JR
    </p>
  </div>
</footer>"""


def build(key, t):
    url = f"https://www.skythatnight.com/theme-{key}.html"
    ogimg = f"https://www.skythatnight.com/assets/starmap/{t['hero']}"
    preset_js = json.dumps({"theme": t["theme"]})

    others = []
    for k in ORDER:
        if k == key:
            continue
        tt = TH[k]
        others.append(
            f'      <a href="theme-{k}.html"><figure><img src="assets/starmap/{tt["hero"]}" '
            f'alt="{re.sub("<[^>]+>","",tt["label"])} theme star map" loading="lazy">'
            f'<figcaption>{tt["title"]}</figcaption></figure></a>')
    others_html = "\n".join(others)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t['metatitle']} · Sky, That Night</title>
<meta name="description" content="{t['metadesc']}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="product">
<meta property="og:site_name" content="Sky, That Night">
<meta property="og:title" content="{t['metatitle']}">
<meta property="og:description" content="{t['metadesc']}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{ogimg}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="assets/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Hanken+Grotesk:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
<link rel="preload" as="image" href="assets/starmap/{t['hero']}">
<style>{STYLE}{EXTRA_CSS}</style>
</head>
<body class="sm-night">
{HEADER}

<main>

<section class="occ-hero">
  <div class="sm-stars" aria-hidden="true"></div>
  <div class="container">
    <div>
      <a class="occ-back" href="./#moods">← All four moods</a>
      <div class="occ-kicker">A poster style</div>
      <h1 class="occ-h1">{t['title']}</h1>
      <p class="occ-story">{t['story']}</p>
      <a class="sm-cta" href="#design">Design in this style — from £39</a>
      <span class="sm-cta-sub">Free UK delivery included · dispatched in 2–4 working days</span>
    </div>
    <div>
      <img src="assets/starmap/{t['hero']}" alt="{re.sub('<[^>]+>','',t['title'])} star map poster">
    </div>
  </div>
</section>

{CONFIG}

<section class="sm-section">
  <div class="container">
    <div class="section-kicker sm-kicker">Seen in the room</div>
    <h2>{t['title']}, on the wall.</h2>
    <div class="occ-room">
      <img src="assets/starmap/{t['room']}" alt="{re.sub('<[^>]+>','',t['title'])} star map framed in a room" loading="lazy">
    </div>
  </div>
</section>

<section class="sm-section" id="more">
  <div class="container">
    <div class="section-kicker sm-kicker">Four moods</div>
    <h2>The other styles.</h2>
    <div class="occ-more-grid">
{others_html}
    </div>
  </div>
</section>

</main>

{FOOTER}

<script>window.SM_PRESET = {preset_js};</script>
<script src="assets/starmap.js?{CACHE}" defer></script>
</body>
</html>
"""


for key, t in TH.items():
    out = os.path.join(HERE, f"theme-{key}.html")
    open(out, "w").write(build(key, t))
    print("wrote", os.path.basename(out))
print("done")
