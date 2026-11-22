// End-to-end self-tests, loaded only with ?selftest=1. Each drives the real page and writes its verdict to
// <html data-selftest="pass|fail"> plus a <pre id="selftest"> log, which scripts/e2e.sh reads from headless
// Chrome. Expectations come from the page's own data, never from fixed launch-day text.
import { decodeMenu, totals, money, problems, SAMPLE, clean } from "./order-core.js";

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
async function until(fn, what, ms = 15000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    const v = await fn();
    if (v) return v;
    await wait(25);
  }
  throw new Error("timed out waiting for " + what);
}

function finish(log, error) {
  const pre = document.createElement("pre");
  pre.id = "selftest";
  pre.textContent = (error ? "FAIL: " + (error.stack || error.message || error) + "\n" : "") + log.join("\n");
  document.body.append(pre);
  document.documentElement.dataset.selftest = error ? "fail" : "pass";
}

function fire(input, value) {
  input.value = value;
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

export async function builder(ctx) {
  const log = [];
  try {
    const make = document.getElementById("make");
    if (!make.disabled) throw new Error("an empty form must not make a link");
    document.getElementById("sample").click();
    ctx.form.elements.permits.checked = true;
    ctx.form.elements.permits.dispatchEvent(new Event("change", { bubbles: true }));
    await until(() => !make.disabled, "the make-link button to enable");
    make.click();
    const length = Number(await until(() => ctx.out.dataset.ready, "the link"));
    const link = ctx.out.querySelector("[name=link]").value;
    const menu = await decodeMenu(new URL(link).hash);
    const want = clean(SAMPLE);
    if (JSON.stringify(menu.items) !== JSON.stringify(want.items) || menu.n !== want.n || menu.ph !== want.ph) throw new Error("link does not hold the menu");
    if (problems(menu).length) throw new Error("sample menu has problems: " + problems(menu).join("; "));
    if (!new URL(link).pathname.endsWith("/order/")) throw new Error("link should open the order page: " + link);
    const edit = ctx.out.querySelector("[data-edit]").value;
    if (new URL(edit).hash !== new URL(link).hash || !new URL(edit).pathname.endsWith("/build/")) throw new Error("edit link is wrong");
    log.push(`link ${length} characters, ${menu.items.length} dishes, edit link ok`);
    finish(log);
  } catch (error) {
    finish(log, error);
  }
}

export async function order(ctx) {
  const log = [];
  try {
    if (!ctx.menu) throw new Error("the order link did not open");
    const dishes = document.querySelectorAll("[data-dish]");
    if (dishes.length !== ctx.menu.items.length) throw new Error(`${dishes.length} dishes shown, ${ctx.menu.items.length} in the link`);
    const send = document.getElementById("send");
    if (send.getAttribute("aria-disabled") !== "true") throw new Error("an empty order must not be sendable");
    const first = ctx.menu.items.findIndex((i) => !i.sold);
    const plus = dishes[first].querySelector("button[aria-label^='One more']");
    const need = ctx.menu.min ? Math.ceil(ctx.menu.min / ctx.menu.items[first].p) : 1;
    for (let i = 0; i < Math.max(2, need); i++) plus.click();
    const choice = document.getElementById("ful-choice");
    const pickup = ctx.menu.ful.findIndex((f) => f.t === "pickup");
    const delivery = ctx.menu.ful.findIndex((f) => f.t === "delivery");
    fire(document.getElementById("c-name"), "Self Test");
    if (pickup >= 0) {
      fire(choice, String(pickup));
      await until(() => send.getAttribute("aria-disabled") === "false", "a sendable pickup order");
      const t = totals(ctx.menu, ctx.cart, "pickup");
      if (!send.dataset.body.includes(`${ctx.cart[first]} x ${ctx.menu.items[first].n}`)) throw new Error("message misses the dish");
      if (!send.dataset.body.includes(`total ${money(t.total)}`)) throw new Error("message misses the total");
      if (!send.href.startsWith(ctx.menu.ph ? "sms:" : "mailto:")) throw new Error("send link is not a text or email: " + send.href.slice(0, 30));
      log.push(`pickup order ok: ${ctx.cart[first]} meals, ${money(t.total)}`);
    }
    if (delivery >= 0 && ctx.menu.zips.length) {
      fire(choice, String(delivery));
      fire(document.getElementById("c-zip"), "00000");
      await until(() => send.getAttribute("aria-disabled") === "true", "a refused ZIP");
      fire(document.getElementById("c-zip"), ctx.menu.zips[0]);
      fire(document.getElementById("c-address"), "1 Test St");
      await until(() => send.getAttribute("aria-disabled") === "false", "an accepted ZIP");
      if (!send.dataset.body.includes(`Deliver to: 1 Test St ${ctx.menu.zips[0]}`)) throw new Error("message misses the address");
      log.push("delivery ZIP check ok");
    }
    const own = document.querySelector("[data-own]");
    if (!own || !own.href.includes("/build/")) throw new Error("no make-your-own link");
    log.push("make-your-own link ok");
    finish(log);
  } catch (error) {
    finish(log, error);
  }
}

export async function page() {
  const log = [];
  try {
    const h1 = document.querySelector("h1");
    if (!h1 || !h1.textContent.trim()) throw new Error("no h1");
    const canonical = document.querySelector('link[rel="canonical"]').href;
    if (new URL(canonical).pathname !== location.pathname) throw new Error(`canonical ${canonical} does not match ${location.pathname}`);
    if (!["localhost", "127.0.0.1"].includes(location.hostname) && canonical !== location.origin + location.pathname) throw new Error("canonical host is wrong");
    for (const node of document.querySelectorAll('script[type="application/ld+json"]')) JSON.parse(node.textContent);
    const rules = document.querySelectorAll("section.rule");
    if (rules.length) {
      for (const r of rules) {
        const links = r.querySelectorAll(".src a[href^='http']");
        if (!links.length) throw new Error("a section without a source: " + r.querySelector("h2").textContent);
        if (!r.querySelector(".src time")) throw new Error("a source without a checked date in " + r.querySelector("h2").textContent);
      }
      if (!document.querySelector(".notice")) throw new Error("no not-legal-advice notice");
      if (!/local health department/i.test(document.body.textContent)) throw new Error("no pointer to the local health department");
      log.push(`${rules.length} sourced sections`);
    }
    log.push("page ok: " + h1.textContent.trim());
    finish(log);
  } catch (error) {
    finish(log, error);
  }
}
