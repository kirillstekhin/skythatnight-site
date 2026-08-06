#!/usr/bin/env python3
"""Раздел Famous Nights: витрина famous-nights.html + 11 страниц night-<slug>.html.

ЗАЧЕМ (30.07.2026). Пины и Reels серии вели на главную: человек посмотрел ролик про
ночь Уэмбли-66, кликнул — и попал на общий конфигуратор. Разрыв. Теперь у каждой ночи
своя страница: история, наша статика, ролик — и конфигуратор, УЖЕ заряженный этой
ночью (window.SM_PRESET, тот же механизм, что у occasion-страниц). Плюс 12 страниц
реального содержания под поиск.

ИСТОЧНИК ОДИН — тот же, что у публикаций: tools/social/posting_plan.json (тексты,
ассеты) + tools/social/famous_nights.json (факты неба). Никакой копии контента в этом
файле нет — правка календаря или копии постов меняет и сайт. Сквозное = одинаковое.

Скелет (STYLE, CONFIG) берётся из index.html — как в gen_occasion_pages.py.
⚠️Урок gen_theme_pages: этот генератор НЕ трогает чужие страницы, только пишет свои.

Запуск: python3 gen_famous_nights.py  (потом gen_sitemap.py)
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
idx = open(os.path.join(HERE, "index.html")).read()
STYLE = re.search(r"<style>(.*?)</style>", idx, re.S).group(1)
CONFIG = re.search(r'(<section class="sm-config" id="design">.*?</section>)', idx, re.S).group(1)

plan = json.load(open(os.path.join(HERE, "..", "tools", "social", "posting_plan.json")))
nights = {e["slug"]: e for e in json.load(
    open(os.path.join(HERE, "..", "tools", "social", "famous_nights.json")))["events"]}

BASE = "https://www.skythatnight.com"

# Часовой пояс: в календаре он числом (для python-движка), конфигуратору нужна зона —
# state.tz пересчитывается из iana на каждый refresh (starmap.js: tzOffsetHours).
IANA = {
    "royal-wedding-1981": "Europe/London", "world-cup-1966": "Europe/London",
    "mtv-launch": "America/New_York", "petit-wire": "America/New_York",
    "perseids": "Europe/London", "woodstock": "America/New_York",
    "carrington": "Europe/London", "abbey-road": "Europe/London",
    "columbus-landfall": "America/Nassau", "berlin-wall": "Europe/Berlin",
    "millennium": "Europe/London",
    # ── добавлено 06.08.2026: ночи из плана, которым не хватало пояса ──
    "gertrude-ederle": "Europe/London",          # Kingsdown, Kent
    "matthew-webb": "Europe/London",             # Dover
    "full-moon-august": "Europe/London",
    "beatles-last-concert": "America/Los_Angeles",  # Candlestick Park, SF
    "voyager-1": "America/New_York",             # Cape Canaveral
    "roald-dahl": "Europe/London",               # Llandaff, Cardiff
    "equinox-autumn": "Europe/London",
    "neptune": "Europe/Berlin",
}

# Рама для пресета — по теме ночи (пары из канона мокапов: gold на luxegold/noir, black на midnight).
FRAME = {"midnight": ("classic", "black"), "luxegold": ("classic", "gold"),
         "noir": ("classic", "gold"), "porcelain": ("framed", "natural"),
         "luxesilver": ("classic", "silver")}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def nice_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def coords(lat, lon):
    return (f"{abs(lat):.4f}° {'N' if lat >= 0 else 'S'} · "
            f"{abs(lon):.4f}° {'E' if lon >= 0 else 'W'}")


EXTRA_CSS = """
/* famous nights */
.fn-hero { padding: clamp(2.4rem,5vw,4.5rem) 0 clamp(1.5rem,3vw,2.5rem); position:relative; overflow:hidden; }
.fn-hero .container { display:grid; grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr); gap:clamp(2rem,4vw,4rem); align-items:center; }
@media (max-width:860px){ .fn-hero .container { grid-template-columns:1fr; } }
.fn-back { display:inline-block; font-family:var(--sans); font-size:.78rem; letter-spacing:.12em; text-transform:uppercase; color:var(--moon-faint); text-decoration:none; margin-bottom:1.4rem; }
.fn-back:hover { color:var(--gold); }
.fn-kicker { font-family:var(--sans); font-size:.78rem; letter-spacing:.32em; text-transform:uppercase; color:var(--gold); margin-bottom:1.1rem; }
.fn-h1 { font-family:var(--serif); font-weight:500; font-size:clamp(2rem,4.2vw,3.2rem); line-height:1.1; color:var(--moon); margin:0 0 1.1rem; text-wrap:balance; }
.fn-quote { font-family:var(--serif); font-style:italic; font-size:clamp(1.25rem,2vw,1.6rem); color:var(--gold); margin:0 0 1.3rem; }
.fn-story { font-family:var(--sans); font-weight:300; font-size:clamp(1rem,1.4vw,1.12rem); line-height:1.7; color:var(--moon-sub); max-width:36rem; margin-bottom:1.6rem; }
.fn-facts { font-family:var(--sans); font-size:.82rem; letter-spacing:.08em; color:var(--moon-faint); margin-bottom:2rem; }
.fn-facts b { color:var(--moon-sub); font-weight:500; }
.fn-hero img { width:100%; height:auto; display:block; border-radius:4px; box-shadow:0 30px 80px rgba(0,0,0,.6), 0 0 0 1px rgba(201,169,97,.14); }
.fn-film video { width:100%; max-width:420px; aspect-ratio:9/16; display:block; margin:2rem auto 0; border-radius:6px; background:#000; box-shadow:0 30px 80px rgba(0,0,0,.6), 0 0 0 1px rgba(201,169,97,.14); }
.fn-ai { font-family:var(--sans); font-size:.78rem; color:var(--moon-faint); text-align:center; max-width:34rem; margin:1rem auto 0; }
.fn-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:1.1rem; margin-top:2.2rem; }
@media (max-width:860px){ .fn-grid { grid-template-columns:repeat(2,1fr); } }
.fn-grid a { text-decoration:none; }
.fn-grid img { width:100%; height:auto; display:block; border-radius:3px; box-shadow:0 16px 40px rgba(0,0,0,.45), 0 0 0 1px rgba(201,169,97,.12); }
.fn-grid .d { font-family:var(--sans); font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; color:var(--moon-faint); margin-top:.65rem; }
.fn-grid figcaption { font-family:var(--serif); font-size:.98rem; color:var(--moon); margin-top:.2rem; }
.fn-grid a:hover figcaption { color:var(--gold); }
/* hub */
.fn-hub-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1.6rem; margin-top:2.6rem; }
@media (max-width:1020px){ .fn-hub-grid { grid-template-columns:repeat(2,1fr); } }
@media (max-width:640px){ .fn-hub-grid { grid-template-columns:1fr; } }
"""

HEADER = """<header>
  <div class="container header-inner">
    <a href="./" class="logo sm-wordmark" aria-label="Sky, That Night — home">
      <span aria-hidden="true">✦</span>&nbsp;SKY, THAT NIGHT
    </a>
    <button class="mobile-menu-btn" aria-label="Open menu">&#9776;</button>
    <nav class="nav" id="main-nav">
      <a href="./#design">Design yours</a>
      <a href="famous-nights.html">Famous Nights</a>
      <a href="./#faq">FAQ</a>
      <a href="#contact">Contact</a>
    </nav>
  </div>
