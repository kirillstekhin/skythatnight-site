#!/usr/bin/env python3
"""Google-тег (gtag.js) + Consent Mode v2 + мини-баннер согласия — во все страницы сайта.

    python3 gen_gtag.py --status        # где стоит, где нет (ничего не меняет)
    python3 gen_gtag.py --inject --go   # вшить/обновить во всех *.html
    python3 gen_gtag.py --remove --go   # снять (если решим, что баннер не нужен)

⛔ БЕЗ `--go` ничего не пишется.

ЗАЧЕМ (11.08.2026). PMax «SKN Star Maps PMax» крутился с 02.08 БЕЗ ЕДИНОЙ конверсии в
кабинете: gtag на сайте отсутствовал полностью (проверено grep'ом — ни одной строки).
Performance Max — это алгоритм, который торгуется ЗА КОНВЕРСИИ; без события покупки он
оптимизируется вслепую, а мы не можем посчитать ни CPA, ни ROAS. Конверсия «Purchase»
заведена 11.08 в аккаунте 544-807-1342: value = разная для каждой (Event snippet),
Count = Every, окно клика 90 дней.

⚠️ ПОЧЕМУ ЗДЕСЬ БАННЕР, ХОТЯ У Cloudflare-СЧЁТЧИКА ЕГО НЕТ.
`gen_analytics.py` выбирал Cloudflare Web Analytics именно потому, что тот БЕЗ КУК —
под UK GDPR/PECR баннер не нужен. Google-тег куки СТАВИТ (`_gcl_au` для атрибуции
конверсий), и это уже не «строго необходимые» куки: PECR reg.6 требует согласия ДО
записи. Поэтому:
  • Consent Mode v2 стартует в состоянии `denied` по всем ad_*/analytics_storage —
    до согласия gtag шлёт бескуковые пинги и ничего не пишет в браузер;
  • узкая полоса внизу с «Accept / Decline» (не модалка — первый экран не закрывает);
  • выбор помнится в localStorage (не кука) ключом `skn_consent`.
Отказ = тег остаётся бескуковым, сайт работает, конверсия просто не засчитается.

⚠️ ОДИН ТЕГ НА СТРАНИЦУ. Скрипт идемпотентен: находит свой блок по маркеру и заменяет
целиком, а не дописывает второй (двойной gtag = задвоенные конверсии).

Пара к этому файлу — `thank-you.html`: там и только там висит событие покупки. Чтобы оно
срабатывало, Stripe Payment Links должны после оплаты возвращать покупателя на неё
(`stripe_set_redirect.py`), иначе человек остаётся на странице Stripe и конверсии нет.
"""
import argparse, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
HOST = "www.skythatnight.com"

AW_ID = "AW-18367610518"                       # Google tag аккаунта 544-807-1342
CONV_LABEL = "IZrUCL3o398cEJb9rbZE"            # метка конверсии «Purchase»
SEND_TO = f"{AW_ID}/{CONV_LABEL}"

# ⚠ ДВА БЛОКА, А НЕ ОДИН (иначе не работает — проверено 11.08).
# Первая версия вешала всё одним куском перед </body>, и на `thank-you.html` событие
# покупки оказывалось ВЫШЕ определения gtag: `typeof gtag === 'function'` = false,
# конверсия молча не отправлялась. Google и так требует тег «immediately after <head>».
# Поэтому: конфиг и согласие — в <head>, видимая полоса и её обработчики — перед </body>.
HSTART = "<!-- SKN_GTAG_HEAD:START"
HEND = "<!-- SKN_GTAG_HEAD:END -->"
BSTART = "<!-- SKN_GTAG_BAR:START"
BEND = "<!-- SKN_GTAG_BAR:END -->"

HEAD_BLOCK = f"""{HSTART} — генерится gen_gtag.py, РУКАМИ НЕ ПРАВИТЬ.
     Consent Mode v2: до согласия куки не пишутся (UK PECR reg.6). -->
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('consent', 'default', {{
    'ad_storage': 'denied', 'ad_user_data': 'denied', 'ad_personalization': 'denied',
    'analytics_storage': 'denied', 'wait_for_update': 500
  }});
  try {{
    if (localStorage.getItem('skn_consent') === 'granted') {{
      gtag('consent', 'update', {{
        'ad_storage': 'granted', 'ad_user_data': 'granted',
        'ad_personalization': 'granted', 'analytics_storage': 'granted'
      }});
    }}
  }} catch (e) {{}}
  gtag('js', new Date());
  gtag('config', '{AW_ID}');
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id={AW_ID}"></script>
<style>
  .skn-consent {{ position:fixed; left:0; right:0; bottom:0; z-index:9999; display:none;
    gap:1rem; align-items:center; justify-content:center; flex-wrap:wrap;
    padding:.85rem 1.2rem; background:rgba(8,12,26,.96); border-top:1px solid rgba(201,169,97,.28);
    font-family:'Hanken Grotesk',system-ui,sans-serif; font-size:.82rem; color:#c9d3e8; }}
  .skn-consent.on {{ display:flex; }}
  .skn-consent p {{ margin:0; max-width:46rem; line-height:1.5; }}
  .skn-consent a {{ color:#c9a961; }}
  .skn-consent button {{ font-family:inherit; font-size:.8rem; letter-spacing:.04em; cursor:pointer;
    padding:.5rem 1.1rem; border-radius:2px; border:1px solid rgba(201,169,97,.5); background:none; color:#c9a961; }}
  .skn-consent button.yes {{ background:#c9a961; border-color:#c9a961; color:#0b1020; font-weight:500; }}
</style>
{HEND}"""

