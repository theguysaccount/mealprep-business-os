"""Validate state guide files against pipeline/RESEARCH.md.

    python3 pipeline/validate_states.py data/states            # a folder
    python3 pipeline/validate_states.py data/states/TX.json   # one file

Prints OK or one line per problem; exit code 0 when OK. build.py uses the same checks.
"""
import datetime
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado", "CT": "Connecticut",
    "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
SECTION_KEYS = ["home", "cottage", "kitchen", "training", "business"]
SECTION_TITLES = {
    "home": "Selling meals made in a home kitchen",
    "cottage": "Cottage food: what can be sold from home",
    "kitchen": "Selling prepared meals from a licensed kitchen",
    "training": "Food safety certificates",
    "business": "Registering the business and sales tax",
}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
UPDATED = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


def words(s):
    return len(re.findall(r"[A-Za-z0-9$%'.-]+", s))


def official(url):
    host = (urlparse(url).hostname or "").lower()
    return url.startswith("https://") and (host.endswith(".gov") or host.endswith(".us") or host == "gov")


def check_source(s, today, where):
    errs = []
    if not isinstance(s, dict):
        return [f"{where}: source must be an object"]
    for k in ("agency", "title", "url", "kind", "checked", "updated", "read"):
        if k not in s:
            errs.append(f"{where}: source missing {k}")
    if errs:
        return errs
    if not isinstance(s["agency"], str) or len(s["agency"].strip()) < 4:
        errs.append(f"{where}: agency name missing")
    if not isinstance(s["title"], str) or not s["title"].strip():
        errs.append(f"{where}: title missing")
    if not isinstance(s["url"], str) or not official(s["url"]):
        errs.append(f"{where}: {s['url']!r} is not an https government (.gov or .us) address")
    if s["kind"] not in ("agency", "statute", "rule"):
        errs.append(f"{where}: kind must be agency, statute or rule")
    if not isinstance(s["checked"], str) or not DATE.match(s["checked"]):
        errs.append(f"{where}: checked must be YYYY-MM-DD")
    elif datetime.date.fromisoformat(s["checked"]) > today:
        errs.append(f"{where}: checked date is in the future")
    if s["updated"] is not None and not (isinstance(s["updated"], str) and UPDATED.match(s["updated"])):
        errs.append(f"{where}: updated must be YYYY, YYYY-MM, YYYY-MM-DD or null")
    if s["read"] not in ("fetched", "search"):
        errs.append(f"{where}: read must be fetched or search")
    return errs


def check(data, name, today=None):
    today = today or datetime.date.today() + datetime.timedelta(days=1)
    errs = []
    for k in ("state", "abbr", "checked", "answer", "answer_text", "sections", "local"):
        if k not in data:
            errs.append(f"missing {k}")
    if errs:
        return errs
    if data["abbr"] not in STATES or STATES[data["abbr"]] != data["state"]:
        errs.append(f"abbr/state {data['abbr']!r}/{data['state']!r} is not a US state or DC")
    if name and name != data["abbr"]:
        errs.append(f"file should be named {data['abbr']}.json")
    if not DATE.match(str(data["checked"])):
        errs.append("checked must be YYYY-MM-DD")
    if data["answer"] not in ("no", "limited", "yes"):
        errs.append("answer must be no, limited or yes")
    if not isinstance(data["answer_text"], str) or not 8 <= words(data["answer_text"]) <= 90:
        errs.append("answer_text: 8-90 words")
    keys = [s.get("key") for s in data["sections"]] if isinstance(data["sections"], list) else []
    if keys != SECTION_KEYS:
        errs.append(f"sections must be {SECTION_KEYS} in that order, got {keys}")
        return errs
    total_points = 0
    for sec in data["sections"]:
        where = sec["key"]
        sources = sec.get("sources", [])
        points = sec.get("points", [])
        if not isinstance(points, list) or not isinstance(sources, list):
            errs.append(f"{where}: points and sources must be lists")
            continue
        if len(points) > 6:
            errs.append(f"{where}: at most 6 points")
        for i, s in enumerate(sources):
            errs += check_source(s, today, f"{where} source {i}")
        used = set()
        for p in points:
            if not isinstance(p, dict) or not isinstance(p.get("text"), str) or not isinstance(p.get("src"), list):
                errs.append(f"{where}: each point needs text and src")
                continue
            if not 8 <= words(p["text"]) <= 70:
                errs.append(f"{where}: point has {words(p['text'])} words (8-70): {p['text'][:50]!r}")
            if not p["src"]:
                errs.append(f"{where}: a point without a source: {p['text'][:50]!r}")
            for i in p["src"]:
                if not isinstance(i, int) or not 0 <= i < len(sources):
                    errs.append(f"{where}: src index {i!r} out of range")
                used.add(i)
            if re.search(r"https?://|<[a-z/]", p["text"]):
                errs.append(f"{where}: no URLs or markup in point text")
        unused = set(range(len(sources))) - used
        if unused:
            errs.append(f"{where}: sources {sorted(unused)} are not cited by any point")
        total_points += len(points)
    if not data["sections"][0]["points"]:
        errs.append("home: needs at least one point (it answers the page's main question)")
    if total_points < 4:
        errs.append("fewer than 4 sourced points in total")
    loc = data["local"]
    if not isinstance(loc, dict) or not isinstance(loc.get("text"), str) or not loc["text"].strip():
        errs.append("local: needs text")
    else:
        errs += check_source(loc.get("source"), today, "local source")
    return errs


def main(paths):
    files = []
    for p in map(Path, paths):
        files += sorted(p.glob("*.json")) if p.is_dir() else [p]
    bad = 0
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as e:
            print(f"{f.name}: not valid JSON ({e})")
            bad += 1
            continue
        errs = check(data, f.stem)
        for e in errs:
            print(f"{f.name}: {e}")
        bad += bool(errs)
    if bad:
        print(f"{bad} file(s) need fixing")
        return 1
    print(f"OK ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["data/states"]))
