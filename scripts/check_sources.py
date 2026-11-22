"""Monthly check of every source the state guides cite: python3 scripts/check_sources.py [--report ops/sources-report.md]

Each cited URL is requested once, slowly (2 s apart, one site at a time), with an identifying User-Agent:
- 200-399: fine.
- 404 or 410: broken. Listed in the report and in an issue, so the guide gets re-checked (OPERATIONS.md).
- 401, 403, 406, 429 or a bot check: the site refuses scripts. Listed as "not checkable by script"; not an error.
- timeouts and 5xx: retried once, then listed as "unreachable this time".
Exit code 0 unless --strict and something is broken. Never touches the site.
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
UA = "mealprep-business-os-linkcheck/1.0 (+https://github.com/theguysaccount/mealprep-business-os)"


def sources():
    out = defaultdict(list)
    for f in sorted((ROOT / "data" / "states").glob("*.json")):
        s = json.loads(f.read_text(encoding="utf-8"))
        for sec in s["sections"]:
            for src in sec["sources"]:
                out[src["url"]].append(f"{s['abbr']} {sec['key']}")
        out[s["local"]["source"]["url"]].append(f"{s['abbr']} local")
    return out


def probe(url):
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/pdf,*/*"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code >= 500 and attempt == 0:
                time.sleep(5)
                continue
            return e.code
        except Exception as e:   # timeouts, TLS problems, DNS
            if attempt == 0:
                time.sleep(5)
                continue
            return f"error: {type(e).__name__}"
    return "error"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    found = sources()
    by_host = defaultdict(list)
    for u in found:
        by_host[urlparse(u).hostname].append(u)
    broken, refused, unreachable, ok = [], [], [], 0
    for host in sorted(by_host):
        for u in by_host[host]:
            status = probe(u)
            if isinstance(status, int) and status < 400:
                ok += 1
            elif status in (404, 410):
                broken.append((u, status))
            elif status in (401, 403, 406, 429, 451):
                refused.append((u, status))
            else:
                unreachable.append((u, status))
            time.sleep(2)
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    lines = [f"# Source check {today}", "", f"{len(found)} cited URLs: {ok} fine, {len(broken)} broken, "
             f"{len(refused)} refuse scripts, {len(unreachable)} unreachable this time.", ""]
    for title, rows in (("Broken (re-check these guides)", broken), ("Refuse scripts (check by hand when re-checking)", refused),
                        ("Unreachable this time", unreachable)):
        if rows:
            lines += [f"## {title}", ""] + [f"- {u} ({s}): {', '.join(found[u])}" for u, s in rows] + [""]
    text = "\n".join(lines)
    print(text)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(text + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text + "\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"broken={len(broken)}\n")
    for u, s in broken:
        print(f"::warning::broken source {u} ({s}) cited by {', '.join(found[u])}")
    return 1 if args.strict and broken else 0


if __name__ == "__main__":
    sys.exit(main())
