#!/usr/bin/env python3
"""Генерит 9 occasion-лендингов skythatnight.com из общего скелета index.html.
Каждая страница: свой head/OG, компактный hero с мокапом, конфигуратор (предзаполнен
через window.SM_PRESET), мокап крупно ниже + сетка «другие поводы». Запуск: python3 gen_occasion_pages.py
"""
import re, os

HERE = os.path.dirname(os.path.abspath(__file__))
idx = open(os.path.join(HERE, "index.html")).read()

STYLE = re.search(r"<style>(.*?)</style>", idx, re.S).group(1)
CONFIG = re.search(r'(<section class="sm-config" id="design">.*?</section>)', idx, re.S).group(1)
CACHE = "v=14"

# порядок для «других поводов»
ORDER = ["met", "proposal", "wedding", "born", "anniversary",
         "birthday", "new-home", "retirement", "memorial"]

OCC = {
    "met": dict(
        title="The night we met", chip="The night you met",
        story="Wherever your story began — a bar, a bus stop, a message at midnight — this is the exact sky that stood over it.",
        img="occ-met.jpg", metatitle="Star Map for the Night You Met",
        metadesc="A star map of the exact sky the night you met — real astronomy, museum-grade print, from £26.99 with free UK delivery.",
        preset=dict(dateStr="2019-08-14", timeStr="22:30", place="London, United Kingdom",
                    lat=51.5074, lon=-0.1278, iana="Europe/London", dedication="The night we met",
                    theme="midnight", frameType="framed", size="3040", frameColor="white")),
    "proposal": dict(
        title="She said yes", chip="The proposal",
        story="The question, the pause, the yes. Keep the stars that witnessed it — in gold, for a night that changed everything.",
        img="occ-proposal.jpg", metatitle="Star Map for a Proposal — She Said Yes",
        metadesc="A gold star map of the exact sky the night you proposed. Real astronomy, handmade frame, from £26.99, free UK delivery.",
        preset=dict(dateStr="2023-09-23", timeStr="21:00", place="Paris, France",
                    lat=48.8566, lon=2.3522, iana="Europe/Paris", dedication="She said yes",
                    theme="luxegold", frameType="framed", size="3040", frameColor="natural")),
    "wedding": dict(
        title="Our wedding sky", chip="A wedding sky",
        story="The first night as married — mapped in soft porcelain to match any home. A first anniversary gift that lasts.",
        img="occ-wedding.jpg", metatitle="Wedding Star Map — The Sky of Your Wedding Night",
        metadesc="A star map of the exact sky above your wedding. Museum-grade porcelain print, from £26.99, free UK delivery. A timeless anniversary gift.",
        preset=dict(dateStr="2024-06-08", timeStr="22:00", place="Rome, Italy",
                    lat=41.9028, lon=12.4964, iana="Europe/Rome", dedication="Our wedding sky",
                    theme="porcelain", frameType="framed", size="3040", frameColor="natural")),
    "born": dict(
        title="The day you were born", chip="The night they were born",
        story="The precise sky over the hospital, the exact minute of the first breath. A new-baby gift no one else can copy.",
        img="occ-born.jpg", metatitle="New Baby Star Map — The Night They Were Born",
        metadesc="A star map of the exact sky the night your baby was born — down to the minute. Museum-grade print, from £26.99, free UK delivery.",
        preset=dict(dateStr="2025-03-03", timeStr="04:12", place="Edinburgh, United Kingdom",
                    lat=55.9533, lon=-3.1883, iana="Europe/London", dedication="The day you were born",
                    theme="midnight", frameType="framed", size="3040", frameColor="white")),
    "anniversary": dict(
        title="Ten years of us", chip="An anniversary",
        story="Ten years, twenty, the very first — return to the sky of the date that started it all, finished in quiet silver.",
        img="occ-anniversary.jpg", metatitle="Anniversary Star Map — The Sky of Your Date",
        metadesc="A silver star map of the exact sky on your anniversary. Real astronomy, handmade frame, from £26.99, free UK delivery.",
        preset=dict(dateStr="2015-07-21", timeStr="21:30", place="Santorini, Greece",
                    lat=36.3932, lon=25.4615, iana="Europe/Athens", dedication="Ten years of us",
                    theme="luxesilver", frameType="framed", size="3040", frameColor="white")),

    # ── Расширение окейжнов 18.07. Изначально bare-print без комнаты → roomless=True и вне
    # ORDER (неровная сетка «More occasions»), трафик только из sitemap/Pinterest/Etsy/Google.
    # 02.08: комнатные мокапы собраны хромакей-композитом (LISTING_IMAGE_PIPELINE_SOP §5a):
    # сцена gemini-3-pro-image с зелёной заглушкой + chroma_composite.py --outset 0.035,
    # арт = прежние bare-принты (source-assets/occ-bare-prints/) → текст 1:1, координаты сверены.
    # Сетка выровнялась, все девять в ORDER, roomless снят.
    "birthday": dict(
        title="The sky the day you were born", chip="A milestone birthday",
        story="Thirty years, fifty, ninety — turn back to the exact sky that stood over the very first day. A birthday gift that reaches further back than any other.",
        img="occ-birthday.jpg", metatitle="Birthday Star Map — The Sky the Day You Were Born",
        metadesc="A personalised star map of the exact sky on the day you were born — a milestone birthday gift. Real astronomy, museum-grade print, from £26.99 with free UK delivery.",
        preset=dict(dateStr="1974-05-16", timeStr="07:20", place="Manchester, United Kingdom",
                    lat=53.4808, lon=-2.2426, iana="Europe/London", dedication="The day you were born",
                    theme="luxegold", frameType="framed", size="3040", frameColor="natural")),
    "new-home": dict(
        title="Your first night here", chip="A new home",
        story="The first night under a new roof, mapped from the sky above your new front door. A housewarming gift that turns a house into the start of a story.",
        img="occ-new-home.jpg", metatitle="New Home Star Map — The Sky Above Your New Address",
        metadesc="A personalised star map of the sky above your new home on your first night there. A thoughtful housewarming gift, from £26.99 with free UK delivery.",
        preset=dict(dateStr="2025-11-01", timeStr="20:00", place="Bristol, United Kingdom",
                    lat=51.4545, lon=-2.5879, iana="Europe/London", dedication="Our first night here",
                    theme="porcelain", frameType="framed", size="3040", frameColor="white")),
    "retirement": dict(
        title="The end of one chapter", chip="A retirement",
        story="A lifetime of early starts, and now the horizon opens. Mark the day it all wound down — or the day it began — with the sky that watched over a life's work.",
        img="occ-retirement.jpg", metatitle="Retirement Star Map — The Sky of a Life's Work",
        metadesc="A personalised star map to mark a retirement — the sky on the first day, the last, or a date that mattered. A meaningful retirement gift, from £26.99 with free UK delivery.",
        preset=dict(dateStr="2026-03-31", timeStr="17:30", place="Edinburgh, United Kingdom",
                    lat=55.9533, lon=-3.1883, iana="Europe/London", dedication="With gratitude, for a life's work",
                    theme="luxesilver", frameType="framed", size="3040", frameColor="natural")),
    "memorial": dict(
        title="The stars still hold that night", chip="In memory",
        story="Some skies we never want to lose. Map the night they were born, or a date you shared, and keep it somewhere the light can reach — a quiet, lasting way to remember someone who mattered.",
        img="occ-memorial.jpg", metatitle="Memorial Star Map — A Keepsake to Remember Them By",
        metadesc="A personalised star map to remember someone — the sky the night they were born, or a date you shared. A gentle, lasting memorial keepsake, from £26.99 with free UK delivery.",
        preset=dict(dateStr="1948-09-12", timeStr="21:00", place="London, United Kingdom",
                    lat=51.5074, lon=-0.1278, iana="Europe/London", dedication="Always in our hearts",
                    theme="midnight", frameType="framed", size="3040", frameColor="white")),
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
/* галерея деталей (перенос Etsy-пакета, 02.08): 6 слайдов из assets/starmap/gallery/ */
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
/* answer capsule (GEO — прямой ответ для AI-цитирования) */
.occ-capsule { background:rgba(201,169,97,.06); border-left:2px solid var(--gold); border-radius:4px; padding:1.05rem 1.3rem; margin:0 0 2rem; max-width:34rem; }
.occ-capsule p { font-family:var(--sans); font-weight:300; font-size:clamp(.95rem,1.3vw,1.05rem); line-height:1.65; color:var(--moon-sub); margin:0; }
/* occasion FAQ (видимый + FAQPage-схема) */
.occ-faq-list { max-width:44rem; margin-top:1.4rem; }
.occ-faq { border-bottom:1px solid rgba(201,169,97,.16); }
.occ-faq summary { font-family:var(--serif); font-size:1.06rem; color:var(--moon); cursor:pointer; padding:.95rem 0; list-style:none; }
.occ-faq summary::-webkit-details-marker { display:none; }
.occ-faq summary::before { content:"+ "; color:var(--gold); }
.occ-faq[open] summary { color:var(--gold); }
.occ-faq[open] summary::before { content:"− "; }
.occ-faq p { font-family:var(--sans); font-weight:300; font-size:.98rem; line-height:1.7; color:var(--moon-sub); margin:0 0 1rem; max-width:40rem; }
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


OCC_WORD = {
    "met": "star map", "proposal": "proposal", "wedding": "wedding", "born": "new-baby",
    "anniversary": "anniversary", "birthday": "birthday", "new-home": "housewarming",
    "retirement": "retirement", "memorial": "memorial",
}

# Shared factual FAQ (answers extractable как answer-capsules — техника GEO plmba)
BASE_FAQ = [
    ("How accurate is the star map?",
     "Every map is generated from real astronomical data for the exact date, time and place you choose — the true positions of the stars, planets and the Milky Way that night, not a decorative pattern."),
    ("What date and time should I choose?",
     "Use the moment that matters — most people pick the evening of the event. If you don't know the exact time, any time that night still shows the correct sky; the stars shift only slightly across a few hours."),
    ("How long does delivery take?",
     "Free UK delivery, dispatched in 2 to 4 working days. A tracking number is emailed the moment your parcel leaves us."),
    ("Can I return it?",
     "Because each map is made to order to your exact date, place and wording, it's exempt from the usual change-of-mind return — so please check every detail before you order. You're still fully protected if anything's wrong: if it arrives faulty, damaged or not as described, email us within 30 days for a full refund or free replacement, return postage on us."),
]


def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def occasion_faq(key, o):
    w = OCC_WORD.get(key, "star map")
    q = f"Is a star map a good {w} gift?" if w != "star map" else "Is a star map a good gift?"
    a = (f"Yes — it is one of the most personal gifts you can give: the exact night sky over the moment "
         f"that matters, mapped down to the minute and framed to keep. It marks the date in a way a generic gift cannot.")
    return [(q, a)] + BASE_FAQ


# Бес-поводные answer-капсулы (GEO): каждая ведёт ПРЯМЫМ ответом на запрос своего повода,
# self-contained (можно процитировать без страницы), ~70-85 слов, факт+тепло. Хвост «from £26.99…» общий.
TAIL = "Sky, That Night recreates it from real astronomy down to the minute, prints it museum-grade and frames it by hand. From £26.99, with free UK delivery, dispatched in 2 to 4 working days."
CAPSULE = {
    "anniversary": ("An anniversary star map is one of the most personal anniversary gifts you can give: a print of the "
        "exact night sky over the evening your story began — the true positions of the stars above your first date, your "
        "wedding, or any year worth marking, finished in quiet silver. " + TAIL),
    "proposal": ("A proposal star map captures the exact sky the night you asked — the real stars over the place and "
        "minute she said yes, kept in gold for a night that changed everything. It is an engagement gift no one else can "
        "copy, because no two skies are ever alike. " + TAIL),
    "wedding": ("A wedding star map is a print of the exact night sky above your wedding — the real stars over the place "
        "and moment you married, finished in soft porcelain to suit any home. It makes a timeless wedding or "
        "first-anniversary gift. " + TAIL),
    "born": ("A new-baby star map shows the exact night sky the moment your baby was born — the real stars above the "
        "hospital, down to the minute of the first breath. It is a new-baby or christening keepsake no one else can "
        "duplicate, ready to hang in the nursery. " + TAIL),
    "birthday": ("A birthday star map shows the exact night sky on the day someone was born — turn back thirty years, "
        "fifty, or ninety to the real stars that stood over their very first day. It is a milestone-birthday gift that "
        "reaches further back than any other. " + TAIL),
    "new-home": ("A new-home star map is a print of the night sky above a new front door — the real stars over the first "
        "night under a new roof. It is a housewarming gift that turns a house into the start of a story. " + TAIL),
    "retirement": ("A retirement star map marks the close of a life's work with the real night sky over a date that "
        "mattered — the last day, the first, or a moment worth keeping. It is a meaningful retirement gift for someone "
        "who already has everything. " + TAIL),
    # ⚠️мемориал БЕЗ коммерческого хвоста (тон важнее факта о цене/сроках — решение юзера 19.07)
    "memorial": ("A memorial star map keeps the real night sky from a date that mattered — the night someone was born, or "
        "a day you shared — as a quiet, lasting way to remember them. Sky, That Night recreates that sky from real "
        "astronomy, down to the minute, and prints it museum-grade, framed by hand to hang somewhere the light can reach. "
        "Made to order, with free UK delivery."),
    "met": ("A star map of the night you met captures the exact sky over the moment your story started — a bar, a bus "
        "stop, a message at midnight — in real stars, kept to the minute. As personal as the memory itself. " + TAIL),
}


def capsule_text(key, o):
    if key in CAPSULE:
        return CAPSULE[key]
    w = OCC_WORD.get(key, "personalised")
    lead = "A star map" if w == "star map" else f"A {w} star map"
    return (f"{lead} from Sky, That Night is a print of the real night sky above a place and time you choose, "
            f"recreated from astronomical data for the exact date — and minute — that matters. " + TAIL)


def faq_jsonld(faqs):
    import json
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'


def product_jsonld(o, url, ogimg):
    import json
    data = {"@context": "https://schema.org", "@type": "Product",
            "name": o["metatitle"], "description": o["metadesc"], "image": ogimg,
            "brand": {"@type": "Brand", "name": "Sky, That Night"},
            "offers": {"@type": "Offer", "priceCurrency": "GBP", "price": "26.99",
                       "availability": "https://schema.org/InStock", "url": url,
                       "shippingDetails": {"@type": "OfferShippingDetails",
                           "shippingRate": {"@type": "MonetaryAmount", "value": "0", "currency": "GBP"},
                           "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "GB"}}}}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'


def faq_html(faqs):
    items = "\n".join(
        f'      <details class="occ-faq"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>'
        for q, a in faqs)
    return f"""<section class="sm-section" id="faq">
  <div class="container">
    <div class="section-kicker sm-kicker">Good to know</div>
    <h2>Questions, answered.</h2>
    <div class="occ-faq-list">
{items}
    </div>
  </div>
</section>""" + LIGHTBOX_HTML


def capsule_html(text):
    return f'<div class="occ-capsule"><p>{esc(text)}</p></div>'


# Перенос Etsy-пакета на сайт (02.08): те же 6 слайдов, что в галереях листингов.
# Источник — SKN_GALLERY (пересжатые 1200px в assets/starmap/gallery/). Клик = полный слайд.
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
</section>"""


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

    room_html = "" if o.get("roomless") else f"""<section class="sm-section">
  <div class="container">
    <div class="section-kicker sm-kicker">Seen in the room</div>
    <h2>{o['title']}, on the wall.</h2>
    <div class="occ-room">
      <img src="assets/starmap/{o['img']}" alt="{o['title']} framed star map, styled in a room" loading="lazy">
    </div>
  </div>
</section>"""

    faqs = occasion_faq(key, o)
    schema = faq_jsonld(faqs) + product_jsonld(o, url, ogimg)
    cap = capsule_html(capsule_text(key, o))
    faqsec = faq_html(faqs)

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
<link rel="icon" href="assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="assets/favicon.png?v=2">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Hanken+Grotesk:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css?v=2">
<link rel="preload" as="image" href="assets/starmap/{o['img']}">
<style>{STYLE}{EXTRA_CSS}</style>
{schema}
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
      {cap}
      <a class="sm-cta" href="#design">Design this sky — from £26.99</a>
      <span class="sm-cta-sub">Free UK delivery included · dispatched in 2–4 working days</span>
    </div>
    <div>
      <img src="assets/starmap/{o['img']}" alt="{o['title']} — framed star map in a room">
    </div>
  </div>
</section>

{config}

{room_html}

{gallery_html()}

{faqsec}

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

# Регенерация перезаписывает html и ВЫНОСИТ beacon аналитики (поймано 02.08:
# после прогона 0 из 13 страниц со счётчиком). Вшиваем обратно сами — идемпотентно.
import gen_analytics
gen_analytics.inject(True)
