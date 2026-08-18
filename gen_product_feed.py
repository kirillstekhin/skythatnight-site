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
# ⛔ 06.08.2026: РАНЬШЕ ЗДЕСЬ БЫЛА ОДНА ССЫЛКА НА ГЛАВНУЮ ДЛЯ ВСЕХ 9 ПОЗИЦИЙ.
# Робот Merchant Center брал из фида «SKN-FRAMED-5070 = £59.99», шёл по ссылке и
# попадал на главную с AggregateOffer 26.99–79.99 — товара за £59.99 там нет.
# Несовпадение по всем девяти = пункт «match your product data with your online
# store», вклад в бан Misrepresentation 05.08. Теперь у каждой позиции свой
# лендинг product-<id>.html (gen_product_pages.py), UTM остаётся в query.
FEED_UTM = [
    ("feed.xml", "utm_source=google&utm_medium=shopping"),
    ("feed-pinterest.xml", "utm_source=pinterest&utm_medium=shopping"),
]


def item_link(pid, utm):
    return f"{SITE}/product-{pid.lower()}.html?{utm}"

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

# ⏱ СРОКИ ДОСТАВКИ В ФИДЕ (12.08.2026). Раньше отдавали только цену доставки (0.00) —
# Google знал, что она бесплатная, но НЕ знал, когда товар приедет, и потому не мог
# написать на карточке «Free delivery by <дата>». Это одна из немногих бесплатных
# аннотаций, которая меняет вид карточки в выдаче; Merchant сам просил её («Show your
# fastest shipping options»).
# Числа НЕ придуманы: handling 2–4 рабочих дня = то, что обещает delivery.html
# («dispatched within 2–4 working days»), transit 1–3 = Evri Next Day 24 с запасом.
# Сверка по реальному заказу Rachel & Tom: оплата 04.08 → отгрузка 06.08 (2 дня) →
# доставка 08.08 (2 дня). ⛔Не занижать: обещание в фиде — это обещание покупателю,
# а Merchant сверяет заявления с фактом.
#
# Доп-кадры (02.08): те же слайды, что на листингах сайта/Etsy — Merchant показывает их
# каруселью в карточке. Рамочным форматам добавляем слайд рам; интерьер — всем.
def additional_images(fmt, moon=False):
    if moon:
        # ⚠ Лунным позициям НЕЛЬЗЯ отдавать звёздные слайды галереи (themes/detail/sizes):
        # на них нарисована звёздная карта, а карточка обещает луну — это ровно то
        # несовпадение «product data vs online store», за которое был бан 05.08.
        # Даём три реальных лунных кадра сайта: они и есть этот товар.
        urls = [f"{SITE}/assets/starmap/{n}"
                for n in ("moon-porcelain.jpg", "moon-noir.jpg", "moon-crescent.jpg")]
        # плюс общие для обоих продуктов: рамы и «как приходит» — они про упаковку, не про рисунок
        urls += [f"{SITE}/assets/starmap/gallery/{n}" for n in ("frames.jpg", "arrives.jpg")]
        return "\n".join(f"    <g:additional_image_link>{u}</g:additional_image_link>" for u in urls)
    names = ["themes.jpg", "detail.jpg", "sizes.jpg", "arrives.jpg"]
    if fmt != "Print":
        names.insert(1, "frames.jpg")
    urls = [f"{SITE}/assets/starmap/gallery/{n}" for n in names]
    urls.append(f"{SITE}/assets/starmap/occ-met.jpg")
    # 18.08: props-сцены поводов (кольца/торт; рамы = референсы Prodigi) — Merchant крутит их
    # каруселью в карточке. Только звёздным позициям: на сценах звёздная карта, луне нельзя.
    urls += [f"{SITE}/assets/starmap/props-wedding.jpg", f"{SITE}/assets/starmap/props-birthday.jpg"]
    return "\n".join(f"    <g:additional_image_link>{u}</g:additional_image_link>" for u in urls)


# ═══ ВТОРОЙ ПРОДУКТ: THE MOON THAT NIGHT (11.08.2026) ═══
# Луна живёт на сайте с 06.08, но в Google её не было вообще: фид отдавал только
# звёздную матрицу. Формат/размер/цена ОБЩИЕ со звёздным (тот же постер, тот же
# Prodigi-SKU, те же Stripe-линки) — отличается только рисунок, поэтому это отдельная
# товарная группа `SKN-MOON`, а не вариант звёздной: у Google `item_group_id` группирует
# варианты ОДНОГО товара, и смешать их значило бы показывать луну по запросу «star map».
MOON_ITEMS = [(pid.replace("SKN-", "SKN-MOON-"), fmt, size, price, extra)
              for pid, fmt, size, price, extra in ITEMS]

