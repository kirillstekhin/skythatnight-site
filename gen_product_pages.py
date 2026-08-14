#!/usr/bin/env python3
"""Страницы товаров: 9 лендингов матрицы 3×3 (Print/Framed/Classic × 30×40/40×50/50×70).

ЗАЧЕМ (06.08.2026, после бана Merchant Center за Misrepresentation).
Все 9 позиций фида вели на ОДНУ ссылку — главную, а главная объявляет
`AggregateOffer` 26.99–79.99. Робот брал из фида «SKN-FRAMED-5070 = £59.99», шёл по
ссылке и не находил там товара за £59.99 — несовпадение по всем девяти позициям
сразу, ровно пункт чеклиста «match your product data with your online store».

Теперь у каждой позиции свой лендинг: цена ВИДНА человеку и объявлена в Product
JSON-LD одним и тем же числом. Ссылки фида переводятся сюда (gen_product_feed.py).

⚠️ ЕДИНСТВЕННЫЙ ИСТОЧНИК ЦЕН — ITEMS из gen_product_feed.py, который в свою очередь
сверен с PRICES конфигуратора (assets/starmap.js). Никаких цен руками в этом файле:
иначе почини одно — сломаешь другое, а именно за расхождение цен нас и забанили.
Сверка конфигуратора выполняется при каждом запуске и падает при расхождении.

    python3 gen_product_pages.py     # из site/ → product-<id>.html × 9
"""
import html
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://www.skythatnight.com"
idx = open(os.path.join(HERE, "index.html")).read()

STYLE = re.search(r"<style>(.*?)</style>", idx, re.S).group(1)
CONFIG = re.search(r'(<section class="sm-config" id="design">.*?</section>)', idx, re.S).group(1)
CACHE = "v=20"

_spec = importlib.util.spec_from_file_location("feed", os.path.join(HERE, "gen_product_feed.py"))
_feed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_feed)          # ⚠ побочно перегенерит feed.xml — так и надо: цены едины
ITEMS = _feed.ITEMS

# ═══ ДВА ПРОДУКТА, ОДНА ГРАММАТИКА СТРАНИЦЫ (11.08.2026) ═══
# У луны своя секция конфигуратора (moon.html + moon.js + пресет MN_PRESET) и свои кадры,
# но лендинг обязан быть устроен ТАК ЖЕ: видимая цена = цена фида = цена в Product JSON-LD.
# Иначе повторяется бан 05.08 — только теперь по девяти лунным позициям.
_moon_html = open(os.path.join(HERE, "moon.html")).read()

PRODUCTS = {
    "star": dict(
        items=ITEMS,
        config=CONFIG,
        script="starmap.js", preset_var="SM_PRESET", cache=CACHE,
        kind="Star Map",
        h1=lambda size: f"Your exact night sky, {size.replace(' cm', ' centimetres')}",
        blurb="Every star in its true position for the date, time and place you choose — "
              "11,000 stars, real constellations and the actual moon phase of your night.",
        jsonld_desc="A museum-grade star map of the exact sky above any place, on any date.",
        others_title="Nine ways to hang the same night.",
        cta="Design this sky"),
    "moon": dict(
        items=_feed.MOON_ITEMS,
        config=re.search(r'(<section class="sm-config" id="design">.*?</section>)', _moon_html, re.S).group(1),
        # ⚠ версию кэша НЕ хардкодим: она живёт в moon.html (его пишет gen_moon_page.py).
        # Разъедется — лунные лендинги отдадут СТАРЫЙ moon.js, и фикс до них не доедет.
        script="moon.js", preset_var="MN_PRESET",
        cache=re.search(r"moon\.js\?(v=\d+)", _moon_html).group(1),
        kind="Moon Phase Print",
        h1=lambda size: f"The Moon of your night, {size.replace(' cm', ' centimetres')}",
        blurb="The real Moon in the true phase of your date — rendered from NASA lunar "
              "photography, not drawn. Your words, your date, your place beneath it.",
        jsonld_desc="A museum-grade portrait of the real Moon in the true phase of your night.",
        others_title="Nine ways to hang the same moon.",
        cta="Design this moon"),
}

