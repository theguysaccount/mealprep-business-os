"""Build the static site into dist/.

    python3 pipeline/build.py
    SITE_URL=https://example.org python3 pipeline/build.py

Inputs: data/states/*.json (sourced guides, see pipeline/RESEARCH.md). No network.
"""
import datetime
import hashlib
import html
import json
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import quote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_states import SECTION_KEYS, SECTION_TITLES, STATES, check  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DATA = Path(os.environ.get("MEALPREP_DATA_DIR") or ROOT / "data")
DIST = Path(os.environ.get("BUILD_DIR") or ROOT / "dist")
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/") or "https://theguysaccount.github.io/mealprep-business-os"
BASE = urlparse(SITE_URL).path.rstrip("/") + "/"
REPO_URL = "https://github.com/theguysaccount/mealprep-business-os"
NAME = "Meal Prep Business Kit"
GOATCOUNTER_URL = os.environ.get("GOATCOUNTER_URL", "").strip()
PRO_URL = os.environ.get("PRO_URL", "").strip()
PRO_LABEL = os.environ.get("PRO_LABEL", "").strip()
GOOGLE_SITE_VERIFICATION = os.environ.get("GOOGLE_SITE_VERIFICATION", "").strip()
STALE_DAYS = 400
TODAY = datetime.datetime.now(datetime.timezone.utc).date()
ANSWER = {"no": ("No", "Not from a home kitchen"), "limited": ("Limited", "Only under conditions"), "yes": ("Yes", "Allowed, with conditions")}

e = html.escape


def url(path=""):
    return BASE + path


def absolute(path=""):
    return SITE_URL + "/" + path


def asset(name, _cache={}):
    if name not in _cache:
        digest = hashlib.sha256((SITE / "assets" / name).read_bytes()).hexdigest()[:10]
        _cache[name] = f"{BASE}assets/{name}?v={digest}"
    return _cache[name]


