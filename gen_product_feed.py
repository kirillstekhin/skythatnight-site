#!/usr/bin/env python3
"""Google Merchant Center product feed → feed.xml (RSS 2.0 + g: namespace).
9 позиций = матрица 3×3 (Print/Framed/Classic × 30x40/40x50/50x70), цены = PRICES
конфигуратора (VAT-incl). Кастом-товар без GTIN → identifier_exists=no.
Запуск: python3 gen_product_feed.py  (из site/), потом коммит feed.xml."""
import html
from datetime import date

SITE = "https://www.skythatnight.com"
LINK = SITE + "/?utm_source=google&utm_medium=shopping"

# (id, формат, размер, цена, картинка, доп-описание формата)
ITEMS = [
    ("SKN-PRINT-3040",   "Print",         "30×40 cm", 26.99, "hero-midnight.jpg",          "museum-grade giclée print, shipped rolled"),
    ("SKN-PRINT-4050",   "Print",         "40×50 cm", 29.99, "hero-midnight.jpg",          "museum-grade giclée print, shipped rolled"),
    ("SKN-PRINT-5070",   "Print",         "50×70 cm", 32.99, "hero-midnight.jpg",          "museum-grade giclée print, shipped rolled"),
    ("SKN-FRAMED-3040",  "Framed",        "30×40 cm", 44.99, "mockup-framed-white.jpg",    "handmade wood frame (white or natural), ready to hang"),
    ("SKN-FRAMED-4050",  "Framed",        "40×50 cm", 52.99, "mockup-framed-white.jpg",    "handmade wood frame (white or natural), ready to hang"),
    ("SKN-FRAMED-5070",  "Framed",        "50×70 cm", 59.99, "mockup-framed-natural.jpg",  "handmade wood frame (white or natural), ready to hang"),
    ("SKN-CLASSIC-3040", "Classic Frame", "30×40 cm", 59.99, "mockup-classic-gold.jpg",    "gallery classic frame in black, antique gold or antique silver"),
    ("SKN-CLASSIC-4050", "Classic Frame", "40×50 cm", 69.99, "mockup-classic-black.jpg",   "gallery classic frame in black, antique gold or antique silver"),
    ("SKN-CLASSIC-5070", "Classic Frame", "50×70 cm", 79.99, "mockup-classic-silver.jpg",  "gallery classic frame in black, antique gold or antique silver"),
]

DESC = ("A museum-grade star map of the exact sky above any place, on any date — "
        "11,000 real stars, true constellations and the actual moon phase of your night. "
        "Personalise the date, place and dedication line. {extra}. "
        "Made to order and hand-finished in the UK. Free UK delivery.")

def item_xml(pid, fmt, size, price, img, extra):
    title = f"Personalised Star Map — {fmt} {size} — Your Exact Night Sky"
    d = DESC.format(extra=extra.capitalize())
    return f"""  <item>
    <g:id>{pid}</g:id>
    <g:title>{html.escape(title)}</g:title>
    <g:description>{html.escape(d)}</g:description>
    <g:link>{html.escape(LINK)}</g:link>
    <g:image_link>{SITE}/assets/starmap/{img}</g:image_link>
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

body = "\n".join(item_xml(*it) for it in ITEMS)
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
open("feed.xml", "w").write(feed)
print(f"feed.xml: {len(ITEMS)} items, {len(feed)} bytes")