# формат из фида → ключ конфигуратора (frameType) и человеческое описание
FMT = {
    "Print":         dict(key="print",   what="Museum-grade giclée print, shipped rolled in a protective tube.",
                          incl=["Giclée print on 200 gsm archival matte paper",
                                "Rolled in tissue inside a rigid tube",
                                "No frame — ready for your own"]),
    "Framed":        dict(key="framed",  what="Handmade wood frame in white or natural oak, ready to hang.",
                          incl=["Giclée print on 200 gsm archival matte paper",
                                "Handmade wood frame, white or natural oak",
                                "Shatterproof glazing, hanging hardware fitted"]),
    "Classic Frame": dict(key="classic", what="Gallery frame in black, antique gold or antique silver.",
                          incl=["Giclée print on 200 gsm archival matte paper",
                                "Gallery frame: black, antique gold or antique silver",
                                "Shatterproof glazing, hanging hardware fitted"]),
}
SIZEKEY = {"30×40 cm": "3040", "40×50 cm": "4050", "50×70 cm": "5070"}

HEADER = re.search(r"(<header>.*?</header>)", idx, re.S).group(1)
FOOTER = re.search(r"(<footer>.*?</footer>)", idx, re.S).group(1)

EXTRA_CSS = """
.pp-hero { padding: clamp(2rem,5vw,4rem) 0; }
.pp-hero .container { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:clamp(2rem,4vw,3.5rem); align-items:center; }
@media (max-width:900px){ .pp-hero .container { grid-template-columns:1fr; } }
.pp-hero img { width:100%; height:auto; display:block; border-radius:4px;
  box-shadow:0 30px 80px rgba(0,0,0,.6), 0 0 0 1px rgba(201,169,97,.14); }
.pp-kicker { font-family:var(--sans); font-size:.78rem; letter-spacing:.32em; text-transform:uppercase; color:var(--gold); margin-bottom:1rem; }
.pp-h1 { font-family:var(--serif); font-weight:500; font-size:clamp(2rem,4vw,3rem); line-height:1.1; color:var(--moon); margin:0 0 1rem; }
.pp-price { font-family:var(--serif); font-size:clamp(1.8rem,3vw,2.4rem); color:var(--gold); margin:0 0 .4rem; }
.pp-avail { font-family:var(--sans); font-size:.85rem; color:var(--moon-sub); margin:0 0 1.6rem; }
.pp-what { font-family:var(--sans); font-weight:300; font-size:1.02rem; line-height:1.7; color:var(--moon-sub); max-width:34rem; margin:0 0 1.4rem; }
.pp-incl { list-style:none; padding:0; margin:0 0 2rem; }
.pp-incl li { font-family:var(--sans); font-weight:300; font-size:.95rem; line-height:1.6; color:var(--moon-sub); padding-left:1.4rem; position:relative; margin-bottom:.5rem; }
.pp-incl li::before { content:'✦'; position:absolute; left:0; color:var(--gold); font-size:.8rem; }
.pp-others { display:grid; grid-template-columns:repeat(3,1fr); gap:.9rem; margin-top:1.6rem; }
@media (max-width:640px){ .pp-others { grid-template-columns:1fr; } }
.pp-others a { display:block; padding:.9rem 1rem; border:1px solid rgba(201,169,97,.25); border-radius:3px;
  font-family:var(--sans); font-size:.9rem; color:var(--moon-sub); text-decoration:none; }
.pp-others a:hover { border-color:var(--gold); color:var(--moon); }
.pp-others .pp-o-price { color:var(--gold); }
"""


def esc(s):
    return html.escape(str(s), quote=True)


def check_configurator_prices():
    """Цены страниц ОБЯЗАНЫ совпадать с конфигуратором — за расхождение и был бан."""
    js = open(os.path.join(HERE, "assets", "starmap.js")).read()
    raw = re.search(r"const PRICES = (\{.*?\});", js, re.S).group(1)
    cfg = {}
    for fmt, body in re.findall(r"(\w+):\s*\{([^}]*)\}", raw):
        cfg[fmt] = {k: float(v) for k, v in re.findall(r"'(\d+)':\s*([\d.]+)", body)}
    bad = []
    for pid, fmt, size, price, _ in ITEMS:
        want = cfg[FMT[fmt]["key"]][SIZEKEY[size]]
        if abs(want - price) >= 0.005:
            bad.append(f"{pid}: фид {price:.2f} ≠ конфигуратор {want:.2f}")
    if bad:
        raise SystemExit("⛔ цены разошлись с конфигуратором:\n  " + "\n  ".join(bad))
    print(f"✓ цены сверены с конфигуратором: {len(ITEMS)}/{len(ITEMS)}")


