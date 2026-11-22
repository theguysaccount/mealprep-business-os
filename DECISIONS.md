# Decisions

Defaults picked without blocking on Jack. Each can be reversed.

1. **Guides plus order page, not "ServiceTitan".** The note's full vision (landing pages, menus, ordering, certification)
   needs accounts, payments and a server. Machine mode on GitHub Pages allows a static site, so v1 is the two parts that
   work without one: sourced licensing guides (the search wedge) and a no-signup order page (the activation).
2. **"Certification" means information, not certifying.** The open question (food handler, kitchen license or nutrition
   claims?) is settled by describing all the state-level requirements with sources and sending readers to their local
   health department. The site never says a seller is compliant, and the builder asks sellers to confirm they have the
   permits their state and county require before it makes a link.
3. **Only official sources.** Every point cites a `.gov` or `.us` page (agency, statute or rule) with the date it was
   checked. Secondary compilations were used, at most, to find official pages. The validator rejects anything else.
4. **Short answers are about perishable meals.** Each guide's label (No / Limited / Yes) answers one question: can
   meals that need refrigeration be made in a home kitchen and sold under state law? That's the question meal preppers
   have, and the one cottage food summaries usually blur.
5. **State rules only.** Counties and cities add rules (permits, zoning, fees). Every page says so and points to the
   local health department.
6. **The menu lives in the link.** Deflate-compressed JSON after `#`, which browsers never send to a server. No
   database, no accounts, no privacy policy burden; editing means opening the private edit link and sharing a new one.
7. **Orders by text message.** An `sms:` link prefilled with the order (email when there's no mobile number). The seller
   gets orders where they already work, and nothing is stored here. No payments (Pages is non-commercial).
8. **No AI landing-page generator from photos.** It needs a model and a server; left for a paid tier on other hosting.
9. **Brand "Meal Prep Business Kit".** Plain and searchable; the repo name stays for continuity.

## Questions for Jack (none block the site)

- Is a paid tier (photos, online payment, order inbox) worth building on other hosting?
- Should the ASI House meal-prep service be a first user of the order page?
