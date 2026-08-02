#!/usr/bin/env python3
"""Cloudflare Web Analytics: создать сайт по API и вшить счётчик во все страницы.

    python3 gen_analytics.py --create --go        # создать Web Analytics site, получить токен
    python3 gen_analytics.py --inject --go        # вшить beacon во все *.html
    python3 gen_analytics.py --status             # что уже стоит (ничего не меняет)

⛔ БЕЗ `--go` ничего не создаётся и не пишется.

Зачем (02.08.2026). На сайте НЕ БЫЛО аналитики вообще — ни одной строки, при 30 страницах
и живой кассе Stripe. Проверено и в исходниках, и в отданном HTML: Cloudflare тоже ничего
не вшивал. Из-за этого «ноль продаж» необъясним: ноль посетителей и сто посетителей со
сломанной корзиной выглядят одинаково, а лечатся противоположно.

Почему именно Cloudflare Web Analytics:
 • сайт и так на Cloudflare Pages — лишнего провайдера не заводим;
 • БЕЗ КУК → под UK GDPR/PECR не нужен баннер согласия. Баннер на маленьком магазине
   срезает половину данных и портит первый экран, то есть лечение хуже болезни;
 • бесплатно и без лимита на просмотры.
⚠️ Чего он НЕ умеет: произвольных событий и воронки. Для нас это приемлемо — заказы и так
   видны в Stripe, не хватало именно ТРАФИКА (кто пришёл и откуда).

⚠️ ТОКЕН СОЗДАЁТСЯ ТОЛЬКО В ПАНЕЛИ — это единственный ручной шаг, обойти его нечем:
API-токен нельзя выпустить, не имея API-токена. Нужны права **Account · Account Settings · Edit** — НЕ Account Analytics: у неё в списке есть только
Read, создать сайт ею нельзя (проверено 02.08 перебором в панели). Дальше всё делает этот скрипт. Токен кладётся в `website/starmap/.cloudflare_creds`
(chmod 600, вне git) полем `api_token`; account_id берётся из `.r2_creds`.
"""
import argparse, json, pathlib, re, sys, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
CREDS = ROOT.parent.parent / "website" / "starmap" / ".cloudflare_creds"
R2 = ROOT.parent.parent / "website" / "starmap" / ".r2_creds"
HOST = "www.skythatnight.com"
API = "https://api.cloudflare.com/client/v4"
MARK = "cloudflareinsights"


def creds():
    if not CREDS.exists():
        sys.exit(f"⛔ нет {CREDS.name}. Создай токен в панели Cloudflare\n"
                 f"   (My Profile → API Tokens → Create Token → Custom,\n"
                 f"    права: Account · Account Settings · Edit)\n"
                 f"   и положи: {{\"api_token\": \"...\"}} в {CREDS}")
    c = json.loads(CREDS.read_text())
    c["account_id"] = c.get("account_id") or json.loads(R2.read_text())["account_id"]
    return c


def api(method, path, c, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + c["api_token"],
                                          "Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"⛔ {method} {path} → {e.code}\n{e.read()[:400].decode(errors='replace')}")


def create(go):
    c = creds()
    if not go:
        print(f"dry-run: создам Web Analytics site для {HOST} (нужен --go)")
        return
    # ⚠️ auto_install=True отвергается (web_analytics.configuration.api.autoInstallInvalid):
    # Cloudflare вшивает счётчик сам только для зоны, проксируемой через него, а у нас
    # Pages-домен. Поэтому создаём сайт без автовставки и вшиваем beacon сами (--inject).
    r = api("POST", f"/accounts/{c['account_id']}/rum/site_info", c, {"host": HOST})
    site = r["result"]
    c["site_tag"] = site["site_tag"]
    c["site_token"] = site["site_token"]
    CREDS.write_text(json.dumps(c, indent=1, ensure_ascii=False) + "\n")
    CREDS.chmod(0o600)
    print(f"✅ site_tag {site['site_tag']}, токен записан в {CREDS.name}")
    print(f"   auto_install={site.get('auto_install')} — если true, Cloudflare вшивает beacon сам,")
    print(f"   и --inject не нужен. Проверь: gen_analytics.py --status")


def snippet(tok):
    return ('<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
            f'data-cf-beacon=\'{{"token": "{tok}"}}\'></script>')


def inject(go):
    c = creds()
    tok = c.get("site_token")
    if not tok:
        sys.exit("⛔ нет site_token — сперва --create")
    pages = [p for p in sorted(ROOT.glob("*.html")) if "</body>" in p.read_text()]
    todo = [p for p in pages if MARK not in p.read_text()]
    print(f"страниц с </body>: {len(pages)}, без счётчика: {len(todo)}")
    if not go:
        print("dry-run — нужен --go")
        return
    for p in todo:
        s = p.read_text()
        p.write_text(s.replace("</body>", f"  {snippet(tok)}\n</body>", 1))
    print(f"✅ вшито в {len(todo)}")


def status():
    local = sorted(p.name for p in ROOT.glob("*.html") if MARK in p.read_text())
    print(f"локально со счётчиком: {len(local)} из {len(list(ROOT.glob('*.html')))}")
    try:
        live = urllib.request.urlopen(urllib.request.Request(
            f"https://{HOST}/", headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode()
        print("на живом сайте:", "✅ beacon отдаётся" if MARK in live else "⛔ beacon НЕ отдаётся")
    except Exception as e:
        print("живой сайт не проверить:", e)


def main():
    ap = argparse.ArgumentParser(description="Cloudflare Web Analytics для skythatnight.com")
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--inject", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()
    if a.create:  create(a.go)
    elif a.inject: inject(a.go)
    elif a.status: status()
    else: ap.print_help()


if __name__ == "__main__":
    main()
