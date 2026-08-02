#!/usr/bin/env python3
"""Продуктовый фид (RSS 2.0 + g: namespace) для Google Merchant Center И Pinterest Catalogs.
9 позиций = матрица 3×3 (Print/Framed/Classic × 30x40/40x50/50x70), цены = PRICES
конфигуратора (VAT-incl). Кастом-товар без GTIN → identifier_exists=no.
Оба канала едят один формат; отличие ТОЛЬКО в UTM ссылки → два файла, чтобы
атрибуция в аналитике не слипалась.
Запуск: python3 gen_product_feed.py  (из site/) → feed.xml + feed-pinterest.xml, потом коммит."""
import html
from datetime import date

SITE = "https://www.skythatnight.com"
FEEDS = [
    ("feed.xml", SITE + "/?utm_source=google&utm_medium=shopping"),
    ("feed-pinterest.xml", SITE + "/?utm_source=pinterest&utm_medium=shopping"),
]

# (id, формат, размер, цена, доп-описание формата)
# Картинка НЕ задаётся здесь: у каждой позиции свой квадрат 1600×1600 по имени id,
# генерится `tools/make_feed_images.py` → assets/starmap/feed/<id>.jpg (см. его шапку про
# «почему квадрат» и «почему у каждой позиции свой кадр»).
ITEMS = [
    ("SKN-PRINT-3040",   "Print",         "30×40 cm", 26.99, "museum-grade giclée print, shipped rolled"),
    ("SKN-PRINT-4050",   "Print",         "40×50 cm", 29.99, "museum-grade giclée print, shipped rolled"),
    ("SKN-PRINT-5070",   "Print",         "50×70 cm", 32.99, "museum-grade giclée print, shipped rolled"),
    ("SKN-FRAMED-3040",  "Framed",        "30×40 cm", 44.99, "handmade wood frame (white or natural), ready to hang"),
    ("SKN-FRAMED-4050",  "Framed",        "40×50 cm", 52.99, "handmade wood frame (white or natural), ready to hang"),
    ("SKN-FRAMED-5070",  "Framed",        "50×70 cm", 59.99, "handmade wood frame (white or natural), ready to hang"),
    ("SKN-CLASSIC-3040", "Classic Frame", "30×40 cm", 59.99, "gallery classic frame in black, antique gold or antique silver"),
    ("SKN-CLASSIC-4050", "Classic Frame", "40×50 cm", 69.99, "gallery classic frame in black, antique gold or antique silver"),
    ("SKN-CLASSIC-5070", "Classic Frame", "50×70 cm", 79.99, "gallery classic frame in black, antique gold or antique silver"),
]

DESC = ("A museum-grade star map of the exact sky above any place, on any date — "
        "11,000 real stars, true constellations and the actual moon phase of your night. "
        "Personalise the date, place and dedication line. {extra}. "
        "Made to order and hand-finished in the UK. Free UK delivery.")

# Доп-кадры (02.08): те же слайды, что на листингах сайта/Etsy — Merchant показывает их
# каруселью в карточке. Рамочным форматам добавляем слайд рам; интерьер — всем.
def additional_images(fmt):
    names = ["themes.jpg", "detail.jpg", "sizes.jpg", "arrives.jpg"]
    if fmt != "Print":
        names.insert(1, "frames.jpg")
    urls = [f"{SITE}/assets/starmap/gallery/{n}" for n in names]
    urls.append(f"{SITE}/assets/starmap/occ-met.jpg")
    return "\n".join(f"    <g:additional_image_link>{u}</g:additional_image_link>" for u in urls)


def item_xml(pid, fmt, size, price, extra, LINK):
    title = f"Personalised Star Map — {fmt} {size} — Your Exact Night Sky"
    d = DESC.format(extra=extra.capitalize())
    return f"""  <item>
    <g:id>{pid}</g:id>
    <g:title>{html.escape(title)}</g:title>
    <g:description>{html.escape(d)}</g:description>
    <g:link>{html.escape(LINK)}</g:link>
    <g:image_link>{SITE}/assets/starmap/feed/{pid}.jpg</g:image_link>
{additional_images(fmt)}
    <g:availability>in_stock</g:availability>
    <g:price>{price:.2f} GBP</g:price>
    <g:condition>new</g:condition>
    <g:brand>SKY, THAT NIGHT</g:brand>
    <g:identifier_exists>no</g:identifier_exists>
    <g:google_product_category>500044</g:google_product_category>
    <g:product_type>Home &amp; Living &gt; Wall Art &gt; Personalised Star Maps</g:product_type>
    <g:item_group_id>SKN-STARMAP</g:item_group_id>
    <g:shipping>
      <g:country>GB</g:country>
      <g:price>0.00 GBP</g:price>
    </g:shipping>
  </item>"""

for fname, link in FEEDS:
    body = "\n".join(item_xml(*it, link) for it in ITEMS)
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
<channel>
  <title>SKY, THAT NIGHT — Personalised Star Maps</title>
  <link>{SITE}/</link>
  <description>Custom star maps of your exact night sky. Generated {date.today().isoformat()}.</description>
{body}
</channel>
</rss>
"""
    open(fname, "w").write(feed)
    print(f"{fname}: {len(ITEMS)} items, {len(feed)} bytes")
