#!/usr/bin/env python3
"""Иконки сайта: золотое кольцо + ковш Большой Медведицы на нашем небе.

    python3 gen_favicon.py            # dry-run: только контактный лист в /tmp
    python3 gen_favicon.py --write    # записать в assets/

Зачем это скрипт, а не одна картинка (31.07.2026). До сих пор в `assets/favicon.png` лежал
**логотип SHOPCIENTY** — чужой бренд во вкладке skythatnight.com, на все 30 страниц.

⛔ ПОЧЕМУ НЕЛЬЗЯ ПРОСТО УМЕНЬШИТЬ КАРТУ. Первая попытка — вырезать диск с золотым кольцом из
настоящего принта `print-samples/cfp-luxegold.png` и отмасштабировать. На 512 и 180 красиво,
а на **16 px, где иконка и живёт во вкладке**, звёзды усредняются в фон и остаётся мутное пятно
с размазанным Млечным Путём. Марку под мелкий размер надо РИСОВАТЬ, а не масштабировать.

⛔ И НЕЛЬЗЯ ОТДАТЬ ОДИН PNG НА ВСЕ РАЗМЕРЫ: браузер сам ужмёт 64→16 и вернёт ту же кашу.
Поэтому каждый размер рисуется СО СВОИМ набором: ≤32 px — только ковш (5 звёзд) и толстое
кольцо; >32 px — полная семёрка с разной величиной звёзд.

Цвета — из реальных пикселей продукта (замер по `cfp-luxegold.png`), а не подобраны на глаз:
небо (11,23,51), золото (201,169,97). Золото сошлось с тем, что уже прописано в style.css
(`rgba(201,169,97,…)`) — подтверждено с двух сторон.
"""
import argparse, pathlib
from PIL import Image, ImageDraw

NAVY = (11, 23, 51)          # небо принта
GOLD = (201, 169, 97)        # кольцо горизонта
WHITE = (255, 255, 255)

# Ковш Большой Медведицы, нормированные координаты (x вправо, y вниз).
# Ручка слева, чаша справа — как на нашем северном небе.
PLOUGH = [(0.115, 0.60), (0.255, 0.53), (0.385, 0.505), (0.515, 0.555),
          (0.545, 0.715), (0.735, 0.745), (0.755, 0.565)]
MAG    = [1.0, 0.85, 0.95, 0.6, 0.75, 0.9, 1.0]
# для ≤32 px — только чаша и начало ручки: силуэт узнаётся, каша не образуется
PLOUGH_TINY = [(0.30, 0.50), (0.52, 0.55), (0.55, 0.74), (0.78, 0.76), (0.80, 0.56)]

SS = 8                       # суперсэмплинг: рисуем крупно, ужимаем LANCZOS


def mark(size):
    tiny = size <= 32
    pts = PLOUGH_TINY if tiny else PLOUGH
    mags = [1.0] * len(PLOUGH_TINY) if tiny else MAG
    S = size * SS
    im = Image.new("RGB", (S, S), NAVY)
    dr = ImageDraw.Draw(im)
    pad = S * (0.07 if tiny else 0.10)
    dr.ellipse([pad, pad, S - pad, S - pad], outline=GOLD,
               width=max(2, int(S * (0.055 if tiny else 0.030))))
    inner = S - 2 * pad
    for (x, y), m in zip(pts, mags):
        cx, cy = pad + inner * x, pad + inner * y
        r = S * (0.042 if tiny else 0.022) * (0.55 + 0.45 * m)
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    return im.resize((size, size), Image.LANCZOS)


SIZES = [512, 180, 64, 32, 16]
OUT = {512: "icon-512.png", 180: "apple-touch-icon.png", 64: "favicon.png"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="записать в assets/ (без него — dry-run)")
    a = ap.parse_args()
    icons = {s: mark(s) for s in SIZES}

    sheet = Image.new("RGB", (len(SIZES) * 150 + 10, 160), (26, 26, 32))
    x = 10
    for s in SIZES:
        sheet.paste(icons[s].resize((140, 140), Image.NEAREST), (x, 10))
        x += 150
    sheet.save("/tmp/favicon_sheet.png")
    print("контактный лист: /tmp/favicon_sheet.png")

    if not a.write:
        print("dry-run — файлы НЕ записаны, добавь --write")
        return
    assets = pathlib.Path(__file__).resolve().parent / "assets"
    for s, name in OUT.items():
        icons[s].save(assets / name)
        print(f"  ✅ assets/{name}  ({s}×{s})")
    # .ico с тремя размерами — сюда браузер лезет за 16/32 и берёт НАШУ отрисовку,
    # а не собственное ужатие 64-го
    icons[64].save(assets / "favicon.ico", sizes=[(16, 16), (32, 32)],
                   append_images=[icons[16], icons[32]])
    print("  ✅ assets/favicon.ico  (16/32 — обе НАШЕЙ отрисовки, проверено сравнением)")


if __name__ == "__main__":
    main()
