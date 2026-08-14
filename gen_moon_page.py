#!/usr/bin/env python3
"""Генерирует moon.html — страницу «The Moon That Night» — из index.html как шаблона.

Второй продукт сайта (04.08.2026): портрет настоящей Луны (фото NASA GSFC/LRO) в фазе
заказанной ночи. Конфигуратор = assets/moon.js (сестра starmap.js, дизайн-код MN2-…,
Stripe-линки и цены ОБЩИЕ со звёздным постером). Печать: fulfil.py различает SM2/MN2
и зовёт render_moon_poster.

⚠️ Шаблон — ЖИВОЙ index.html: правки главной сами приезжают сюда при перегенерации.
Запуск:  python3 gen_moon_page.py   (перегенерировать после любой правки index.html)
В конце сам вшивает аналитик-beacon через gen_analytics.inject (канон сайта).
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "index.html"
DST = HERE / "moon.html"

MOON_JS_V = "v=2"


def cut_section(html, marker):
    """Вырезать целиком <section>…</section>, содержащую маркер.
    ⚠️ Если маркер САМ начинается с '<section', наивный rfind(0, i) берёт ПРЕДЫДУЩУЮ
    секцию. И тонкость Python: rfind(sub, 0, end) требует, чтобы sub ЦЕЛИКОМ влезла
    в срез — конец диапазона должен быть i + len('<section'), не i+1 (гоча 04.08)."""
    i = html.find(marker)
    if i < 0:
        raise SystemExit(f"маркер не найден: {marker}")
    start = html.rfind("<section", 0, i + len("<section"))
    end = html.find("</section>", i) + len("</section>")
    return html[:start] + html[end:], html[start:end]


def main():
    h = SRC.read_text()

    # ── head ──
    h = h.replace(
        "<title>Sky, That Night — Custom Star Maps of Your Exact Sky</title>",
        "<title>The Moon That Night — Custom Moon Phase Print of Your Date | Sky, That Night</title>")
    h = h.replace(
        '<meta name="description" content="A museum-grade star map of the exact sky above any place on any date — real astronomy, 11,000 stars, the true moon phase of your night. Framed or print, from £26.99 with free UK delivery.">',
        '<meta name="description" content="A museum-grade portrait of the real Moon exactly as it hung on your night — true phase from NASA imagery, personalised with your words, date and place. Framed or print, from £26.99 with free UK delivery.">')
    h = h.replace('<link rel="canonical" href="https://www.skythatnight.com/">',
                  '<link rel="canonical" href="https://www.skythatnight.com/moon.html">')
    h = h.replace('<meta property="og:title" content="Sky, That Night — Custom Star Maps">',
                  '<meta property="og:title" content="The Moon That Night — Custom Moon Phase Print">')
    h = h.replace('<meta property="og:description" content="The exact sky above any place, on any date. Real astronomy, museum-grade print, from £26.99.">',
                  '<meta property="og:description" content="The real Moon of your night — true phase, NASA imagery, museum-grade print, from £26.99.">')
    h = h.replace('<meta property="og:url" content="https://www.skythatnight.com/">',
                  '<meta property="og:url" content="https://www.skythatnight.com/moon.html">')
    h = h.replace('<meta property="og:image" content="https://www.skythatnight.com/assets/starmap/og-lifestyle.jpg">',
                  '<meta property="og:image" content="https://www.skythatnight.com/assets/starmap/hero-moon.jpg">')
    h = h.replace('<link rel="preload" as="image" href="assets/starmap/hero-midnight.jpg">',
                  '<link rel="preload" as="image" href="assets/starmap/hero-moon.jpg">')

    # ── JSON-LD ──
    h = re.sub(
        r'\{"@context":"https://schema\.org","@type":"Product".*?\}\n</script>',
        ('{"@context":"https://schema.org","@type":"Product","name":"Custom Moon Phase Print",'
         '"description":"Personalised portrait of the real Moon in its true phase for any date — '
         'NASA imagery, museum-grade giclée print, optional handmade frame.",'
         '"image":"https://www.skythatnight.com/assets/starmap/hero-moon.jpg","sku":"moon-print",'
         '"brand":{"@type":"Brand","name":"Sky, That Night"},'
         '"offers":{"@type":"AggregateOffer","lowPrice":"26.99","highPrice":"79.99",'
         '"priceCurrency":"GBP","availability":"https://schema.org/InStock",'
         '"url":"https://www.skythatnight.com/moon.html"}}\n</script>'),
        h, count=1, flags=re.S)

    # ── hero ──
    hero_new = '''<section class="sm-hero">
  <div class="sm-stars" aria-hidden="true"></div>
  <div class="container">
    <div>
      <div class="sm-kicker sm-reveal">The Atelier · Personalised</div>
      <h1 class="sm-h1 sm-reveal">The moon that watched<br><em>your night.</em></h1>
      <p class="sm-lede sm-reveal">Full, new, or the exact crescent in between — the Moon as it truly hung
      over your date, rendered from NASA imagery with its real phase computed to the minute.
      Printed at museum grade in the UK, framed by hand.</p>
      <a class="sm-cta" href="#design">Design yours — from £26.99</a>
      <span class="sm-cta-sub">Free UK delivery included · dispatched in 2–4 working days</span>
    </div>
    <div class="sm-fan" aria-hidden="true">
      <img src="assets/starmap/moon-porcelain.jpg" alt="" loading="lazy">
      <img src="assets/starmap/hero-moon.jpg" alt="Custom moon phase poster, midnight theme">
      <img src="assets/starmap/moon-crescent.jpg" alt="" loading="lazy">
    </div>
  </div>
</section>'''
    h, _old_hero = cut_section(h, 'class="sm-hero"')
    h = h.replace("<main>\n", "<main>\n\n" + hero_new + "\n", 1)

    # ── конфигуратор: табы (в шаблоне активен Star Map — переключаем актив), заголовок ──
    h = h.replace(
        '''<a class="sm-prodtab active" href="#design" aria-current="page">✦ Star Map</a>
        <a class="sm-prodtab" href="moon.html#design">☾ The Moon</a>''',
        '''<a class="sm-prodtab" href="./#design">✦ Star Map</a>
        <a class="sm-prodtab active" href="moon.html#design" aria-current="page">☾ The Moon</a>''')
    h = h.replace("<h2>Your sky.</h2>", "<h2>Your moon.</h2>")
    h = h.replace('placeholder="e.g. Eliana Grace · The night we met"',
                  'placeholder="e.g. Rachel &amp; Tom · The moon that night"')
    h = h.replace(">Buy this sky<", ">Buy this moon<")

    # ── craft-тексты ──
    h = h.replace("<h2>Not an illustration.<br>An astronomical record.</h2>",
                  "<h2>Not clip-art.<br>The actual Moon.</h2>")
    h = h.replace(
        "<h3>Real astronomy</h3>\n        <p>Your sky is computed from professional star catalogues — over 11,000 stars placed exactly\n        where they stood above your place, at your minute. The Milky Way included on print.</p>",
        "<h3>NASA imagery</h3>\n        <p>The lunar disc is a real photographic mosaic from NASA's Lunar Reconnaissance Orbiter —\n        every mare and crater where it belongs, printed with museum-grade fidelity.</p>")
    h = h.replace(
        "<p>Every map carries the true phase of the moon for your date — full, new, or the exact\n        crescent in between. A detail almost nobody else gets right.</p>",
        "<p>The phase is computed for your exact date, time and timezone — full, new, or the precise\n        crescent in between, with the soft terminator falling exactly where it did that night.</p>")

    # ── вырезать звёздные секции ──
    # ⚠️ Маркеры — УНИКАЛЬНЫЕ куски РАЗМЕТКИ: короткое "sm-film" совпадало с CSS-классом
    # в <style> и cut_section резал от несуществующего <section (гоча первой генерации).
    for marker in ('src="assets/starmap/skythatnight-film.mp4',
                   '<section class="sm-section" id="moods">',
                   '<section class="sm-section" id="frames">',
                   '<section class="sm-section" id="occasions">',
                   '<section class="sm-section" id="famous">'):
        h, _ = cut_section(h, marker)

    # ── галерея тем + кросс-селл (на место перед FAQ) ──
    insert = '''<section class="sm-section" id="moods">
  <div class="container">
    <div class="section-kicker sm-kicker">Moods</div>
    <h2>One moon, many nights.</h2>
    <div class="sm-gallery-grid">
      <figure><img src="assets/starmap/hero-moon.jpg" alt="Full moon poster, midnight theme" loading="lazy"><figcaption>Midnight · full moon</figcaption></figure>
      <figure><img src="assets/starmap/moon-crescent.jpg" alt="Waxing crescent moon poster" loading="lazy"><figcaption>Midnight · waxing crescent</figcaption></figure>
      <figure><img src="assets/starmap/moon-porcelain.jpg" alt="Porcelain duotone moon poster" loading="lazy"><figcaption>Porcelain · engraving duotone</figcaption></figure>
      <figure><img src="assets/starmap/moon-noir.jpg" alt="Noir gold moon poster" loading="lazy"><figcaption>Noir · gold on black</figcaption></figure>
    </div>
  </div>
</section>

<section class="sm-section" id="pair">
  <div class="container">
    <div class="section-kicker sm-kicker">Make it a pair</div>
    <h2>The stars were there too.</h2>
    <div class="sm-craft-grid">
      <div>
        <h3>✦ The Star Map</h3>
        <p>Eleven thousand stars exactly where they stood above your place, at your minute —
        our original piece, and the moon's perfect companion on the wall.</p>
        <p><a class="sm-cta" href="./#design" style="margin-top:.6rem;display:inline-block;">Design the sky of the same night</a></p>
      </div>
      <div>
        <h3>☾ + ✦ Side by side</h3>
        <p>Same night, two portraits: the whole sky and its brightest character. Order both in the
        same theme and size — they hang as a diptych.</p>
      </div>
      <div>
        <h3>The same craft</h3>
        <p>Identical paper, inks, frames and sizes across both pieces — museum-grade giclée,
        handmade UK frames, free delivery.</p>
      </div>
    </div>
  </div>
</section>

'''
    faq_i = h.find('<section class="sm-section sm-faq"')
    h = h[:faq_i] + insert + h[faq_i:]

    # ── FAQ: первый вопрос — лунный ──
    h = h.replace(
        "<summary>How accurate is the sky?</summary>\n      <p>Genuinely accurate. We compute the position of every star from professional astronomical\n      catalogues for your exact date, time and coordinates — the same mathematics observatories use.\n      Rotate the map to your date of birth and an astronomer would recognise the sky.</p>",
        "<summary>Is it really the moon of my date?</summary>\n      <p>Yes. We compute the lunar phase for your exact date, time and timezone with the same\n      astronomical formulae used across our star maps, and render it over a NASA Lunar\n      Reconnaissance Orbiter photographic mosaic — the terminator falls exactly where it did.</p>")

    # ── скрипты ──
    h = re.sub(r'<script src="assets/starmap\.js\?v=\d+" defer></script>',
               f'<script src="assets/moon.js?{MOON_JS_V}" defer></script>', h)

    DST.write_text(h)
    print(f"✓ {DST.name} ({DST.stat().st_size // 1024}KB)")

    import gen_analytics
    gen_analytics.inject(True)


if __name__ == "__main__":
    main()