MOON_DESC = ("A portrait of the real Moon exactly as it hung over your night — the true phase "
             "of your date, rendered from NASA lunar photography, not a drawing. "
             "Personalise the date, place and dedication line. {extra}. "
             "Made to order and hand-finished in the UK. Free UK delivery.")


# ═══ ЗАГОЛОВКИ: ПОД ЗАПРОС, А НЕ ПОД ОПИСАНИЕ ТОВАРА (12.08.2026) ═══
# В Google Shopping ранжирование в первую очередь сопоставляет ЗАПРОС с title. Старые
# заголовки («Personalised Star Map — Classic Frame 50×70 cm — Your Exact Night Sky»)
# описывали товар, а не то, что человек набирает: повод в них не попадал вообще, хотя
# star-map покупают именно поводом. В соседних карточках выдачи 12.08 — «The Night We
# Met - Star Map…», «Name a Star Gift Set…»: у конкурентов повод в заголовке есть.
# Структура: [что это] — [чем отличается] — [формат+размер] — [повод].
#  • первые ~70 знаков видны в выдаче → туда главный запрос и отличие;
#  • формат и размер ОБЯЗАТЕЛЬНЫ в середине: 18 позиций различаются только ими, без них
#    Google склеит их в дубли;
#  • повод в хвосте — он индексируется, даже когда обрезан на экране;
#  • ⛔ноль промо-текста («SALE», «best») — это прямой запрет в правилах фида.
# Слово «Print» в формате заменено, иначе у голого принта выходило «Star Map Print …
# Print 30×40 cm».
FMT_TITLE = {"Print": "Unframed", "Framed": "Wood Frame", "Classic Frame": "Gallery Frame"}


def item_xml(pid, fmt, size, price, extra, LINK):
    moon = pid.startswith("SKN-MOON-")
    ff = FMT_TITLE[fmt]
    if moon:
        title = (f"Personalised Moon Phase Print — The Real Moon of Your Date — "
                 f"{ff} {size} — Anniversary & Birthday Gift")
        d = MOON_DESC.format(extra=extra.capitalize())
    else:
        title = (f"Personalised Star Map Print — The Night Sky of Any Date and Place — "
                 f"{ff} {size} — Anniversary & Wedding Gift")
        d = DESC.format(extra=extra.capitalize())
    if len(title) > 150:                      # жёсткий лимит Google на title
        raise SystemExit(f"⛔ {pid}: заголовок {len(title)} знаков, лимит 150")
    return f"""  <item>
    <g:id>{pid}</g:id>
    <g:title>{html.escape(title)}</g:title>
    <g:description>{html.escape(d)}</g:description>
    <g:link>{html.escape(LINK)}</g:link>
    <g:image_link>{SITE}/assets/starmap/feed/{pid}.jpg</g:image_link>
{additional_images(fmt, moon)}
    <g:availability>in_stock</g:availability>
    <g:price>{price:.2f} GBP</g:price>
    <g:condition>new</g:condition>
    <g:brand>SKY, THAT NIGHT</g:brand>
    <g:identifier_exists>no</g:identifier_exists>
    <g:google_product_category>500044</g:google_product_category>
    <g:product_type>Home &amp; Living &gt; Wall Art &gt; {"Personalised Moon Phase Prints" if moon else "Personalised Star Maps"}</g:product_type>
    <g:item_group_id>{"SKN-MOON" if moon else "SKN-STARMAP"}</g:item_group_id>
    <g:shipping>
      <g:country>GB</g:country>
      <g:service>Free standard delivery</g:service>
      <g:price>0.00 GBP</g:price>
      <g:min_handling_time>2</g:min_handling_time>
      <g:max_handling_time>4</g:max_handling_time>
      <g:min_transit_time>1</g:min_transit_time>
      <g:max_transit_time>3</g:max_transit_time>
    </g:shipping>
  </item>"""

ALL_ITEMS = ITEMS + MOON_ITEMS

for fname, utm in FEED_UTM:
    # ссылка теперь СВОЯ у каждой позиции — см. комментарий у FEED_UTM
    body = "\n".join(item_xml(*it, item_link(it[0], utm)) for it in ALL_ITEMS)
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
<channel>
  <title>SKY, THAT NIGHT — Personalised Star Maps</title>
  <link>{SITE}/</link>
  <description>Custom star maps and moon phase prints of your exact night. Generated {date.today().isoformat()}.</description>
{body}
</channel>
</rss>
"""
    open(fname, "w").write(feed)
    print(f"{fname}: {len(ALL_ITEMS)} items ({len(ITEMS)} star + {len(MOON_ITEMS)} moon), {len(feed)} bytes")