</header>"""

# email_off: КРАУЛЕР Google должен видеть email в открытую — Cloudflare
# Email Obfuscation превращал его в [email protected], что попало в претензию
# Misrepresentation (нет способа связаться). Комментарий отключает обфускацию точечно.
FOOTER = """<footer>
  <div class="container footer-links">
    <div class="foot-link-col">
      <div class="foot-rule">Sky, That Night</div>
      <a href="./#design">Design your sky</a>
      <a href="famous-nights.html">Famous Nights</a>
      <a href="./#faq">FAQ</a>
    </div>
    <div class="foot-link-col">
      <div class="foot-rule" id="contact" style="scroll-margin-top:100px">Help</div>
      <!--email_off--><a href="mailto:admin@shopcienty.com">admin@shopcienty.com</a><!--/email_off-->
      <a href="about.html">About Us</a>
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


def head(title, desc, path, ogimg, extra_schema="", preload=None):
    pre = f'\n<link rel="preload" as="image" href="{preload}">' if preload else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}/{path}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Sky, That Night">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}/{path}">
<meta property="og:image" content="{ogimg}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="assets/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Hanken+Grotesk:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css?v=2">{pre}
<style>{STYLE}{EXTRA_CSS}</style>
{extra_schema}
</head>
<body class="sm-night">"""


def others_grid(current):
    cells = []
    for p in plan["posts"]:
        if p["slug"] == current or p["slug"] not in nights:
            continue                       # occ-* и прочие не-«ночи» страниц не имеют
        n = nights[p["slug"]]
        cells.append(
            f'      <a href="night-{p["slug"]}.html"><figure>'
            f'<img src="assets/social/{p["image_file"]}" alt="{esc(p["pin_title"])}" loading="lazy">'
            f'<div class="d">{nice_date(n["render"]["date"])}</div>'
            f'<figcaption>{esc(p["caption_on_image"])}</figcaption></figure></a>')
    return "\n".join(cells)


def night_page(p):
    slug = p["slug"]
    n = nights[slug]["render"]
    date_h = nice_date(n["date"])
    img = f'assets/social/{p["image_file"]}'
    vid = f'assets/social/video/{p["video_file"]}'
    ft, fc = FRAME.get(n["theme"], ("classic", "black"))
    preset = dict(dateStr=n["date"], timeStr=n["time"], place=n["place"],
                  lat=n["lat"], lon=n["lon"], iana=IANA[slug],
                  dedication=n["dedication"], theme=n["theme"],
                  frameType=ft, size="3040", frameColor=fc)
    title = f'{p["pin_title"]} · Sky, That Night'
    desc = p["pin_desc"][:158].rsplit(" ", 1)[0] + "…" if len(p["pin_desc"]) > 160 else p["pin_desc"]
    schema = ('<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": p["pin_title"], "description": desc,
        "image": f'{BASE}/{img}', "datePublished": "2026-07-30",
        "author": {"@type": "Organization", "name": "Sky, That Night"},
    }, ensure_ascii=False) + "</script>")

    return head(title, desc, f"night-{slug}.html", f"{BASE}/{img}", schema, preload=img) + f"""
{HEADER}

