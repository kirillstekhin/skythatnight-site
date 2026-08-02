#!/usr/bin/env python3
"""Генерит 4 theme-лендинга skythatnight.com («Four moods»). Клик по теме → страница
с той же структурой, что occasion-страницы, но конфигуратор предвыбирает кликнутую тему
(window.SM_PRESET={theme}). Запуск: python3 gen_theme_pages.py"""
import re, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
idx = open(os.path.join(HERE, "index.html")).read()

STYLE = re.search(r"<style>(.*?)</style>", idx, re.S).group(1)
CONFIG = re.search(r'(<section class="sm-config" id="design">.*?</section>)', idx, re.S).group(1)
CACHE = "v=15"

ORDER = ["midnight", "luxe", "porcelain", "dense"]

TH = {
    "midnight": dict(
        title="Midnight", label="Midnight",
        story="Deep navy and starlight — our signature finish. Bright stars glow above a midnight-blue sky, the Milky Way drifting across it. The classic that suits every room.",
        hero="hero-midnight.jpg", room="occ-met.jpg", theme="midnight",
        metatitle="Midnight Star Map — Deep Navy & Starlight",
        # ✅02.08.2026: генератор ДОГНАЛ живые страницы (v-стамп поднят до v=15, фавикон-блок
        # актуализирован, ручные CSS-довески перенесены в EXTRA_CSS, цена берётся из живого
        # index-CONFIG). История мины ниже — оставлена как урок: ПЕРЕД прогоном сверять дифф.
        # ⛔⛔ ГЕНЕРАТОР ОТСТАЛ ОТ ЗАДЕПЛОЕННЫХ theme-*.html (вскрыто 29.07.2026).
        # Живые страницы правились РУКАМИ: там `starmap.js?v=14`, `sm-price` = £44.99 и правила
        # `.sm-frames-grid`. Прогон этого файла молча ОТКАТЫВАЕТ всё три — а откат кэш-версии
        # с 14 на 11 даёт стухший JS через Cloudflare (та же болячка, что была с legal-страницами).
        # ПЕРЕД ЗАПУСКОМ: сверить v-стамп, sm-price и CSS с текущими theme-*.html и подтянуть сюда.
        # 29.07 цену £39→£26.99 в живых страницах правили ТЕКСТОМ, без перегенерации, именно поэтому.
        # 31.07 так же текстом: `sm-price` £49→£44.99 на 4 theme-страницах и в 404.html — £49 был
        # стейл-заглушкой (живой JS для той же комплектации считает £44.99, проверено в браузере),
        # и до загрузки скрипта покупатель видел лишнюю пятёрку.
        metadesc="The Midnight star map: deep navy sky, glowing stars, the Milky Way. Museum-grade print of your exact sky, from £26.99, free UK delivery."),
    "luxe": dict(
        title="Luxe · gold &amp; silver", label="Luxe",
        story="The night sky finished in precious metal — a gold or silver horizon ring and lettering against deep navy. For an anniversary, a wedding, a milestone worth marking. Switch between gold and silver in the panel.",
        hero="hero-luxe.jpg", room="occ-proposal.jpg", theme="luxegold",
        metatitle="Luxe Gold &amp; Silver Star Map",
        metadesc="The Luxe star map: deep navy sky with a gold or silver horizon ring and lettering. Museum-grade print of your exact sky, from £26.99, free UK delivery."),
    "porcelain": dict(
        title="Porcelain", label="Porcelain",
        story="Ink on warm ivory — an engraved, almost antique look. Light, airy and quietly striking on a pale wall. The bright alternative to midnight.",
        hero="hero-porcelain.jpg", room="occ-wedding.jpg", theme="porcelain",
        metatitle="Porcelain Star Map — Ink on Ivory",
        metadesc="The Porcelain star map: engraved ink constellations on warm ivory paper. Museum-grade print of your exact sky, from £26.99, free UK delivery."),
    "dense": dict(
        title="Deep sky detail", label="Deep sky",
        story="Every print carries the full sky — over 11,000 stars and the Milky Way, rendered in fine deep-sky detail. Choose Midnight and the whole galaxy comes with it.",
        hero="hero-dense.jpg", room="occ-born.jpg", theme="midnight",
        metatitle="Deep-Sky Detail Star Map — 11,000 Stars",
        metadesc="Deep-sky detail: over 11,000 stars and the Milky Way on every print. Museum-grade star map of your exact sky, from £26.99, free UK delivery."),
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
/* ручные довески живых страниц, восстановлены 02.08 после отката прогоном */
@media (max-width:820px){ .sm-gallery-grid { grid-template-columns:repeat(2,1fr); } }
.sm-occgrid { display:grid; grid-template-columns:repeat(5,1fr); gap:1.1rem; margin-top:2.2rem; }
@media (max-width:1100px){ .sm-occgrid { grid-template-columns:repeat(3,1fr); } }
/* галерея деталей (перенос Etsy-пакета, 02.08) — как в gen_occasion_pages */
.occ-gallery-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1.1rem; margin-top:2.2rem; }
@media (max-width:860px){ .occ-gallery-grid { grid-template-columns:repeat(2,1fr); } }
.occ-gallery-grid a { text-decoration:none; }
.occ-gallery-grid img { width:100%; height:auto; display:block; border-radius:3px; box-shadow:0 16px 40px rgba(0,0,0,.45), 0 0 0 1px rgba(201,169,97,.12); }
.occ-gallery-grid figcaption { font-family:var(--serif); font-size:.98rem; color:var(--moon); margin-top:.6rem; }
.occ-gallery-grid a:hover figcaption { color:var(--gold); }
/* лайтбокс галереи (02.08): стрелки/клавиши/свайп, без внешних либ */
.occ-lightbox { position:fixed; inset:0; z-index:1000; background:rgba(4,6,18,.93); display:flex; align-items:center; justify-content:center; }
.occ-lightbox[hidden] { display:none; }
.occ-lightbox img { max-width:min(90vw,1000px); max-height:82vh; width:auto; height:auto; border-radius:4px; box-shadow:0 40px 120px rgba(0,0,0,.8); }
.lb-caption { position:absolute; bottom:4vh; left:0; right:0; text-align:center; font-family:var(--serif); font-size:1.05rem; color:var(--moon); }
.lb-close { position:absolute; top:2vh; right:3vw; font-size:2.2rem; background:none; border:none; color:var(--moon); cursor:pointer; line-height:1; }
.lb-prev,.lb-next { position:absolute; top:50%; transform:translateY(-50%); font-size:3rem; background:none; border:none; color:var(--moon); cursor:pointer; padding:1rem; line-height:1; font-family:var(--serif); }
.lb-prev { left:2vw; } .lb-next { right:2vw; }
.lb-close:hover,.lb-prev:hover,.lb-next:hover { color:var(--gold); }
@media (max-width:860px){ .lb-prev,.lb-next { font-size:2.4rem; padding:.6rem; } .occ-lightbox img { max-width:94vw; } }
"""

# Тот же пакет слайдов, что на occasion-страницах и в Etsy-галереях (источник SKN_GALLERY).
GALLERY_SLIDES = [
    ("themes.jpg", "Five themes", "The same sky in five finishes — midnight, porcelain, noir, luxe gold and luxe silver"),
    ("frames.jpg", "Five frames", "Handmade wood and gallery classic frames for a personalised star map"),
    ("personalised.jpg", "Your night, in four lines", "What you personalise on a custom star map print"),
    ("detail.jpg", "Every star in its true position", "Close-up of the astronomical detail on the print"),
    ("sizes.jpg", "Three sizes", "Star map print sizes shown to scale — 30×40, 40×50 and 50×70 cm"),
    ("arrives.jpg", "How it arrives", "Prints ship rolled in a tube, framed pieces boxed with protected corners"),
]


# HTML+JS лайтбокса. Плейн-строка (НЕ f-string — внутри JS с фигурными скобками);
# gallery_html() конкатенирует её к секции галереи.
LIGHTBOX_HTML = """
<div class="occ-lightbox" id="occ-lightbox" hidden role="dialog" aria-label="Image viewer">
  <button class="lb-close" aria-label="Close">&times;</button>
  <button class="lb-prev" aria-label="Previous image">&#8249;</button>
  <img src="" alt="">
  <button class="lb-next" aria-label="Next image">&#8250;</button>
  <div class="lb-caption"></div>
