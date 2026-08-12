#!/usr/bin/env python3
"""Страница после оплаты `thank-you.html` — подтверждение заказа + событие конверсии.

    python3 gen_thankyou.py     # из site/ → thank-you.html

ЗАЧЕМ (11.08.2026). Две задачи одной страницей:
 1. **Измерение.** Событие `conversion` Google Ads может стоять ТОЛЬКО на странице, куда
    покупатель попадает ПОСЛЕ оплаты. Раньше Stripe показывал свою типовую «Payment
    successful» — чужой домен, повесить туда нечего, поэтому PMax крутился вслепую.
 2. **Опыт покупателя.** Страница Stripe ничего не говорит о том, что будет дальше:
    товар делается под заказ, ждать 2–4 рабочих дня. Тишина после оплаты — первая
    причина писем «а где мой заказ» и запросов возврата.

Значение конверсии приходит в query от Stripe: `?sku=SKN-PRINT-4050&v=29.99&
session_id={CHECKOUT_SESSION_ID}` (подставляет `stripe_set_redirect.py`). Величина нужна
не для отчётности — по ней PMax учится торговаться за дорогие заказы (tROAS), поэтому
шлём именно цену позиции, а не единицу.

⚠️ ЗАЩИТА ОТ ДВОЙНОГО СЧЁТА: событие шлётся один раз на session_id (ключ в localStorage).
Без этого F5 на странице спасибо = вторая «покупка» в отчёте и испорченное обучение.
⚠️ Цена НЕ доверяется вслепую: значение из URL проверяется по прайс-матрице (PRICES из
конфигуратора), чужое/битое → шлём цену по SKU, а если и его нет — событие без value.
"""
import html
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://www.skythatnight.com"
idx = open(os.path.join(HERE, "index.html")).read()

STYLE = re.search(r"<style>(.*?)</style>", idx, re.S).group(1)
HEADER = re.search(r"(<header>.*?</header>)", idx, re.S).group(1)
FOOTER = re.search(r"(<footer>.*?</footer>)", idx, re.S).group(1)

_spec = importlib.util.spec_from_file_location("feed", os.path.join(HERE, "gen_product_feed.py"))
_feed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_feed)
# ⚠ ALL_ITEMS, а не ITEMS: с 11.08 в фиде живут ещё 9 лунных SKU, и без них
# страница спасибо не узнала бы цену лунного заказа и слала бы конверсию без value.
PRICE_BY_SKU = {pid: price for pid, _f, _s, price, _e in _feed.ALL_ITEMS}

SEND_TO = "AW-18367610518/IZrUCL3o398cEJb9rbZE"   # см. gen_gtag.py

EXTRA_CSS = """
.ty { padding: clamp(3rem,7vw,6rem) 0 clamp(2rem,5vw,4rem); text-align:center; }
.ty-mark { font-size:2.4rem; color:var(--gold); line-height:1; margin-bottom:1.2rem; }
.ty h1 { font-family:var(--serif); font-weight:500; font-size:clamp(2rem,4.4vw,3.2rem);
  line-height:1.1; color:var(--moon); margin:0 0 1rem; }
.ty-lead { font-family:var(--sans); font-weight:300; font-size:1.05rem; line-height:1.7;
  color:var(--moon-sub); max-width:36rem; margin:0 auto 1.2rem; }
.ty-ref { font-family:var(--sans); font-size:.82rem; letter-spacing:.14em; text-transform:uppercase;
  color:var(--moon-faint); margin-bottom:2.6rem; }
.ty-steps { display:grid; grid-template-columns:repeat(3,1fr); gap:1.4rem; max-width:52rem;
  margin:0 auto 2.6rem; text-align:left; }
@media (max-width:760px){ .ty-steps { grid-template-columns:1fr; } }
.ty-step { padding:1.3rem 1.4rem; border:1px solid rgba(201,169,97,.2); border-radius:3px; }
.ty-step-n { font-family:var(--sans); font-size:.72rem; letter-spacing:.28em; text-transform:uppercase;
  color:var(--gold); margin-bottom:.6rem; }
.ty-step p { font-family:var(--sans); font-weight:300; font-size:.94rem; line-height:1.65;
  color:var(--moon-sub); margin:0; }
.ty-note { font-family:var(--sans); font-weight:300; font-size:.9rem; line-height:1.7;
  color:var(--moon-faint); max-width:38rem; margin:0 auto 2rem; }
.ty-note a { color:var(--gold); }
"""