<main>

<section class="fn-hero">
  <div class="sm-stars" aria-hidden="true"></div>
  <div class="container">
    <div>
      <a class="fn-back" href="famous-nights.html">← All famous nights</a>
      <div class="fn-kicker">Famous Nights · {date_h}</div>
      <h1 class="fn-h1">{esc(p["pin_title"])}</h1>
      <p class="fn-quote">«{esc(p["caption_on_image"])}»</p>
      <p class="fn-story">{esc(p["pin_desc"])}</p>
      <p class="fn-facts"><b>{esc(n["place"])}</b> · {date_h} · {n["time"]} local · {coords(n["lat"], n["lon"])}</p>
      <a class="sm-cta" href="#design">Now map your own night — from £26.99</a>
      <span class="sm-cta-sub">The configurator below is already set to this sky. Change the date to yours.</span>
    </div>
    <div>
      <img src="{img}" alt="{esc(p["pin_title"])} — star map art print">
    </div>
  </div>
</section>

<section class="sm-section fn-film" id="film">
  <div class="container">
    <div class="section-kicker sm-kicker">The short film</div>
    <h2>Eight seconds over {esc(n["place"].split(",")[0])}.</h2>
    <video controls playsinline preload="none" poster="{img}" src="{vid}"></video>
    <p class="fn-ai">The era scene is an AI reconstruction. The sky above it is not — every star is computed
    from astronomical data for {date_h}, {n["time"]} local time.</p>
  </div>
</section>

{CONFIG}

<section class="sm-section">
  <div class="container">
    <div class="section-kicker sm-kicker">Keep exploring</div>
    <h2>Other famous nights.</h2>
    <div class="fn-grid">
{others_grid(slug)}
    </div>
  </div>
</section>

</main>

{FOOTER}

<script>window.SM_PRESET = {json.dumps(preset)};</script>
<script>
/* Автозапуск фильма по докрутке: без звука, лупом, пауза при уходе из вида.
   Уважаем reduced-motion; как только зритель сам включил звук или перемотал —
   больше не вмешиваемся (userTouched). preload="none" → трафик идёт только
   когда секция реально доехала до экрана.
   ⚠️pending-защёлка обязательна: pause() во время неразрешённого play() даёт
   AbortError и глушит видео насовсем (поймано при проверке 30.07). Порог 0.35 —
   на низких ландшафтных экранах половина высокого 9:16 не помещается никогда. */
