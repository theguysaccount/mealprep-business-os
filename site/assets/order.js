// The customer-facing order page. The menu comes from the link; the order goes out as a text message (or an
// email) that the customer sends themselves. Nothing is stored or sent by this site.
import { decodeMenu, schedule, totals, orderMessage, smsLink, mailLink, zipAllowed, money, formatTime, formatLeft, DAYS, TAG_LABELS } from "./order-core.js";

const cfg = JSON.parse(document.getElementById("cfg").textContent);
const root = document.getElementById("order");
const toast = document.getElementById("toast");
const cart = {};
let menu = null;

function track(name) {
  try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: "event/" + name, title: name, event: true }); } catch (e) { /* never break the page */ }
}

function el(tag, props = {}, kids = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "text") node.textContent = v;
    else if (k === "class") node.className = v;
    else if (k.startsWith("data-") || k.startsWith("aria-") || k === "for") node.setAttribute(k, v);
    else node[k] = v;
  }
  for (const kid of kids) if (kid) node.append(kid);
  return node;
}

function say(message) {
  toast.textContent = message;
  toast.classList.add("on");
  clearTimeout(say.t);
  say.t = setTimeout(() => toast.classList.remove("on"), 1800);
}

function whenText(s) {
  const c = s.cutoff;
  const first = s.next[0];
  const what = first.t === "delivery" ? "delivery" : "pickup";
  return [`Order by `, el("strong", { text: `${DAYS[c.d]} ${formatTime(c.h, c.m)}` }),
    ` for ${DAYS[first.d]} ${what}${first.w ? " (" + first.w + ")" : ""}. Orders close in about ${formatLeft(s.minutesLeft)}.`];
}

