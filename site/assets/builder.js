// The order-page builder: a form whose whole state becomes a link. Nothing is sent anywhere.
import { encodeMenu, decodeMenu, clean, problems, DAYS, TAG_LABELS, SAMPLE, MAX_ITEMS, MAX_LINK } from "./order-core.js";

const cfg = JSON.parse(document.getElementById("cfg").textContent);
const form = document.querySelector("form.builder");
const itemsBox = document.getElementById("items");
const fulBox = document.getElementById("ful");
const out = document.getElementById("result");
const problemsBox = document.getElementById("problems");
const toast = document.getElementById("toast");
const $ = (sel, root = form) => root.querySelector(sel);

function track(name) {
  try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: "event/" + name, title: name, event: true }); } catch (e) { /* never break the page */ }
}

function say(message) {
  toast.textContent = message;
  toast.classList.add("on");
  clearTimeout(say.t);
  say.t = setTimeout(() => toast.classList.remove("on"), 1800);
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

let uid = 0;
function field(label, input, hint) {
  const id = "f" + ++uid;
  input.id = id;
  return el("div", { class: "field" }, [el("label", { for: id, text: label }), input, hint ? el("small", { text: hint }) : null]);
}

function dayPicker(value) {
  const s = el("select", {});
  DAYS.forEach((d, i) => s.append(el("option", { value: String(i), text: d, selected: i === value })));
  return s;
}

function addItem(it = {}) {
  if (itemsBox.children.length >= MAX_ITEMS) return say(`Up to ${MAX_ITEMS} dishes`);
  const box = el("div", { class: "item", "data-item": "" });
  const remove = el("button", { type: "button", class: "quiet small", text: "Remove" });
  remove.addEventListener("click", () => { box.remove(); changed(); });
  box.append(el("div", { class: "head" }, [el("strong", { text: "Dish" }), remove]));
  box.append(field("Name", el("input", { type: "text", name: "n", maxLength: 80, value: it.n || "", placeholder: "Chicken, rice and broccoli" })));
  box.append(el("div", { class: "row" }, [
    field("Price ($)", el("input", { type: "number", name: "p", min: 0, step: "0.01", inputMode: "decimal", value: it.p ?? "" })),
    field("Calories", el("input", { type: "number", name: "cal", min: 0, step: "1", inputMode: "numeric", value: it.cal ?? "" })),
    field("Protein (g)", el("input", { type: "number", name: "pro", min: 0, step: "1", inputMode: "numeric", value: it.pro ?? "" })),
  ]));
  box.append(field("Description", el("input", { type: "text", name: "d", maxLength: 200, value: it.d || "", placeholder: "What's in it, portion size, allergens" })));
  const checks = el("div", { class: "checks" });
  for (const [k, label] of Object.entries(TAG_LABELS)) {
    checks.append(el("label", {}, [el("input", { type: "checkbox", name: "tag", value: k, checked: (it.tags || []).includes(k) }), document.createTextNode(label)]));
  }
  checks.append(el("label", {}, [el("input", { type: "checkbox", name: "sold", checked: !!it.sold }), document.createTextNode("Sold out this week")]));
  box.append(checks);
  itemsBox.append(box);
}

function addFul(f = {}) {
  if (fulBox.children.length >= 4) return say("Up to 4 pickup or delivery options");
  const box = el("div", { class: "item", "data-ful": "" });
  const remove = el("button", { type: "button", class: "quiet small", text: "Remove" });
  remove.addEventListener("click", () => { if (fulBox.children.length > 1) { box.remove(); changed(); } });
  const type = el("select", { name: "t" }, [el("option", { value: "pickup", text: "Pickup" }), el("option", { value: "delivery", text: "Delivery" })]);
  type.value = f.t === "delivery" ? "delivery" : "pickup";
  const day = dayPicker(Number.isInteger(f.d) ? f.d : 0);
  day.name = "d";
  box.append(el("div", { class: "head" }, [el("strong", { text: "Pickup or delivery" }), remove]));
  box.append(el("div", { class: "row" }, [field("Type", type), field("Day", day),
    field("Time window", el("input", { type: "text", name: "w", maxLength: 40, value: f.w || "", placeholder: "11 AM-2 PM" }))]));
  box.append(field("Where / notes", el("input", { type: "text", name: "note", maxLength: 160, value: f.note || "", placeholder: "Pickup address, or the area you deliver to" })));
  fulBox.append(box);
}

function read() {
  const v = (name) => form.elements[name]?.value ?? "";
  const items = [...itemsBox.querySelectorAll("[data-item]")].map((box) => ({
    n: $("[name=n]", box).value, p: $("[name=p]", box).value === "" ? null : Number($("[name=p]", box).value),
    d: $("[name=d]", box).value, cal: $("[name=cal]", box).value === "" ? null : Number($("[name=cal]", box).value),
    pro: $("[name=pro]", box).value === "" ? null : Number($("[name=pro]", box).value),
    tags: [...box.querySelectorAll("[name=tag]:checked")].map((c) => c.value), sold: $("[name=sold]", box).checked,
  }));
  const ful = [...fulBox.querySelectorAll("[data-ful]")].map((box) => ({
    t: $("[name=t]", box).value, d: Number($("[name=d]", box).value), w: $("[name=w]", box).value, note: $("[name=note]", box).value,
  }));
  const [h, m] = (v("cutTime") || "20:00").split(":").map(Number);
  return clean({ v: 1, n: v("bizName"), st: v("state"), ph: v("phone"), em: v("email"), tz: v("tz"),
    cut: { d: Number(v("cutDay")), h, m }, ful, zips: v("zips"), fee: v("fee") === "" ? null : Number(v("fee")),
    min: v("min") === "" ? null : Number(v("min")), pay: v("pay"), lic: v("lic"), note: v("note"), items });
}

function fill(menu) {
  const set = (name, value) => { if (form.elements[name]) form.elements[name].value = value ?? ""; };
  set("bizName", menu.n); set("state", menu.st); set("phone", menu.ph); set("email", menu.em); set("tz", menu.tz);
  set("cutDay", String(menu.cut.d)); set("cutTime", `${String(menu.cut.h).padStart(2, "0")}:${String(menu.cut.m).padStart(2, "0")}`);
  set("zips", menu.zips.join(", ")); set("fee", menu.fee); set("min", menu.min); set("pay", menu.pay); set("lic", menu.lic); set("note", menu.note);
  itemsBox.replaceChildren();
  fulBox.replaceChildren();
  (menu.items.length ? menu.items : [{}]).forEach(addItem);
  menu.ful.forEach(addFul);
  changed();
}

let latest = null;
async function changed() {
  const menu = read();
  const issues = problems(menu);
  const permits = form.elements.permits.checked;
  if (!permits) issues.push("Tick the box about permits.");
  problemsBox.replaceChildren(...issues.map((p) => el("li", { text: p })));
  const button = document.getElementById("make");
  button.disabled = issues.length > 0;
  const guide = document.getElementById("guide-link");
  const st = cfg.states.find((s) => s.abbr === menu.st);
  guide.hidden = !st;
  if (st) { guide.href = cfg.base + "permits/" + st.slug + "/"; guide.textContent = `What ${st.name} requires`; }
  latest = menu;
  out.hidden = true;
}

async function make() {
  const menu = read();
  if (problems(menu).length || !form.elements.permits.checked) return;
  const frag = await encodeMenu(menu);
  const link = new URL(cfg.base + "order/#" + frag, location.href).href;
  const edit = new URL(cfg.base + "build/#" + frag, location.href).href;
  $("[name=link]", out).value = link;
  $("[data-open]", out).href = link;
  $("[data-edit]", out).value = edit;
  document.getElementById("toolong").hidden = link.length <= MAX_LINK;
  out.hidden = false;
  out.dataset.ready = String(link.length);
  out.scrollIntoView({ behavior: "smooth", block: "start" });
  track("link_created");
}

async function copy(text, done) {
  try { await navigator.clipboard.writeText(text); say(done); } catch (e) { window.prompt("Copy this:", text); }
}

form.addEventListener("input", changed);
form.addEventListener("change", changed);
form.addEventListener("submit", (e) => { e.preventDefault(); make(); });
document.getElementById("add-item").addEventListener("click", () => { addItem(); changed(); });
document.getElementById("add-ful").addEventListener("click", () => { addFul(); changed(); });
document.getElementById("sample").addEventListener("click", () => { fill(clean(SAMPLE)); say("Sample menu loaded"); track("sample"); });
out.querySelector("[data-copy-link]").addEventListener("click", () => { copy($("[name=link]", out).value, "Order link copied"); track("link_copied"); });
out.querySelector("[data-copy-edit]").addEventListener("click", () => copy($("[data-edit]", out).value, "Edit link copied"));
const share = out.querySelector("[data-share]");
if (navigator.share) share.addEventListener("click", () => {
  navigator.share({ title: latest?.n || "Order page", url: $("[name=link]", out).value }).catch(() => {});
  track("link_shared");
});
else share.hidden = true;

async function start() {
  const hash = location.hash.slice(1);
  if (hash) {
    try {
      fill(await decodeMenu(hash));
      form.elements.permits.checked = true;
      say("Your menu is loaded. Change anything, then make a new link.");
    } catch (e) {
      say(e.message);
      fill(clean({}));
    }
  } else fill(clean({ tz: Intl.DateTimeFormat().resolvedOptions().timeZone, st: cfg.defaultState || "" }));
  document.body.dataset.ready = "1";
  if (new URLSearchParams(location.search).has("selftest")) {
    const m = await import("./selftest.js");
    m.builder({ form, fill, make, out });
  }
}
start();
