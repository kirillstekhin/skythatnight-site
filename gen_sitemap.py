#!/usr/bin/env python3
"""Generate sitemap.xml with <lastmod> from each page's last git-commit date.

Public pages = every *.html except the excludes; index.html is emitted as "/".
lastmod = last git commit date of the file (YYYY-MM-DD), falling back to mtime.
Run after regenerating pages:  python3 gen_sitemap.py
"""
import subprocess, os, glob, datetime

BASE = "https://www.skythatnight.com"
EXCLUDE = {"404.html"}          # error page — never in sitemap


def group_meta(fn):
    """(sort_group, url_path, priority) — controls order + priority hint."""
    if fn == "index.html":
        return (0, "/", "1.0")
    if fn.startswith("occasion-"):
        return (1, "/" + fn, "0.8")
    if fn.startswith("theme-"):
        return (2, "/" + fn, "0.7")
    return (3, "/" + fn, "0.3")   # legal / other


def lastmod(fn):
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", fn],
            capture_output=True, text=True, check=True).stdout.strip()
        if out:
            return out
    except Exception:
        pass
    return datetime.date.fromtimestamp(os.path.getmtime(fn)).isoformat()


rows = []
for fn in glob.glob("*.html"):
    if fn in EXCLUDE:
        continue
    grp, path, pr = group_meta(fn)
    rows.append((grp, path, pr, lastmod(fn)))
rows.sort(key=lambda r: (r[0], r[1]))

out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for grp, path, pr, lm in rows:
    out.append(f'  <url><loc>{BASE}{path}</loc>'
               f'<lastmod>{lm}</lastmod><priority>{pr}</priority></url>')
out.append('</urlset>')
open("sitemap.xml", "w").write("\n".join(out) + "\n")
print(f"wrote sitemap.xml — {len(rows)} URLs")
