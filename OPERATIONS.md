# Operations

The Meal Prep Business Kit is a static site on GitHub Pages: sourced state guides (`data/states/*.json`) built into
pages, plus an order-page builder whose menus live entirely inside the links people share. There is no server,
database, account or payment. GitHub Actions runs everything recurring.

**Live:** https://theguysaccount.github.io/mealprep-business-os/
**Repo:** https://github.com/theguysaccount/mealprep-business-os

## Automated jobs

| Job | Workflow | When | What it does | How it fails safe |
|---|---|---|---|---|
| Build and deploy | `deploy.yml` | every push to `main`, Mondays 07:23 UTC, by hand | Python tests (build, guide validation), Node tests (order links, cutoffs, totals, messages), validates every guide against `pipeline/RESEARCH.md` (official `.gov`/`.us` sources only, a checked date on every source), builds, drives five pages in headless Chrome (makes a link from the sample menu, places pickup and delivery orders, checks the guides), deploys, runs the same checks live, pings IndexNow. The weekly run refreshes the "due for a re-check" notices. | Any failure stops before deploy; the last good site stays live. Re-running is always safe. |
| Weekly self-test | `selftest.yml` | Wednesdays 13:41 UTC, by hand | Tests; the end-to-end checks on the **live** site; every sitemap page answers 200 with its canonical URL; the data files agree; warns about guides last checked more than a year ago. Then the keep-alive. | Failure opens (or comments on) one `ops-alert` issue; GitHub emails the owner. The site is untouched. |
| Monthly source check | `sources.yml` | the 3rd of each month, 09:13 UTC | Requests every cited source once, 2 seconds apart. Broken links (404/410) go into one `source-check` issue naming the guides that cite them. | Sites that refuse scripts (many state sites do) are listed, not treated as errors. The site is never touched. |
| Keep-alive | `selftest.yml` → `scripts/keepalive.sh` | weekly | Re-enables scheduled workflows (except any turned off by hand); empty `[skip ci]` commit after 45 quiet days. | Keeps schedules alive past GitHub's 60-day cutoff. |

GitHub fires scheduled runs on this account hours late and sometimes skips them; nothing here depends on timing.

## What to watch

- `ops-alert` issues (the live site or a test broke), `source-check` issues (a cited page moved or vanished), and
  `correction` issues (a reader says a rule is outdated). The re-check routine (key 1) handles the last two.
- A guide's page shows "due for a re-check" once its check date is over 400 days old.

## Keys Jack can turn later

### 1. Monthly re-check routine (keeps the guides current)

Guides can't be researched inside Actions (no AI key). Schedule a Claude Code routine (claude.ai/code → Routines) for
the 5th of each month on this repo:

> In theguysaccount/mealprep-business-os: read `pipeline/RESEARCH.md`. Re-check the 5 state guides in `data/states/`
> with the oldest `checked` dates, plus every state named in an open `source-check` or `correction` issue. For each,
> re-read every cited source, fix what changed (new laws, moved pages, new programs), set every `checked` date to
> today, and validate with `python3 pipeline/validate_states.py data/states`. Never cite non-government sources; never
> get around a site that refuses scripts. Run `python3 -m unittest discover -s tests` and `node --test tests/js/*.test.mjs`,
> commit, push, and close the issues you resolved with a note of what changed.

### 2. Custom domain

The base URL is one setting: the repository variable `SITE_URL`. Canonical URLs, the sitemap, robots.txt, structured
data, order links made from then on, IndexNow and the self-tests all follow it. To move the site:

1. DNS (owned by the domain rollout; not done here). Subdomain: `CNAME <name> → theguysaccount.github.io`. Apex:
   `A @ → 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153`, `AAAA @ → 2606:50c0:8000::153,
   2606:50c0:8001::153, 2606:50c0:8002::153, 2606:50c0:8003::153`, `CNAME www → theguysaccount.github.io`.
2. `gh api -X PUT repos/theguysaccount/mealprep-business-os/pages -f cname=<domain>`, then once the certificate is
   issued `gh api -X PUT repos/theguysaccount/mealprep-business-os/pages -F https_enforced=true`.
3. `gh variable set SITE_URL -b https://<domain> -R theguysaccount/mealprep-business-os`
4. `gh workflow run deploy.yml -R theguysaccount/mealprep-business-os`

Order links already shared keep working: GitHub redirects the old `github.io` path to the domain, and the menu after
`#` survives the redirect. Domain ideas are in `LAUNCH.md`.

### 3. Money: the paid version

Pages is non-commercial, so the free tools stay free and there's no checkout. One slot is built in: a "paid version"
box on the home page, the builder and every state guide, hidden until set. A paid tier (photos, online payment, order
inbox) needs other hosting plus Stripe. When it exists, set `PRO_URL` (and optionally `PRO_LABEL`) as repository
variables and redeploy.

### 4. Analytics

Off by default. Create a GoatCounter site (cookieless), set `GOATCOUNTER_URL` = `https://<code>.goatcounter.com/count`,
redeploy. Events in the code: `link_created` (**activation**: a seller made an order link), `link_copied`,
`link_shared`, `order_page_view`, `order_sent` (**the value event**: a customer sent an order), `own_from_order`
(**the loop**: a customer clicked "make your own"), `state_pick`, `state_to_build`, `cta_build`, `sample`.

### 5. Search Console

Set `GOOGLE_SITE_VERIFICATION` (the content of Google's meta tag) and redeploy, then submit `/sitemap.xml`. Bing and
Yandex get every deploy through IndexNow; the account's root robots.txt lists the sitemap.

## Running it by hand

```bash
python3 -m unittest discover -s tests -v
node --test tests/js/*.test.mjs
python3 pipeline/validate_states.py data/states
python3 pipeline/build.py && scripts/e2e.sh
scripts/e2e.sh https://theguysaccount.github.io/mealprep-business-os/
python3 scripts/check_live.py https://theguysaccount.github.io/mealprep-business-os
python3 scripts/check_sources.py            # slow: every cited source, 2 s apart
node scripts/fixture.mjs > tests/fixtures/order-link.txt   # after changing the sample menu or the link format
```
