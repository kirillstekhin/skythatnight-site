#!/usr/bin/env python3
"""Submit URLs to IndexNow — instant-indexing ping for Bing, Yandex, Seznam, Naver.
(Google does NOT use IndexNow; Google discovery = Search Console + sitemap.)

Ownership is proven by a public key file  <key>.txt  at the site root that
contains exactly the key. Run AFTER that file is live (committed + pushed),
otherwise the engines cannot validate ownership and drop the submission.

  python3 indexnow.py               # submit every URL in sitemap.xml
  python3 indexnow.py <url> ...     # submit only the given URLs
"""
import sys, glob, json, re, urllib.request, urllib.error

HOST = "www.skythatnight.com"
BASE = "https://" + HOST


def find_key():
    """Key file = <key>.txt at repo root whose content equals its own name."""
    for f in glob.glob("*.txt"):
        name = f[:-4]
        try:
            content = open(f).read().strip()
        except OSError:
            continue
        if content == name and re.fullmatch(r"[A-Za-z0-9-]{8,128}", content):
            return content, f
    return None, None


def sitemap_urls():
    xml = open("sitemap.xml").read()
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def submit(urls):
    key, keyfile = find_key()
    if not key:
        sys.exit("No IndexNow key file (expected <key>.txt containing the key at repo root)")
    payload = {"host": HOST, "key": key,
               "keyLocation": f"{BASE}/{keyfile}", "urlList": urls}
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=20)
        print(f"IndexNow HTTP {resp.status} — submitted {len(urls)} URLs (key {key[:6]}…)")
        print("  200=OK  202=received/validating  (both mean accepted)")
    except urllib.error.HTTPError as e:
        print(f"IndexNow HTTP {e.code}: {e.reason}")
        print("  " + e.read().decode(errors="replace")[:300])


if __name__ == "__main__":
    submit(sys.argv[1:] or sitemap_urls())