function render() {
  const s = schedule(menu);
  document.title = `${menu.n}: order meal prep`;
  const head = el("div", {}, [el("h1", { text: menu.n })]);
  head.append(el("p", { class: "when" }, whenText(s)));
  const ful = el("ul", {}, menu.ful.map((f) => el("li", { text: `${f.t === "delivery" ? "Delivery" : "Pickup"} ${DAYS[f.d]}${f.w ? ", " + f.w : ""}${f.note ? ": " + f.note : ""}` })));
  head.append(ful);
  if (menu.zips.length && menu.ful.some((f) => f.t === "delivery")) {
    head.append(el("p", { class: "note", text: `Delivers to ZIP codes ${menu.zips.join(", ")}${menu.fee ? `; delivery fee ${money(menu.fee)}` : ""}.` }));
  }
  if (menu.min) head.append(el("p", { class: "note", text: `Minimum order ${money(menu.min)}.` }));
  if (menu.note) head.append(el("p", { text: menu.note }));
  const list = el("ul", { class: "menu" });
  menu.items.forEach((it, i) => {
    const qty = el("output", { text: "0", "aria-live": "polite" });
    const minus = el("button", { type: "button", text: "−", "aria-label": `One less ${it.n}` });
    const plus = el("button", { type: "button", text: "+", "aria-label": `One more ${it.n}` });
    const bump = (d) => { cart[i] = Math.max(0, Math.min(99, (cart[i] || 0) + d)); qty.textContent = String(cart[i]); update(); };
    minus.addEventListener("click", () => bump(-1));
    plus.addEventListener("click", () => bump(1));
    const meta = el("div", { class: "meta" });
    if (it.cal) meta.append(el("span", { text: `${it.cal} cal` }));
    if (it.pro) meta.append(el("span", { text: `${it.pro} g protein` }));
    for (const t of it.tags) meta.append(el("span", { class: "tag", text: TAG_LABELS[t] || t }));
    const info = el("div", {}, [el("h3", { text: it.n }), it.d ? el("p", { text: it.d }) : null, meta.children.length ? meta : null]);
    const side = it.sold ? el("div", { class: "price", text: "Sold out" })
      : el("div", { class: "qty" }, [el("span", { class: "price", text: money(it.p) }), minus, qty, plus]);
    list.append(el("li", { class: "dish" + (it.sold ? " sold" : ""), "data-dish": String(i) }, [info, side]));
  });
  const details = el("fieldset", { class: "box no-print" });
  details.append(el("legend", { text: "Your details" }));
  const choice = el("select", { id: "ful-choice" });
  menu.ful.forEach((f, i) => choice.append(el("option", { value: String(i), text: `${f.t === "delivery" ? "Delivery" : "Pickup"} ${DAYS[f.d]}${f.w ? " " + f.w : ""}` })));
  const name = el("input", { type: "text", id: "c-name", maxLength: 60, autocomplete: "name" });
  const zip = el("input", { type: "text", id: "c-zip", maxLength: 5, inputMode: "numeric", autocomplete: "postal-code" });
  const address = el("input", { type: "text", id: "c-address", maxLength: 160, autocomplete: "street-address" });
  const notes = el("textarea", { id: "c-notes", maxLength: 300 });
  const lab = (text, input) => el("div", { class: "field" }, [el("label", { for: input.id, text }), input]);
  const deliveryOnly = el("div", { "data-delivery": "" }, [lab("ZIP code", zip), lab("Street address", address)]);
  details.append(lab("Pickup or delivery", choice), lab("Your name", name), deliveryOnly, lab("Allergies or notes", notes));
  details.append(el("p", { class: "note", text: "Nothing you type here is stored or sent by this page. It goes into a text message that you send yourself." }));
  const sum = el("div", { class: "sum" });
  const send = el("a", { class: "button", href: "#", id: "send", "aria-disabled": "true", text: menu.ph ? "Text my order" : "Email my order" });
  const warn = el("p", { class: "note", id: "warn", role: "status" });
  const bar = el("div", { class: "sticky no-print" }, [sum, warn]);
  const pay = menu.pay ? el("p", { text: "Payment: " + menu.pay }) : null;
  const lic = menu.lic ? el("p", { class: "note", text: menu.lic }) : null;
  const print = el("button", { type: "button", class: "quiet small no-print", text: "Print this menu" });
  print.addEventListener("click", () => window.print());
  const own = el("p", { class: "make-own" }, ["Run a meal prep business? ",
    el("a", { href: cfg.base + "build/", text: "Make your own free order page", "data-own": "" }), " · ",
    el("a", { href: cfg.base + "permits/", text: "permits by state" })]);
  own.querySelector("[data-own]").addEventListener("click", () => track("own_from_order"));
  const disclaimer = el("p", { class: "note" }, [`${menu.n} made this page with a free tool and is responsible for its own food, permits and prices. `,
    "Questions about an order go to them, not to this website."]);
  root.replaceChildren(head, list, details, pay, lic, print, bar, own, disclaimer);

  function update() {
    const f = menu.ful[Number(choice.value)] || menu.ful[0];
    const method = f.t;
    deliveryOnly.hidden = method !== "delivery";
    const t = totals(menu, cart, method);
    const z = zip.value.trim();
    sum.replaceChildren(el("div", {}, [el("strong", { text: `Total ${money(t.total)}` }),
      el("span", { class: "note", text: ` · ${t.lines.reduce((a, l) => a + l.qty, 0)} meals${t.fee ? ` incl. ${money(t.fee)} delivery` : ""}` })]), send);
    let problem = "";
    if (!t.lines.length) problem = "Add at least one meal.";
    else if (t.belowMinimum) problem = `The minimum order is ${money(menu.min)}.`;
    else if (method === "delivery" && !/^\d{5}$/.test(z)) problem = "Enter your ZIP code for delivery.";
    else if (method === "delivery" && !zipAllowed(menu, z)) problem = `${menu.n} doesn't deliver to ${z}. Choose pickup, or ask them.`;
    else if (!name.value.trim()) problem = "Add your name so they know whose order it is.";
    warn.textContent = problem;
    const body = orderMessage(menu, { cart, method, ful: Number(choice.value), name: name.value, zip: z, address: address.value, notes: notes.value });
    send.href = problem ? "#" : (menu.ph ? smsLink(menu.ph, body) : mailLink(menu.em, `Order for ${menu.n}`, body));
    send.setAttribute("aria-disabled", problem ? "true" : "false");
    send.dataset.body = body;
    send.dataset.total = String(t.total);
  }
  send.addEventListener("click", (e) => {
    if (send.getAttribute("aria-disabled") === "true") { e.preventDefault(); say(warn.textContent || "Add a meal first"); return; }
    track("order_sent");
  });
  for (const input of [choice, name, zip, address, notes]) input.addEventListener("input", update);
  update();
  track("order_page_view");
}

async function start() {
  try {
    menu = await decodeMenu(location.hash);
    render();
  } catch (e) {
    root.replaceChildren(el("h1", { text: "This order link didn't open" }), el("p", { text: e.message }),
      el("p", {}, ["Running a meal prep business? ", el("a", { href: cfg.base + "build/", text: "Make a free order page" }), "."]));
  }
  document.body.dataset.ready = "1";
  if (new URLSearchParams(location.search).has("selftest")) {
    const m = await import("./selftest.js");
    m.order({ menu, cart });
  }
}
window.addEventListener("hashchange", () => location.reload());
start();
