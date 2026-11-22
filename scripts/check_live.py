"""Weekly health check of the live site: python3 scripts/check_live.py https://theguysaccount.github.io/mealprep-business-os

Every sitemap page answers 200 with its own canonical URL; the data files parse and agree with the sitemap; the
IndexNow key is served; guides older than a year are listed as warnings (they show a re-check notice on the page).
Exits 1 on any error.
"""
import datetime
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "mealprep-business-os-healthcheck/1.0 (+https://github.com/theguysaccount/mealprep-business-os)"


def get(url):
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return e.code, b""
            last = e
        except OSError as e:
            last = e
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{url}: {last}")


def main(base):
    base = base.rstrip("/")
    errors, warnings = [], []
    status, body = get(f"{base}/sitemap.xml")
    urls = re.findall(r"<loc>([^<]+)</loc>", body.decode())
    if status != 200 or len(urls) < 5:
        errors.append(f"sitemap: status {status}, {len(urls)} URLs")
    for u in urls:
        status, page = get(u)
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', page.decode("utf-8", "replace"))
        if status != 200 or not canon or canon.group(1) != u:
            errors.append(f"{u}: status {status}, canonical {canon.group(1) if canon else None}")
    meta = json.loads(get(f"{base}/data/meta.json")[1])
    states = json.loads(get(f"{base}/data/states.json")[1])["states"]
    if meta["states"] != len(states) or sum(1 for u in urls if "/permits/" in u and u.rstrip("/").count("/") > base.count("/") + 1) != len(states):
        errors.append("state count differs between meta.json, states.json and the sitemap")
    today = datetime.datetime.now(datetime.timezone.utc).date()
    for s in states:
        age = (today - datetime.date.fromisoformat(s["checked"])).days
        if age > 365:
            warnings.append(f"{s['state']} was last checked {age} days ago: due for the re-check routine")
    key = (ROOT / "site" / "indexnow-key.txt").read_text().strip()
    if get(f"{base}/{key}.txt")[1].decode().strip() != key:
        errors.append("IndexNow key file not served")
    print(f"checked {len(urls)} pages; {len(states)} guides, checked {meta['oldest_check']} to {meta['newest_check']}")
    for w in warnings:
        print(f"::warning::{w}")
    for e in errors:
        print(f"::error::{e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
