# Research brief: state meal-prep licensing guides

This is the brief for writing and re-checking `data/states/<XX>.json`, whether by an agent session or by hand.
Each file becomes the public page "<State> meal prep business: permits and licenses". Readers are people who want
to cook meals and sell them (weekly meal prep, ready-to-eat or reheat meals). Every rule on the page must cite a
state government source and the date it was checked. The pages are information, not legal advice, and send
readers to their local health department to confirm.

## What to find for each state

1. **Home kitchen.** Can someone make perishable prepared meals at home and sell them? Prepared meals need
   refrigeration (time/temperature control for safety, "TCS" or "potentially hazardous" food), which most cottage
   food laws exclude. Look for: the cottage food law's food list; any home-kitchen meal program (California's
   microenterprise home kitchen operations, Utah's microenterprise home kitchens, "food freedom" laws in states such
   as Wyoming, North Dakota, Montana and others) and its conditions (county opt-in, permit, caps, direct sale only).
2. **Cottage food.** What can be sold from a home kitchen (non-perishable foods), whether registration, a permit,
   training or labels are required, sales caps, and where sales may happen (in person, online, delivery).
3. **Licensed kitchen route.** How a meal-prep business sells prepared meals legally: who issues the food
   establishment / food service / retail food permit (state agency, or county and city health departments), whether
   a commercial, commissary or shared kitchen is required, and plan review if the source mentions it.
4. **Food safety certificates.** Whether a certified food protection manager (CFPM) is required, and whether
   employees need food handler cards (statewide, or only in some counties).
5. **Business basics.** Registering the business (Secretary of State) and collecting sales tax on prepared food
   (state revenue or tax department).
6. **Local health departments.** A state page that lists or links to local health departments.

## Rules

- Sources must be state (or federal) government websites: domains ending in `.gov` or `.us`, including the state
  legislature or code website. Not law firms, blogs, Forrager, Institute for Justice, Wikipedia or AI summaries. Use
  those only to find the official page, then cite the official page.
- Read the page before you cite it. Fetch it (curl with the User-Agent
  `mealprep-business-os-research/1.0 (+https://github.com/theguysaccount/mealprep-business-os)`); if a site refuses
  scripts, you may rely on the search result's text of that same official page and mark the source `"read": "search"`.
  Never try to get around a refusal (no browser user agents, no proxies, no archive copies of blocked pages).
- Write plain English. Be precise and modest: say "your county or city health department issues the permit" rather
  than guessing a fee. Include numbers (sales caps, fees, hours of training) only when the source states them, and
  say which year the source gives when it gives one.
- Never tell a reader they are allowed to do something. Describe what the law and agency say ("The state's cottage
  food law does not cover meals that need refrigeration"). No legal advice, no "you should".
- Every point cites at least one source by index. Every source records the agency, the page title, the URL, the
  date you checked it, and the date the page shows as updated or effective if it shows one.
- If you can't find an official source for something, leave the point out. A short, sourced page beats a full,
  guessed one.

## File format (`data/states/XX.json`, XX = postal code)

```json
{
  "state": "Texas",
  "abbr": "TX",
  "checked": "2026-11-22",
  "answer": "no",
  "answer_text": "Texas's cottage food law covers foods that don't need refrigeration, so meals sold for reheating must be made in a permitted food establishment.",
  "sections": [
    {"key": "home", "points": [{"text": "…", "src": [0]}], "sources": [
      {"agency": "Texas Department of State Health Services", "title": "Cottage Food Production Operations", "url": "https://www.dshs.texas.gov/…",
       "kind": "agency", "checked": "2026-11-22", "updated": null, "read": "fetched"}]},
    {"key": "cottage", "points": [], "sources": []},
    {"key": "kitchen", "points": [], "sources": []},
    {"key": "training", "points": [], "sources": []},
    {"key": "business", "points": [], "sources": []}
  ],
  "local": {"text": "Food establishment permits are issued by …", "source": {"agency": "…", "title": "…", "url": "…", "kind": "agency", "checked": "2026-11-22", "updated": null, "read": "fetched"}}
}
```

- `answer`: `no` (perishable prepared meals can't be sold from a home kitchen under state law), `limited` (only under
  a specific program or conditions: county opt-in, a permit, caps, direct sales only), or `yes` (state law broadly
  allows home-made perishable meals sold directly to consumers, with or without registration).
- `answer_text`: 1 to 3 sentences that explain the answer, based only on the sources.
- `sections`: exactly these five keys in this order: `home`, `cottage`, `kitchen`, `training`, `business`. Each has
  1 to 6 points (each point 8 to 70 words) and its own `sources` list; `src` holds indexes into that list.
- `kind`: `agency` (an agency page or PDF), `statute` (the code or a bill), `rule` (administrative code).
- `checked`: YYYY-MM-DD, the day you read it. `updated`: YYYY-MM-DD or YYYY or null.
- `read`: `fetched` or `search`.

Validate with `python3 pipeline/validate_states.py data/states/XX.json` (or a folder) and fix what it reports.