BODY = f"""
<section class="ty">
  <div class="sm-stars" aria-hidden="true"></div>
  <div class="container">
    <div class="ty-mark" aria-hidden="true">&#10022;</div>
    <h1>Your night is being made.</h1>
    <p class="ty-lead">Payment received &mdash; thank you. Your sky is now with our print studio,
    calculated for the exact date, time and place you chose. A confirmation is on its way to
    your email.</p>
    <p class="ty-ref" id="ty-ref"></p>

    <div class="ty-steps">
      <div class="ty-step">
        <div class="ty-step-n">Step one</div>
        <p>We render your night at print resolution &mdash; 11,000 real stars in their true
        positions, with the moon phase of that evening.</p>
      </div>
      <div class="ty-step">
        <div class="ty-step-n">Step two</div>
        <p>It is printed on 200&nbsp;gsm archival matte paper, hand-checked, and framed if you
        chose a frame.</p>
      </div>
      <div class="ty-step">
        <div class="ty-step-n">Step three</div>
        <p>Dispatched in 2&ndash;4 working days with free UK delivery. Tracking arrives by email
        the moment it leaves us.</p>
      </div>
    </div>

    <p class="ty-note">Spotted a mistake in the date, place or wording? Email
    <a href="mailto:admin@shopcienty.com">admin@shopcienty.com</a> straight away &mdash; if it
    has not gone to print yet, we will fix it. Because each piece is made to your
    specification it is exempt from change-of-mind returns, but if it arrives damaged or not as
    ordered we reprint it free. See <a href="delivery.html">Delivery &amp; Returns</a>.</p>

    <a class="sm-cta" href="./">Design another night</a>
  </div>
</section>
"""

PRICES_JS = ", ".join(f'"{k}":{v:.2f}' for k, v in PRICE_BY_SKU.items())

SCRIPT = f"""<script>
(function () {{
  var q = new URLSearchParams(location.search);
  var sid = q.get('session_id') || '';
  var sku = (q.get('sku') || '').toUpperCase();
  var PRICES = {{{PRICES_JS}}};

  /* ссылка на заказ — покупателю, чтобы было что назвать в письме */
  var ref = sid ? sid.slice(-10).toUpperCase() : '';
  document.getElementById('ty-ref').textContent = ref ? 'Order reference ' + ref : '';

  /* значение конверсии: URL проверяем по матрице цен, иначе берём цену SKU */
  var v = parseFloat(q.get('v'));
  var known = PRICES[sku];
  var value = (known !== undefined && Math.abs(v - known) < 0.005) ? known
            : (known !== undefined ? known : (isFinite(v) && v > 0 && v < 500 ? v : null));

  /* один раз на session_id — F5 не должен рождать вторую покупку */
  var key = 'skn_conv_' + (sid || 'nosid');
  var fired = false;
  try {{ fired = localStorage.getItem(key) === '1'; }} catch (e) {{}}
  if (!fired && typeof gtag === 'function') {{
    var payload = {{ 'send_to': '{SEND_TO}', 'currency': 'GBP', 'transaction_id': sid }};
    if (value !== null) payload.value = value;
    gtag('event', 'conversion', payload);
    try {{ localStorage.setItem(key, '1'); }} catch (e) {{}}
  }}
}})();
</script>"""

PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Thank you &mdash; your night is being made | Sky, That Night</title>
<meta name="description" content="Your order is confirmed. Each star map is made to order in the UK and dispatched within 2-4 working days with free UK delivery and tracking by email.">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{SITE}/thank-you.html">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sky, That Night">
<meta property="og:title" content="Thank you &mdash; your night is being made">
<meta property="og:url" content="{SITE}/thank-you.html">
<meta name="twitter:card" content="summary">
<link rel="icon" href="assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="assets/favicon.png?v=2">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Hanken+Grotesk:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css?v=2">
<style>{STYLE}{EXTRA_CSS}</style>
</head>
<body class="sm-night">
{HEADER}
<main>
{BODY}
</main>
{FOOTER}
{SCRIPT}
</body>
</html>
"""

def _reinject():
    """Перегенерация страницы сносит вшитые блоки — вернуть их СРАЗУ.

    ⚠ Мина 02.08: генераторы страниц выносили beacon Cloudflare, и сайт молча терял
    аналитику. Здесь та же ловушка вдвойне: без gtag страница спасибо перестанет
    засчитывать покупки, а Google Ads будет показывать ноль конверсий при живых заказах.
    """
    import importlib.util as _iu
    for name in ("gen_analytics", "gen_gtag"):
        sp = _iu.spec_from_file_location(name, os.path.join(HERE, f"{name}.py"))
        mod = _iu.module_from_spec(sp)
        sp.loader.exec_module(mod)
        mod.inject(True)


if __name__ == "__main__":
    out = os.path.join(HERE, "thank-you.html")
    open(out, "w").write(PAGE)
    print(f"✅ thank-you.html · {len(PAGE)} байт · матрица цен {len(PRICE_BY_SKU)} SKU · send_to {SEND_TO}")
    _reinject()
