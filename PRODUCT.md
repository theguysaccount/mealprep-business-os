# Product: Meal Prep Business Kit

**The user.** Someone who cooks meals to sell (weekly meal prep, ready-to-heat dinners), usually starting from
Instagram DMs and a spreadsheet, often unsure whether they can legally cook at home.

**The painful job.** Finding out, for their state, what permits apply to perishable prepared meals (most cottage food
laws exclude them), then taking weekly orders without a pile of DMs.

**The promise.** One page that says what your state requires, with the official source and date behind every rule;
and a free order page with your menu, cutoff and delivery ZIPs in minutes, with orders arriving as texts.

**The wedge.** People search "[state] meal prep business license". Each state page answers that with sources, then
offers the order page. Every order page carries "make your own free order page", so each seller's customers see it.

**Why now.** Meal prep sellers are numerous and small; the incumbents (GoPrep, Sprwt, Shopify apps) are paid SaaS.
A no-signup link-only order page costs nothing to run.

**The one activation metric.** A seller makes an order link (`link_created`), then a customer sends an order from it
(`order_sent`). Counted once analytics is on (OPERATIONS.md, key 4).

**First revenue event.** A seller upgrades to a paid tier with photos and online payment (`PRO_URL`, on other hosting).

**What v1 deliberately won't do.** No accounts, no payments, no stored orders, no AI landing-page generator from dish
photos (needs a server and a model), no certification or legal advice, no claims that a seller is compliant.