BAR_BLOCK = f"""{BSTART} — генерится gen_gtag.py, РУКАМИ НЕ ПРАВИТЬ. -->
<div class="skn-consent" id="skn-consent" role="region" aria-label="Cookie choice">
  <p>We use cookies only to measure whether our ads work. Nothing is stored until you choose.
     See our <a href="privacy.html">Privacy Policy</a>.</p>
  <span>
    <button class="yes" id="skn-consent-yes">Accept</button>
    <button id="skn-consent-no">Decline</button>
  </span>
</div>
<script>
  (function () {{
    var bar = document.getElementById('skn-consent');
    var saved = null;
    try {{ saved = localStorage.getItem('skn_consent'); }} catch (e) {{}}
    if (!saved) bar.classList.add('on');
    function decide(ok) {{
      try {{ localStorage.setItem('skn_consent', ok ? 'granted' : 'denied'); }} catch (e) {{}}
      if (ok) gtag('consent', 'update', {{
        'ad_storage': 'granted', 'ad_user_data': 'granted',
        'ad_personalization': 'granted', 'analytics_storage': 'granted'
      }});
      bar.classList.remove('on');
    }}
    document.getElementById('skn-consent-yes').onclick = function () {{ decide(true); }};
    document.getElementById('skn-consent-no').onclick = function () {{ decide(false); }};
  }})();
</script>
{BEND}"""


def pages():
    return [p for p in sorted(ROOT.glob("*.html")) if "</body>" in p.read_text()]


def _strip(s, a, b):
    i, j = s.find(a), s.find(b)
    if i < 0 or j < 0:
        return s
    k = i - 1 if i > 0 and s[i - 1] == "\n" else i
    return s[:k] + s[j + len(b):]


def clean(s):
    """Снять оба блока, включая ЛЮБУЮ старую однокусочную версию."""
    s = _strip(s, HSTART, HEND)
    s = _strip(s, BSTART, BEND)
    s = _strip(s, "<!-- SKN_GTAG:START", "<!-- SKN_GTAG:END -->")   # версия до разделения
    return s


def ok(s):
    """Страница в порядке, только если ОБА блока на месте И конфиг выше полосы."""
    return HEAD_BLOCK in s and BAR_BLOCK in s and s.find(HSTART) < s.find(BSTART)


def inject(go, remove=False):
    todo, already = [], 0
    for p in pages():
        s = p.read_text()
        if remove:
            if HSTART in s or BSTART in s or "<!-- SKN_GTAG:START" in s:
                todo.append(p)
        elif ok(s):
            already += 1
        else:
            todo.append(p)
    verb = "снять" if remove else "вшить/обновить"
    print(f"страниц: {len(pages())} · уже актуально: {already} · {verb}: {len(todo)}")
    if not go:
        print("dry-run — нужен --go")
        return
    for p in todo:
        s = clean(p.read_text())
        if not remove:
            if "</head>" not in s:
                print(f"  ⚠ пропуск {p.name}: нет </head>")
                continue
            s = s.replace("</head>", HEAD_BLOCK + "\n</head>", 1)
            s = s.replace("</body>", BAR_BLOCK + "\n</body>", 1)
        p.write_text(s)
    print(f"✅ {'снят' if remove else 'вшит'} в {len(todo)} страниц")


def status():
    local = [p.name for p in pages() if ok(p.read_text())]
    print(f"локально с тегом: {len(local)} из {len(pages())}")
    missing = [p.name for p in pages() if not ok(p.read_text())]
    if missing:
        print("  без тега:", ", ".join(missing))
    try:
        live = urllib.request.urlopen(urllib.request.Request(
            f"https://{HOST}/", headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode()
        print("на живом сайте:", "✅ тег отдаётся" if AW_ID in live else "⛔ тега НЕТ")
        ty = urllib.request.urlopen(urllib.request.Request(
            f"https://{HOST}/thank-you.html", headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode()
        print("страница спасибо:", "✅ событие покупки на месте" if SEND_TO in ty else "⛔ события НЕТ")
    except Exception as e:
        print("живой сайт не проверить:", e)


def main():
    ap = argparse.ArgumentParser(description="Google-тег + Consent Mode для skythatnight.com")
    ap.add_argument("--inject", action="store_true")
    ap.add_argument("--remove", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()
    if a.status or not (a.inject or a.remove):
        status()
        return
    inject(a.go, remove=a.remove)


if __name__ == "__main__":
    main()