def jsonld(prod, pid, fmt, size, price, url, img):
    """Product с ОДНОЙ ценой — не AggregateOffer. Робот сверяет её с фидом.

    ⚠ ВОЗВРАТ: `MerchantReturnNotPermitted`, а НЕ 14 дней. Первая версия этих страниц
    объявляла FiniteReturnWindow/14/FreeReturn, хотя delivery.html и FAQ главной прямо
    говорят обратное: персонализированные товары освобождены от 14-дневного права на
    отказ (Consumer Contracts Regulations 2013). Робот, сверяющий заявления с политикой
    магазина, увидел бы ровно то, за что нас и забанили, — только вторым пунктом.
    Права на брак/повреждение (30 дней на отказ, репринт/возврат) сюда не входят:
    returnPolicyCategory описывает отказ по передумал, законные права он не отменяет."""
    P = PRODUCTS[prod]
    return f"""<script type="application/ld+json">{{
"@context":"https://schema.org","@type":"Product",
"name":"Personalised {P['kind']} — {fmt} {size}",
"sku":"{pid}","mpn":"{pid}","brand":{{"@type":"Brand","name":"Sky, That Night"}},
"image":"{img}","url":"{url}",
"description":"{esc(P['jsonld_desc'])} {esc(FMT[fmt]['what'])}",
"offers":{{"@type":"Offer","price":"{price:.2f}","priceCurrency":"GBP",
"availability":"https://schema.org/InStock","itemCondition":"https://schema.org/NewCondition",
"url":"{url}","priceValidUntil":"2027-12-31",
"seller":{{"@type":"Organization","name":"Shopcienty Limited"}},
"shippingDetails":{{"@type":"OfferShippingDetails",
"shippingRate":{{"@type":"MonetaryAmount","value":"0","currency":"GBP"}},
"shippingDestination":{{"@type":"DefinedRegion","addressCountry":"GB"}}}},
"hasMerchantReturnPolicy":{{"@type":"MerchantReturnPolicy",
"applicableCountry":"GB","returnPolicyCategory":"https://schema.org/MerchantReturnNotPermitted",
"merchantReturnLink":"{SITE}/delivery.html"}}}}}}</script>"""


def others_html(prod, cur_id):
    cells = []
    for pid, fmt, size, price, _ in PRODUCTS[prod]["items"]:
        if pid == cur_id:
            continue
        cells.append(f'      <a href="product-{pid.lower()}.html">{esc(fmt)} · {esc(size)}<br>'
                     f'<span class="pp-o-price">£{price:.2f}</span></a>')
    return "\n".join(cells)


def build(prod, pid, fmt, size, price, extra):
    P = PRODUCTS[prod]
    slug = f"product-{pid.lower()}.html"
    url = f"{SITE}/{slug}"
    img = f"{SITE}/assets/starmap/feed/{pid}.jpg"
    info = FMT[fmt]
    title = f"Personalised {P['kind']} — {fmt} {size} — £{price:.2f}"
    subject = ("moon phase print showing the true phase of any date and place"
               if prod == "moon" else
               "star map of the exact sky above any place on any date")
    desc = (f"{fmt} {size} personalised {subject}. "
            f"£{price:.2f} including free UK delivery. Made to order in the UK.")
    incl = "\n".join(f"        <li>{esc(x)}</li>" for x in info["incl"])
    preset = f'{{"frameType":"{info["key"]}","size":"{SIZEKEY[size]}"}}'

    return slug, f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Sky, That Night</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="product">
<meta property="og:site_name" content="Sky, That Night">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="assets/favicon.png?v=2">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Hanken+Grotesk:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css?v=2">
<link rel="preload" as="image" href="assets/starmap/feed/{pid}.jpg">
<style>{STYLE}{EXTRA_CSS}</style>
{jsonld(prod, pid, fmt, size, price, url, img)}
</head>
<body class="sm-night">
{HEADER}

<main>

<section class="pp-hero">
  <div class="sm-stars" aria-hidden="true"></div>
  <div class="container">
    <div>
      <div class="pp-kicker">{esc(fmt)} · {esc(size)}</div>
      <h1 class="pp-h1">{esc(P['h1'](size))}</h1>
      <p class="pp-price">£{price:.2f}</p>
      <p class="pp-avail">In stock · free UK delivery · made to order, dispatched in 2–4 working days</p>
      <p class="pp-what">{esc(info['what'])} {esc(P['blurb'])}</p>
      <ul class="pp-incl">
{incl}
      </ul>
      <a class="sm-cta" href="#design">{esc(P['cta'])} — £{price:.2f}</a>
      <span class="sm-cta-sub">Free UK delivery included · personalised, so no change-of-mind returns — damaged or not as approved, we reprint or refund in full · <a href="delivery.html">Delivery &amp; returns</a></span>
    </div>
    <div>
      <img src="assets/starmap/feed/{pid}.jpg" alt="{esc(fmt)} {esc(size)} personalised {esc(P['kind'].lower())}, £{price:.2f}">
    </div>
  </div>