</div>
<script>
(function(){
  var grid=document.querySelector('.occ-gallery-grid'); if(!grid) return;
  var links=[].slice.call(grid.querySelectorAll('a'));
  var lb=document.getElementById('occ-lightbox'), img=lb.querySelector('img'),
      cap=lb.querySelector('.lb-caption'), i=0;
  document.body.appendChild(lb); /* из main (stacking context z:1) в корень — иначе sticky-шапка (z:30) перекрывает крестик */
  function show(n){ i=(n+links.length)%links.length;
    img.src=links[i].getAttribute('href');
    img.alt=links[i].querySelector('img').alt;
    var f=links[i].querySelector('figcaption'); cap.textContent=f?f.textContent:'';
    lb.hidden=false; document.body.style.overflow='hidden'; }
  function hide(){ lb.hidden=true; document.body.style.overflow=''; }
  links.forEach(function(a,n){ a.addEventListener('click',function(e){ e.preventDefault(); show(n); }); });
  lb.querySelector('.lb-prev').addEventListener('click',function(e){ e.stopPropagation(); show(i-1); });
  lb.querySelector('.lb-next').addEventListener('click',function(e){ e.stopPropagation(); show(i+1); });
  lb.querySelector('.lb-close').addEventListener('click',hide);
  lb.addEventListener('click',function(e){ if(e.target===lb) hide(); });
  document.addEventListener('keydown',function(e){ if(lb.hidden) return;
    if(e.key==='Escape') hide(); else if(e.key==='ArrowLeft') show(i-1); else if(e.key==='ArrowRight') show(i+1); });
  var tx=null;
  lb.addEventListener('touchstart',function(e){ tx=e.touches[0].clientX; },{passive:true});
  lb.addEventListener('touchend',function(e){ if(tx===null) return;
    var dx=e.changedTouches[0].clientX-tx; tx=null;
    if(Math.abs(dx)>40) show(dx>0?i-1:i+1); },{passive:true});
})();
</script>"""


def gallery_html():
    def esc(s):
        return s.replace("&", "&amp;").replace('"', "&quot;")
    cells = "\n".join(
        f'      <a href="assets/starmap/gallery/{f}" target="_blank" rel="noopener">'
        f'<figure><img src="assets/starmap/gallery/{f}" alt="{esc(alt)}" loading="lazy">'
        f'<figcaption>{esc(cap)}</figcaption></figure></a>'
        for f, cap, alt in GALLERY_SLIDES)
    return f"""<section class="sm-section">
  <div class="container">
    <div class="section-kicker sm-kicker">Every detail, up close</div>
    <h2>What you're choosing from.</h2>
    <div class="occ-gallery-grid">
{cells}
    </div>
  </div>
</section>""" + LIGHTBOX_HTML

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
      <a href="#contact">Contact</a>
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
      <div class="foot-rule" id="contact" style="scroll-margin-top:100px">Help</div>
      <a href="mailto:admin@shopcienty.com">admin@shopcienty.com</a>
      <a href="delivery.html">Delivery &amp; Returns</a>
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
<link rel="icon" href="assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="assets/favicon.png?v=2">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Hanken+Grotesk:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css?v=2">
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
      <a class="sm-cta" href="#design">Design in this style — from £26.99</a>
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

{gallery_html()}

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

# Регенерация перезаписывает html и ВЫНОСИТ beacon аналитики (поймано 02.08:
# после прогона 0 из 13 страниц со счётчиком). Вшиваем обратно сами — идемпотентно.
import gen_analytics
gen_analytics.inject(True)
