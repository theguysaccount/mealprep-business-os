# Meal Prep Business Kit

Two free tools for people who cook and sell meals:

1. **Permits by state.** For all 50 states and DC: can you sell meal prep made at home, what cottage food law covers,
   the licensed-kitchen route, food safety certificates, and registration. Every point cites the state agency or
   statute and the date it was checked. Information, not legal advice.
2. **A free order page.** Menu, prices, weekly order cutoff, pickup and delivery days, delivery ZIP codes. Customers
   order by text message. No signup: the whole menu lives inside the link.

**Live:** https://theguysaccount.github.io/mealprep-business-os/

## Run, test, deploy

```bash
python3 pipeline/build.py               # build into dist/
scripts/e2e.sh                          # serve dist/ under the production path and drive it in headless Chrome
python3 -m unittest discover -s tests   # build and guide tests
node --test tests/js/*.test.mjs         # order links, cutoffs, totals, messages
python3 pipeline/validate_states.py data/states
```

GitHub Actions deploys on every push to `main` (`.github/workflows/deploy.yml`). `OPERATIONS.md` covers every job,
how it fails safe, and the switches (domain, paid version, analytics). `pipeline/RESEARCH.md` is the brief for
writing and re-checking a state guide.

## Licenses

Code: MIT. Guide text: CC BY 4.0. Sources are linked on each page and belong to their agencies.