</section>

{P['config']}

<section class="sm-section">
  <div class="container">
    <div class="section-kicker sm-kicker">Other sizes and finishes</div>
    <h2>{esc(P['others_title'])}</h2>
    <div class="pp-others">
{others_html(prod, pid)}
    </div>
  </div>
</section>

</main>

{FOOTER}
<script>window.{P['preset_var']} = {preset};</script>
<script src="assets/{P['script']}?{P['cache']}" defer></script>
</body>
</html>
"""


GRID_START = "<!-- SM_PRICE_GRID:START"
GRID_END = "<!-- SM_PRICE_GRID:END -->"


def update_index():
    """Сетка цен в секции #prices главной — из тех же ITEMS.

    ⚠ Без ссылок с главной девять лендингов были бы сиротами: в sitemap есть, а во
    внутренней перелинковке нет — краулер до них доходит медленно и неохотно, а нам
    нужно, чтобы он увидел цены как можно раньше. Разметка ГЕНЕРИТСЯ, а не живёт
    руками, ровно по причине бана: цена на главной, в фиде и на лендинге — одно число
    из одного источника."""
    p = os.path.join(HERE, "index.html")
    s = open(p).read()
    i, j = s.find(GRID_START), s.find(GRID_END)
    if i < 0 or j < 0:
        raise SystemExit(f"⛔ в index.html нет маркеров {GRID_START}…{GRID_END}")
    cells = "\n".join(
        f'      <a class="sm-pg-cell" href="product-{pid.lower()}.html">'
        f'<span class="sm-pg-fmt">{esc(fmt)}</span>'
        f'<span class="sm-pg-size">{esc(size)}</span>'
        f'<span class="sm-pg-price">£{price:.2f}</span></a>'
        for pid, fmt, size, price, _ in ITEMS)
    grid = (f'{GRID_START} — генерится gen_product_pages.py из ITEMS фида, РУКАМИ НЕ ПРАВИТЬ.\n'
            f'         Цена здесь обязана совпадать с фидом и страницей товара: за расхождение\n'
            f'         Merchant Center выдал Misrepresentation 05.08.2026. -->\n'
            f'    <div class="sm-pricegrid">\n{cells}\n    </div>\n    ')
    s = s[:i] + grid + s[j:]

    # ⚠ Главная объявляет AggregateOffer с диапазоном — он ОБЯЗАН быть краями той же
    # матрицы. Разъедется (подняли цену рамки, забыли главную) — и это ровно тот же
    # Misrepresentation, только уже на главной. Тянем из ITEMS, руками не держим.
    lo, hi = min(x[3] for x in ITEMS), max(x[3] for x in ITEMS)
    s, n = re.subn(r'("lowPrice":")[\d.]+(","highPrice":")[\d.]+(")',
                   lambda m: f"{m.group(1)}{lo:.2f}{m.group(2)}{hi:.2f}{m.group(3)}", s)
    if n != 1:
        raise SystemExit(f"⛔ AggregateOffer на главной не найден (совпадений {n})")
    open(p, "w").write(s)
    print(f"✓ сетка цен на главной обновлена: {len(ITEMS)} ссылок; "
          f"диапазон AggregateOffer £{lo:.2f}–£{hi:.2f}")


def main():
    check_configurator_prices()
    written = []
    for prod, P in PRODUCTS.items():
        for pid, fmt, size, price, extra in P["items"]:
            slug, page = build(prod, pid, fmt, size, price, extra)
            open(os.path.join(HERE, slug), "w").write(page)
            written.append((prod, slug, price))
    update_index()
    _reinject()
    print(f"✅ страниц товаров: {len(written)}")
    for prod, slug, price in written:
        print(f"   [{prod:4}] {slug:38} £{price:.2f}")


def _reinject():
    """Новые страницы рождаются БЕЗ счётчика и без Google-тега — вернуть сразу.

    ⚠ Мина 02.08 (аналитика) и 11.08 (gtag): свежесгенерированный лендинг без тега
    молча не считает конверсии, и в кабинете Google это выглядит как «реклама не
    работает», хотя заказы идут.
    """
    for name in ("gen_analytics", "gen_gtag"):
        sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, f"{name}.py"))
        mod = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(mod)
        mod.inject(True)


if __name__ == "__main__":
    main()