def jsonld(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def json_script(data, id_):
    return f'<script type="application/json" id="{id_}">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def nice_date(iso):
    if len(iso) == 4:
        return iso
    if len(iso) == 7:
        d = datetime.date.fromisoformat(iso + "-01")
        return f"{d.strftime('%B')} {d.year}"
    d = datetime.date.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def slug(name):
    return name.lower().replace(" ", "-")


LOGO = ('<svg viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#1f7a4d"/>'
        '<path d="M7 13h18l-2 11H9z" fill="#fff"/><path d="M11 13c0-4 2-6 5-6s5 2 5 6" fill="none" stroke="#f2b134" stroke-width="2.5"/></svg>')
NAV = [("", "Home"), ("permits/", "Permits by state"), ("build/", "Free order page"), ("about/", "About")]


def shell(*, path, title, description, body, head="", scripts="", index=True):
    canonical = absolute(path)
    robots = "" if index else '<meta name="robots" content="noindex,follow">\n'
    verification = f'<meta name="google-site-verification" content="{e(GOOGLE_SITE_VERIFICATION)}">\n' if GOOGLE_SITE_VERIFICATION and path == "" else ""
    analytics = (f'<script data-goatcounter="{e(GOATCOUNTER_URL)}" async src="https://gc.zgo.at/count.js"></script>\n' if GOATCOUNTER_URL else "")
    current = ' aria-current="page"'
    links = "".join(f'<a href="{url(p)}"{current if p == path or (p and path.startswith(p)) else ""}>{e(label)}</a>' for p, label in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
{robots}{verification}<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(NAME)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{e(absolute('assets/og.png'))}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1f7a4d">
<link rel="icon" href="{url('favicon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{asset('site.css')}">
{head}{analytics}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap"><a class="brand" href="{url()}">{LOGO}{e(NAME)}</a><nav class="top" aria-label="Site">{links}</nav></div></header>
<main id="main"><div class="wrap">
{body}
</div></main>
<footer class="site"><div class="wrap"><nav aria-label="Footer"><a href="{url('permits/')}">Permits by state</a><a href="{url('build/')}">Make an order page</a>
<a href="{url('about/')}">How guides are checked</a><a href="{REPO_URL}/issues/new?template=correction.yml">Report an outdated rule</a><a href="{REPO_URL}">Source on GitHub</a></nav>
<p>Information, not legal advice. Rules change and counties add their own: confirm with your local health department before you sell.
Not affiliated with any government agency.</p></div></footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
{scripts}
</body>
</html>
"""


def write(path, text):
    out = DIST / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def pro_box():
    if not PRO_URL:
        return ""
    return (f'<aside class="box" data-pro><strong>{e(PRO_LABEL or "Want photos and online payment?")}</strong> '
            f'<a href="{e(PRO_URL)}" rel="noopener" target="_blank">See the paid version</a></aside>')


def load_states():
    states, problems = [], []
    for f in sorted((DATA / "states").glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        errs = check(data, f.stem, TODAY + datetime.timedelta(days=1))
        if errs:
            problems += [f"{f.name}: {x}" for x in errs]
        else:
            data["slug"] = slug(data["state"])
            states.append(data)
    if problems:
        raise SystemExit("state guides have problems:\n  " + "\n  ".join(problems))
    states.sort(key=lambda s: s["state"])
    return states


def state_select(states, placeholder="Choose your state"):
    opts = "".join(f'<option value="{url("permits/" + s["slug"] + "/")}">{e(s["state"])}</option>' for s in states)
    return f'<label class="skip" for="jump">State</label><select class="jump" id="jump"><option value="">{e(placeholder)}</option>{opts}</select>'


def page_home(states):
    counts = {k: sum(1 for s in states if s["answer"] == k) for k in ANSWER}
    body = f"""<section class="hero">
<h1>Selling meal prep? Know your state's rules.</h1>
<p class="lead">See which permits your state requires to sell prepared meals, with the agency and date behind every rule. Then make a free order page with your menu, weekly cutoff and delivery ZIP codes. Customers order by text. No signup.</p>
<div class="ctas"><a class="button" href="{url('permits/')}">Permits by state</a><a class="button quiet" href="{url('build/')}" data-track="cta_build">Make a free order page</a></div>
<p>{state_select(states)}</p>
</section>
<ul class="cards">
<li class="card"><h3>Can I sell meal prep from home?</h3><p>Usually not. Cottage food laws cover foods like bread and cookies that don't need refrigeration. Of the {len(states)} guides here, {counts['no']} say no for perishable meals, {counts['limited']} allow it only under conditions, and {counts['yes']} allow it more broadly.</p><p><a href="{url('permits/')}">Compare every state</a></p></li>
<li class="card"><h3>What do I need instead?</h3><p>Most meal preppers cook in a licensed kitchen (their own, a commissary or a shared kitchen) and get a food permit from the county or city health department, plus a food safety certificate.</p></li>
<li class="card"><h3>A free order page in minutes</h3><p>List your meals, prices, order cutoff and pickup or delivery days. You get one link for your Instagram bio or texts. Orders arrive as text messages. Nothing to install, nothing stored.</p><p><a href="{url('build/')}">Make yours</a></p></li>
</ul>
{pro_box()}
<p class="note">Every state guide cites the state agency or statute behind each rule and the date it was checked. This is information, not legal advice: confirm with your local health department before you sell.</p>"""
    data = {"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": absolute(),
            "description": "State-by-state meal prep business permits with sources, and a free no-signup order page builder."}
    write("index.html", shell(path="", title="Meal prep business permits by state, and a free order page",
                              description="Which permits you need to sell meal prep in your state, with the agency and date behind each rule, plus a free order page with weekly cutoffs and delivery ZIPs. No signup.",
                              body=body, head=jsonld(data) + "\n", scripts=f'<script type="module" src="{asset("page.js")}"></script>'))


def page_hub(states):
    rows = "".join(
        f'<li><a href="{url("permits/" + s["slug"] + "/")}"><span>{e(s["state"])}</span><span class="pill {s["answer"]}">{ANSWER[s["answer"]][0]}</span></a></li>'
        for s in states)
    newest = max(s["checked"] for s in states)
    oldest = min(s["checked"] for s in states)
    body = f"""<p class="crumbs"><a href="{url()}">Home</a> › Permits by state</p>
<h1>Meal prep business permits by state</h1>
<p>Can you sell prepared meals made in your home kitchen? The label shows each state's short answer for perishable meals: <span class="pill no">No</span> not from a home kitchen, <span class="pill limited">Limited</span> only under a specific program or conditions, <span class="pill yes">Yes</span> broadly allowed for direct sales. Each guide explains the rules, the licensed-kitchen route, food safety certificates and business registration, citing the state source for every point.</p>
<p>{state_select(states, "Jump to a state")}</p>
<ul class="states">{rows}</ul>
<div class="notice"><strong>Information, not legal advice.</strong> Guides were checked between {nice_date(oldest)} and {nice_date(newest)}. Counties and cities often add their own rules, so confirm with your local health department before you sell. Spotted an outdated rule? <a href="{REPO_URL}/issues/new?template=correction.yml">Tell us</a>.</div>
<h2>Why most meal prep can't be made at home</h2>
<p>Prepared meals are "time/temperature control for safety" food (also called potentially hazardous food): they need refrigeration to stay safe. Most states' cottage food laws, which let people sell some foods from a home kitchen, cover only foods that are shelf-stable, like bread, cookies, jams and dry mixes. Meals usually have to come from a permitted food establishment: a licensed commercial kitchen, a commissary or a shared kitchen you rent by the hour.</p>
<h2>What a licensed meal prep business usually needs</h2>
<ul><li>A food establishment or food service permit from the county or city health department (in some states, from a state agency).</li>
<li>A licensed kitchen to cook in, and often a plan review before the permit.</li>
<li>A certified food protection manager, and in some places food handler cards for staff.</li>
<li>A registered business and a sales tax account where prepared food is taxable.</li></ul>
<p>Each state's guide links to the official pages for these.</p>"""
    data = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Meal prep business permits by state", "url": absolute("permits/"),
            "mainEntity": {"@type": "ItemList", "numberOfItems": len(states), "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "url": absolute("permits/" + s["slug"] + "/"), "name": s["state"]} for i, s in enumerate(states)]}}
    write("permits/index.html", shell(path="permits/", title="Meal prep business permits by state (with sources)",
                                      description="Can you sell meal prep from home in your state? A sourced, dated guide for every state: cottage food limits, the licensed kitchen route, food safety certificates and registration.",
                                      body=body, head=jsonld(data) + "\n", scripts=f'<script type="module" src="{asset("page.js")}"></script>'))


def source_line(s):
    upd = f", page dated {nice_date(s['updated'])}" if s.get("updated") else ""
    how = "" if s["read"] == "fetched" else " (read from the agency's search listing)"
    return (f'{e(s["agency"])}: <a href="{e(s["url"])}" rel="noopener" target="_blank">{e(s["title"])}</a>{upd}. '
            f'Checked <time datetime="{s["checked"]}">{nice_date(s["checked"])}</time>{how}.')


def page_state(s, states):
    sections = ""
    faq = []
    for sec in s["sections"]:
        if not sec["points"]:
            continue
        key = sec["key"]
        # number the sources page-wide so footnotes are unique
        items = ""
        for p in sec["points"]:
            refs = "".join(f'<sup><a href="#{key}-s{i + 1}" aria-label="source {i + 1}">[{i + 1}]</a></sup>' for i in p["src"])
            items += f"<li>{e(p['text'])}{refs}</li>"
        srcs = "".join(f'<li id="{key}-s{i + 1}">[{i + 1}] {source_line(src)}</li>' for i, src in enumerate(sec["sources"]))
        sections += (f'<section class="rule" id="{key}"><h2>{e(SECTION_TITLES[key])}</h2><ul>{items}</ul>'
                     f'<ol class="src" aria-label="Sources">{srcs}</ol></section>')
        faq.append({"@type": "Question", "name": f"{SECTION_TITLES[key]} in {s['state']}",
                    "acceptedAnswer": {"@type": "Answer", "text": " ".join(p["text"] for p in sec["points"])}})
    loc = s["local"]
    age = (TODAY - datetime.date.fromisoformat(s["checked"])).days
    stale = (f'<div class="notice"><strong>This guide is due for a re-check.</strong> It was last checked on {nice_date(s["checked"])}. '
             f'Rules may have changed since.</div>' if age > STALE_DAYS else "")
    label, sub = ANSWER[s["answer"]]
    others = [o for o in states if o["abbr"] != s["abbr"]]
    neighbours = "".join(f'<li><a href="{url("permits/" + o["slug"] + "/")}"><span>{e(o["state"])}</span><span class="pill {o["answer"]}">{ANSWER[o["answer"]][0]}</span></a></li>'
                         for o in others if o["answer"] != "no")
    build_link = url("build/") + "?state=" + s["abbr"]
    body = f"""<p class="crumbs"><a href="{url()}">Home</a> › <a href="{url('permits/')}">Permits by state</a> › {e(s["state"])}</p>
<h1>{e(s["state"])} meal prep business: permits and licenses</h1>
<div class="box answer {s['answer']}"><span class="pill {s['answer']}">{label}: {e(sub.lower())}</span>
<p><strong>Can you sell meal prep made in a home kitchen in {e(s["state"])}?</strong> {e(s["answer_text"])}</p></div>
<div class="notice"><strong>Information, not legal advice.</strong> Checked on <time datetime="{s['checked']}">{nice_date(s['checked'])}</time> against the sources listed under each section. Counties and cities can add rules: confirm with your local health department before you sell.</div>
{stale}
{sections}
<section class="rule" id="local"><h2>Your local health department</h2><ul><li>{e(loc["text"])}<sup><a href="#local-s1">[1]</a></sup></li></ul>
<ol class="src" aria-label="Sources"><li id="local-s1">[1] {source_line(loc["source"])}</li></ol></section>
<div class="tint"><h2 style="margin-top:0">Taking orders?</h2><p>Make a free order page for your menu: weekly cutoff, pickup and delivery days, delivery ZIP codes, orders by text. One link, no signup.</p>
<a class="button" href="{build_link}" data-track="state_to_build">Make my order page</a></div>
{pro_box()}
<p class="note">Spotted something outdated? <a href="{REPO_URL}/issues/new?template=correction.yml&amp;title={quote('Correction: ' + s['state'])}">Report it</a> and it gets re-checked.</p>
<h2>States that allow home-kitchen meals in some form</h2>
<ul class="states">{neighbours or '<li>None in this list.</li>'}</ul>"""
    desc = f"Can you sell meal prep from home in {s['state']}? {s['answer_text']} Sourced and dated, with the permits, certificates and registration a meal prep business needs."
    if len(desc) > 300:
        desc = desc[:297].rsplit(" ", 1)[0] + "…"
    here = absolute(f"permits/{s['slug']}/")
    data = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": f"Can you sell meal prep made in a home kitchen in {s['state']}?",
                 "acceptedAnswer": {"@type": "Answer", "text": s["answer_text"]}}] + faq},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": NAME, "item": absolute()},
                {"@type": "ListItem", "position": 2, "name": "Permits by state", "item": absolute("permits/")},
                {"@type": "ListItem", "position": 3, "name": s["state"], "item": here}]}]
    write(f"permits/{s['slug']}/index.html", shell(
        path=f"permits/{s['slug']}/", title=f"{s['state']} meal prep business license and permits (checked {nice_date(s['checked'])})",
        description=desc, body=body, head="".join(jsonld(d) + "\n" for d in data),
        scripts=f'<script type="module" src="{asset("page.js")}"></script>'))