(function () {{
  var v = document.querySelector('.fn-film video');
  if (!v || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var pending = false;
  function outOfView() {{
    var r = v.getBoundingClientRect();
    var vis = Math.min(r.bottom, innerHeight) - Math.max(r.top, 0);
    return vis < r.height * 0.35;
  }}
  function enter() {{
    if (v.dataset.userTouched || pending || !v.paused) return;
    pending = true; v.muted = true; v.loop = true;
    var p = v.play();
    if (p && p.then) p.then(function () {{
      pending = false; if (outOfView()) v.pause();   // успел уехать, пока грузилось
    }}).catch(function () {{ pending = false; }});
    else pending = false;
  }}
  function leave() {{
    if (v.dataset.userTouched || pending || v.paused) return;
    v.pause();
  }}
  var io = new IntersectionObserver(function (es) {{
    es.forEach(function (e) {{ (e.isIntersecting ? enter : leave)(); }});
  }}, {{ threshold: 0.35 }});
  io.observe(v);
  v.addEventListener('volumechange', function () {{
    if (!v.muted) {{ v.dataset.userTouched = 1; v.loop = false; }}
  }});
  v.addEventListener('seeking', function () {{ v.dataset.userTouched = 1; }});
}})();
</script>
<script src="assets/starmap.js?v=14" defer></script>
</body>
</html>
"""


def hub_page():
    cells = []
    for p in plan["posts"]:
        if p["slug"] not in nights:      # occ-* постам страниц не делаем (см. main)
            continue
        n = nights[p["slug"]]["render"]
        cells.append(
            f'      <a href="night-{p["slug"]}.html"><figure>'
            f'<img src="assets/social/{p["image_file"]}" alt="{esc(p["pin_title"])}" loading="lazy">'
            f'<div class="d">{nice_date(n["date"])} · {esc(n["place"].split(",")[0])}</div>'
            f'<figcaption>«{esc(p["caption_on_image"])}»</figcaption></figure></a>')
    grid = "\n".join(cells)
    title = "Famous Nights — the real sky over history's great evenings · Sky, That Night"
    desc = ("The royal wedding, the 1966 World Cup, the night the Berlin Wall opened — the real night sky "
            "over each, computed from astronomical data and printed as art. Then map your own night.")
    ogimg = f'{BASE}/assets/social/{plan["posts"][0]["image_file"]}'
    schema = ('<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "Famous Nights",
        "itemListElement": [{"@type": "ListItem", "position": i + 1,
                             "url": f'{BASE}/night-{p["slug"]}.html'}
                            for i, p in enumerate(plan["posts"])],
    }) + "</script>")
    return head(title, desc, "famous-nights.html", ogimg, schema) + f"""
{HEADER}

<main>

<section class="fn-hero">
  <div class="sm-stars" aria-hidden="true"></div>
  <div class="container" style="grid-template-columns:1fr">
    <div>
      <div class="fn-kicker">Famous Nights</div>
      <h1 class="fn-h1">The sky remembers every night.</h1>
      <p class="fn-story" style="max-width:44rem">Some evenings the whole world was looking the same way —
      and above every one of them stood a sky nobody thought to keep. We compute those skies from real
      astronomical data, set them over a scene from that era, and print them as art. Eleven nights so far,
      from a caravel in 1492 to the minute the century turned. And below each one — the same tools,
      ready to map <em>your</em> night.</p>
      <a class="sm-cta" href="./#design">Map your own night — from £26.99</a>
      <span class="sm-cta-sub">Free UK delivery included · dispatched in 2–4 working days</span>
    </div>
  </div>
</section>

<section class="sm-section">
  <div class="container">
    <div class="fn-hub-grid fn-grid" style="grid-template-columns:repeat(3,1fr)">
{grid}
    </div>
  </div>
</section>

</main>

{FOOTER}
</body>
</html>
"""


def main():
    # ⚠️ В плане постинга живут не только «ночи», но и occasion-посты (occ-wedding,
    # occ-born…) — у них нет записи в famous_nights.json. Раньше цикл падал на первом
    # таком слаге с KeyError, и ВСЕ страницы после него (включая gertrude-ederle) не
    # создавались молча — пины ссылались бы на 404 (найдено 06.08.2026).
    skipped = []
    for p in plan["posts"]:
        if p["slug"] not in nights:
            skipped.append(p["slug"])
            continue
        fn = f'night-{p["slug"]}.html'
        open(os.path.join(HERE, fn), "w").write(night_page(p))
        print("wrote", fn)
    if skipped:
        print("· без страницы (нет в famous_nights.json):", ", ".join(skipped))
    open(os.path.join(HERE, "famous-nights.html"), "w").write(hub_page())
    print("wrote famous-nights.html")


if __name__ == "__main__":
    main()
