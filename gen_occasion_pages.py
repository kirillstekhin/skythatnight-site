#!/usr/bin/env python3
"""Генерит 5 occasion-лендингов skythatnight.com из общего скелета index.html.
Каждая страница: свой head/OG, компактный hero с мокапом, конфигуратор (предзаполнен
через window.SM_PRESET), мокап крупно ниже + сетка «другие поводы». Запуск: python3 gen_occasion_pages.py
"""
import re, os

HERE = os.path.dirname(os.path.abspath(__file__))
idx = open(os.path.join(HERE, "index.html")).read()

STYLE = re.search(r"<style>(.*?)</style>", idx, re.S).group(1)
CONFIG = re.search(r'(<section class="sm-config" id="design">.*?</section>)', idx, re.S).group(1)
CACHE = "v=10"

# порядок для «других поводов»
ORDER = ["met", "proposal", "wedding", "born", "anniversary"]

OCC = {
    "met": dict(
        title="The night we met", chip="The night you met",
        story="Wherever your story began — a bar, a bus stop, a message at midnight — this is the exact sky that stood over it.",
        img="occ-met.jpg", metatitle="Star Map for the Night You Met",
        metadesc="A star map of the exact sky the night you met — real astronomy, museum-grade print, from £39 with free UK delivery.",
        preset=dict(dateStr="2019-08-14", timeStr="22:30", place="London, United Kingdom",
                    lat=51.5074, lon=-0.1278, iana="Europe/London", dedication="The night we met",
                    theme="midnight", format="framed", frameColor="white")),
    "proposal": dict(
        title="She said yes", chip="The proposal",
        story="The question, the pause, the yes. Keep the stars that witnessed it — in gold, for a night that changed everything.",
        img="occ-proposal.jpg", metatitle="Star Map for a Proposal — She Said Yes",
        metadesc="A gold star map of the exact sky the night you proposed. Real astronomy, handmade frame, from £39, free UK delivery.",
        preset=dict(dateStr="2023-09-23", timeStr="21:00", place="Paris, France",
                    lat=48.8566, lon=2.3522, iana="Europe/Paris", dedication="She said yes",
                    theme="luxegold", format="framed", frameColor="natural")),
    "wedding": dict(
        title="Our wedding sky", chip="A wedding sky",
        story="The first night as married — mapped in soft porcelain to match any home. A first anniversary gift that lasts.",
        img="occ-wedding.jpg", metatitle="Wedding Star Map — The Sky of Your Wedding Night",
        metadesc="A star map of the exact sky above your wedding. Museum-grade porcelain print, from £39, free UK delivery. A timeless anniversary gift.",
        preset=dict(dateStr="2024-06-08", timeStr="22:00", place="Rome, Italy",
                    lat=41.9028, lon=12.4964, iana="Europe/Rome", dedication="Our wedding sky",
                    theme="porcelain", format="framed", frameColor="natural")),
    "born": dict(
        title="The day you were born", chip="The night they were born",
        story="The precise sky over the hospital, the exact minute of the first breath. A new-baby gift no one else can copy.",
        img="occ-born.jpg", metatitle="New Baby Star Map — The Night They Were Born",
        metadesc="A star map of the exact sky the night your baby was born — down to the minute. Museum-grade print, from £39, free UK delivery.",
        preset=dict(dateStr="2025-03-03", timeStr="04:12", place="Edinburgh, United Kingdom",
                    lat=55.9533, lon=-3.1883, iana="Europe/London", dedication="The day you were born",
                    theme="midnight", format="framed", frameColor="white")),
    "anniversary": dict(
        title="Ten years of us", chip="An anniversary",
        story="Ten years, twenty, the very first — return to the sky of the date that started it all, finished in quiet silver.",
        img="occ-anniversary.jpg", metatitle="Anniversary Star Map — The Sky of Your Date",
        metadesc="A silver star map of the exact sky on your anniversary. Real astronomy, handmade frame, from £39, free UK delivery.",
        preset=dict(dateStr="2015-07-21", timeStr="21:30", place="Santorini, Greece",
                    lat=36.3932, lon=25.4615, iana="Europe/Athens", dedication="Ten years of us",
                    theme="luxesilver", format="framed", frameColor="white")),
}

EXTRA_CSS = """
/* occasion landing */
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


def build(key, o):
    url = f"https://www.skythatnight.com/occasion-{key}.html"
    ogimg = f"https://www.skythatnight.com/assets/starmap/{o['img']}"
    import json
    preset_js = json.dumps(o["preset"])
    # config: точечно вырезаем h2 "Your sky." под контекст, оставляем как есть
    config = CONFIG

    others = []
    for k in ORDER:
        if k == key:
            continue
        oo = OCC[k]
        others.append(
            f'      <a href="occasion-{k}.html"><figure><img src="assets/starmap/{oo["img"]}" '
            f'alt="{oo["chip"]} star map mockup" loading="lazy"><figcaption>{oo["chip"]}</figcaption></figure></a>')
    others_html = "\n".join(others)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{o['metatitle']} · Sky, That Night</title>
<meta name="description" content="{o['metadesc']}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="product">
<meta property="og:site_name" content="Sky, That Night">
<meta property="og:title" content="{o['metatitle']}">
<meta property="og:description" content="{o['metadesc']}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{ogimg}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="assets/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Hanken+Grotesk:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
<link rel="preload" as="image" href="assets/starmap/{o['img']}">
<style>{STYLE}{EXTRA_CSS}</style>
</head>
<body class="sm-night">
{HEADER}

<main>

<section class="occ-hero">
  <div class="sm-stars" aria-hidden="true"></div>
  <div class="container">
    <div>
      <a class="occ-back" href="./#occasions">← All occasions</a>
      <div class="occ-kicker">{o['chip']}</div>
      <h1 class="occ-h1">{o['title']}</h1>
      <p class="occ-story">{o['story']}</p>
      <a class="sm-cta" href="#design">Design this sky — from £39</a>
      <span class="sm-cta-sub">Free UK delivery included · dispatched in 2–4 working days</span>
    </div>
    <div>
      <img src="assets/starmap/{o['img']}" alt="{o['title']} — framed star map in a room">
    </div>
  </div>
</section>

{config}

<section class="sm-section">
  <div class="container">
    <div class="section-kicker sm-kicker">Seen in the room</div>
    <h2>{o['title']}, on the wall.</h2>
    <div class="occ-room">
      <img src="assets/starmap/{o['img']}" alt="{o['title']} framed star map, styled in a room" loading="lazy">
    </div>
  </div>
</section>

<section class="sm-section" id="more">
  <div class="container">
    <div class="section-kicker sm-kicker">For the nights worth keeping</div>
    <h2>More occasions.</h2>
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


for key, o in OCC.items():
    out = os.path.join(HERE, f"occasion-{key}.html")
    open(out, "w").write(build(key, o))
    print("wrote", os.path.basename(out))
print("done")