def page_build(states):
    st_opts = '<option value="">Choose your state</option>' + "".join(f'<option value="{s["abbr"]}">{e(s["state"])}</option>' for s in states)
    tz_opts = "".join(f'<option value="{v}">{e(k)}</option>' for k, v in [
        ("Eastern", "America/New_York"), ("Central", "America/Chicago"), ("Mountain", "America/Denver"), ("Arizona", "America/Phoenix"),
        ("Pacific", "America/Los_Angeles"), ("Alaska", "America/Anchorage"), ("Hawaii", "Pacific/Honolulu")])
    days = "".join(f'<option value="{i}">{d}</option>' for i, d in enumerate(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]))
    body = f"""<p class="crumbs"><a href="{url()}">Home</a> › Free order page</p>
<h1>Make a free meal prep order page</h1>
<p>Fill this in and get one link to share. Customers pick meals, choose pickup or delivery, and send you the order as a text. Your menu lives inside the link: nothing is uploaded or stored, and there's no account. To change the menu later, keep the edit link.</p>
<p><button type="button" class="quiet small" id="sample">Try it with a sample menu</button></p>
<form class="builder" novalidate>
<fieldset><legend>Your business</legend>
<div class="field"><label for="bizName">Business name</label><input type="text" id="bizName" name="bizName" maxlength="80" autocomplete="organization"></div>
<div class="row"><div class="field"><label for="phone">Mobile number for orders</label><input type="tel" id="phone" name="phone" autocomplete="tel" placeholder="512-555-0142"><small>Orders arrive as texts to this number. It is shown to customers.</small></div>
<div class="field"><label for="email">Email (if no mobile)</label><input type="email" id="email" name="email" autocomplete="email"></div></div>
<div class="row"><div class="field"><label for="state">State</label><select id="state" name="state">{st_opts}</select></div>
<div class="field"><label for="tz">Time zone</label><select id="tz" name="tz">{tz_opts}</select></div></div>
</fieldset>
<fieldset><legend>Weekly order cutoff</legend>
<div class="row"><div class="field"><label for="cutDay">Orders close on</label><select id="cutDay" name="cutDay">{days}</select></div>
<div class="field"><label for="cutTime">at</label><input type="text" id="cutTime" name="cutTime" value="20:00" pattern="[0-2]?[0-9]:[0-5][0-9]" inputmode="numeric"><small>24-hour time, e.g. 20:00</small></div></div>
</fieldset>
<fieldset><legend>Pickup and delivery</legend>
<div id="ful"></div>
<p><button type="button" class="quiet small" id="add-ful">Add another pickup or delivery option</button></p>
<div class="field"><label for="zips">Delivery ZIP codes</label><input type="text" id="zips" name="zips" placeholder="78701, 78702, 78704"><small>Only needed if you deliver. Orders from other ZIP codes can't be sent.</small></div>
<div class="row"><div class="field"><label for="fee">Delivery fee ($)</label><input type="number" id="fee" name="fee" min="0" step="0.01" inputmode="decimal"></div>
<div class="field"><label for="min">Minimum order ($)</label><input type="number" id="min" name="min" min="0" step="0.01" inputmode="decimal"></div></div>
</fieldset>
<fieldset><legend>Menu</legend>
<div id="items"></div>
<p><button type="button" class="quiet small" id="add-item">Add a dish</button></p>
</fieldset>
<fieldset><legend>Details for customers</legend>
<div class="field"><label for="pay">How customers pay</label><input type="text" id="pay" name="pay" maxlength="160" placeholder="Cash or card at pickup"><small>This page doesn't take payments.</small></div>
<div class="field"><label for="note">Note for customers</label><textarea id="note" name="note" maxlength="400" placeholder="Storage and reheating instructions, allergens, how long meals keep"></textarea></div>
<div class="field"><label for="lic">Permit or license line (optional)</label><input type="text" id="lic" name="lic" maxlength="120" placeholder="Prepared in a permitted kitchen, permit #… (County)"></div>
</fieldset>
<div class="box"><label class="checks"><input type="checkbox" name="permits"> I have, or will get before I sell, the permits my state and county require for the food I list. <a id="guide-link" href="{url('permits/')}" hidden>What my state requires</a></label></div>
<ul class="problems" id="problems" aria-live="polite"></ul>
<p><button type="submit" id="make" disabled>Make my order link</button></p>
</form>
<section class="box result" id="result" hidden>
<h2 style="margin-top:0">Your order page is ready</h2>
<div class="field"><label for="link">Order link: share this</label><textarea id="link" name="link" readonly></textarea></div>
<p class="ctas"><button type="button" data-copy-link>Copy link</button><a class="button quiet" data-open href="#" target="_blank" rel="noopener">Open my order page</a><button type="button" class="quiet" data-share>Share</button></p>
<p class="notice" id="toolong" hidden>This link is long. It works in browsers and most apps, but some text-message apps cut long links. Shorter dish descriptions make it shorter.</p>
<div class="field"><label for="edit">Edit link: keep this private, it opens your menu here to change it</label><textarea id="edit" data-edit readonly></textarea></div>
<p><button type="button" class="quiet small" data-copy-edit>Copy edit link</button></p>
<p class="note">Put the order link in your Instagram or TikTok bio, your link-in-bio page, or a text to regulars. When the menu changes, open the edit link, change it, and share the new link.</p>
</section>
{pro_box()}"""
    cfg = {"base": BASE, "states": [{"abbr": s["abbr"], "name": s["state"], "slug": s["slug"]} for s in states]}
    script = ("<script>(function(){var s=new URLSearchParams(location.search).get('state');var c=document.getElementById('cfg');"
              "if(s&&/^[A-Z]{2}$/.test(s)){var d=JSON.parse(c.textContent);d.defaultState=s;c.textContent=JSON.stringify(d);}})();</script>")
    write("build/index.html", shell(path="build/", title="Free meal prep order page maker (no signup)",
                                    description="Make a free order page for your meal prep business: menu, prices, weekly order cutoff, pickup and delivery days, delivery ZIP codes. Customers order by text. No signup, nothing stored.",
                                    body=body, scripts=json_script(cfg, "cfg") + "\n" + script + f'\n<script type="module" src="{asset("builder.js")}"></script>'))


def page_order():
    body = '<div id="order"><p>Loading the menu…</p><noscript><p>This order page needs JavaScript.</p></noscript></div>'
    cfg = {"base": BASE}
    write("order/index.html", shell(path="order/", title="Order meal prep", description="A meal prep menu and order page.", body=body, index=False,
                                    scripts=json_script(cfg, "cfg") + f'\n<script type="module" src="{asset("order.js")}"></script>'))


def page_about(states):
    body = f"""<h1>About the Meal Prep Business Kit</h1>
<p>Two free tools for people who cook and sell meals: a guide to each state's rules, and an order page that takes orders by text. No accounts and no fees.</p>
<h2 id="method">How the state guides are researched</h2>
<ul><li>Every point on a state page cites a state government source: the agency's own page, the statute or the administrative rule. Law firm posts and blogs are not used as sources.</li>
<li>Each source shows the date it was checked, and the date the page or rule shows when it shows one.</li>
<li>Guides are written with AI assistance from those sources and re-checked on a schedule. A monthly job tests every cited link; a guide older than about a year shows a re-check notice.</li>
<li>Guides describe what the sources say. They don't tell anyone they may legally sell food. Counties and cities add their own rules, so the local health department has the final word.</li></ul>
<h2>Not legal advice</h2>
<p>This site is information, not legal advice, and it is not a government site. Before you sell food, confirm the requirements with your local health department, and with a lawyer if you're unsure.</p>
<h2>The order page and your privacy</h2>
<p>An order page keeps the whole menu inside its link, after the # sign, which browsers never send to any server. Customer orders go out as text messages (or emails) that customers send themselves. This site stores nothing and sees nothing. {"Page visits are counted with GoatCounter, which stores no personal data." if GOATCOUNTER_URL else "The site does not count visits."}</p>
<h2>Corrections</h2>
<p>If a rule is out of date or wrong, <a href="{REPO_URL}/issues/new?template=correction.yml">open a correction</a> with a link to the official source. Corrections are re-checked against the source before the page changes.</p>
<h2>Open source</h2>
<p>The code and the guides are <a href="{REPO_URL}">on GitHub</a>. Guide text is CC BY 4.0.</p>"""
    write("about/index.html", shell(path="about/", title="About: how the meal prep permit guides are researched",
                                    description="How the state meal prep permit guides are sourced and dated, why they aren't legal advice, and how the no-signup order page keeps your data private.",
                                    body=body))


def page_404():
    body = f'<h1>That page isn\'t here</h1><p><a href="{url("permits/")}">Permits by state</a> · <a href="{url("build/")}">Make a free order page</a></p>'
    write("404.html", shell(path="404.html", title="Page not found", description="Page not found.", body=body, index=False))


def write_static(states):
    shutil.copytree(SITE / "assets", DIST / "assets", dirs_exist_ok=True)
    shutil.copy(SITE / "favicon.svg", DIST / "favicon.svg")
    key = (SITE / "indexnow-key.txt").read_text().strip()
    write(f"{key}.txt", key)
    pages = ["", "permits/"] + [f"permits/{s['slug']}/" for s in states] + ["build/", "about/"]
    lastmod = {f"permits/{s['slug']}/": s["checked"] for s in states}
    newest = max(s["checked"] for s in states)
    items = "".join(f"<url><loc>{e(absolute(p))}</loc><lastmod>{lastmod.get(p, newest)}</lastmod></url>\n" for p in pages)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: {BASE}order/\n\nSitemap: {absolute('sitemap.xml')}\n")
    write("urls.txt", "\n".join(absolute(p) for p in pages) + "\n")
    sources = []
    for s in states:
        for sec in s["sections"]:
            for src in sec["sources"]:
                sources.append({"state": s["abbr"], "section": sec["key"], **src})
        sources.append({"state": s["abbr"], "section": "local", **s["local"]["source"]})
    write("data/states.json", json.dumps({"built": TODAY.isoformat(), "license": "CC BY 4.0", "states": [
        {k: v for k, v in s.items() if k != "slug"} | {"page": absolute(f"permits/{s['slug']}/")} for s in states]}, ensure_ascii=False))
    write("data/meta.json", json.dumps({"built": TODAY.isoformat(), "states": len(states), "sources": len(sources),
                                        "oldest_check": min(s["checked"] for s in states), "newest_check": newest,
                                        "sample_state": states[0]["slug"]}, indent=1))


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    states = load_states()
    if not states:
        raise SystemExit("no state guides in data/states")
    write_static(states)
    page_home(states)
    page_hub(states)
    for s in states:
        page_state(s, states)
    page_build(states)
    page_order()
    page_about(states)
    page_404()
    print(f"built {sum(1 for _ in DIST.rglob('*.html'))} pages: {len(states)} state guides; site {SITE_URL}")


if __name__ == "__main__":
    build()
