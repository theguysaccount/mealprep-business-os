// Order pages whose whole state lives in the link. Pure functions (no DOM), shared by the builder, the order
// page and the node tests.
//
// A link looks like https://…/order/#1.<base64url of deflate-raw(JSON)>. "0." means plain (uncompressed)
// JSON, used where the browser has no CompressionStream. The part after # never reaches any server.

export const VERSION = 1;
export const MAX_ITEMS = 40;
export const MAX_LINK = 7000;   // characters; long links break in some SMS apps and QR codes
export const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

const enc = new TextEncoder();
const dec = new TextDecoder();

function toB64url(bytes) {
  let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromB64url(text) {
  const b64 = text.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((text.length + 3) % 4);
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function pipe(bytes, stream) {
  const body = new Blob([bytes]).stream().pipeThrough(stream);
  return new Uint8Array(await new Response(body).arrayBuffer());
}

const canCompress = () => typeof CompressionStream === "function" && typeof DecompressionStream === "function";

/** Menu object -> the part of the link after "#". */
export async function encodeMenu(menu) {
  const json = enc.encode(JSON.stringify(clean(menu)));
  if (canCompress()) return "1." + toB64url(await pipe(json, new CompressionStream("deflate-raw")));
  return "0." + toB64url(json);
}

/** The part after "#" -> a cleaned menu object. Throws on anything that isn't a valid link. */
export async function decodeMenu(fragment) {
  const text = String(fragment || "").replace(/^#/, "").trim();
  const m = /^([01])\.([A-Za-z0-9_-]+)$/.exec(text);
  if (!m) throw new Error("This link is incomplete. Ask the business for its full order link.");
  let bytes = fromB64url(m[2]);
  if (m[1] === "1") {
    if (!canCompress()) throw new Error("This browser is too old to open order links. Try a current browser.");
    bytes = await pipe(bytes, new DecompressionStream("deflate-raw"));
  }
  const menu = JSON.parse(dec.decode(bytes));
  if (!menu || menu.v !== VERSION) throw new Error("This order link was made with a newer version. Reload the page.");
  return clean(menu);
}

const str = (v, max) => (typeof v === "string" ? v.replace(/[\u0000-\u001f\u007f]/g, " ").trim().slice(0, max) : "");
const num = (v, lo, hi) => {
  const n = typeof v === "number" ? v : parseFloat(v);
  return Number.isFinite(n) && n >= lo && n <= hi ? Math.round(n * 100) / 100 : null;
};

/** Phone number -> digits with a leading + (US numbers get +1). Empty string when it can't be a phone. */
export function normalizePhone(raw) {
  const digits = String(raw || "").replace(/[^\d+]/g, "");
  const d = digits.replace(/\+/g, "");
  if (digits.startsWith("+") && d.length >= 8 && d.length <= 15) return "+" + d;
  if (d.length === 10) return "+1" + d;
  if (d.length === 11 && d.startsWith("1")) return "+" + d;
  return "";
}

export function normalizeZips(raw) {
  const list = Array.isArray(raw) ? raw : String(raw || "").split(/[\s,;]+/);
  return [...new Set(list.map((z) => String(z).trim().slice(0, 5)).filter((z) => /^\d{5}$/.test(z)))].sort().slice(0, 200);
}

const TAGS = ["GF", "DF", "V", "VG", "NF", "HP", "LC", "KETO", "SPICY"];
export const TAG_LABELS = { GF: "Gluten-free", DF: "Dairy-free", V: "Vegetarian", VG: "Vegan", NF: "Nut-free", HP: "High protein",
  LC: "Low carb", KETO: "Keto", SPICY: "Spicy" };

/** Keep only known fields, with sane lengths and ranges. Unknown or broken fields are dropped, never trusted. */
export function clean(menu) {
  const m = menu && typeof menu === "object" ? menu : {};
  const cut = m.cut && typeof m.cut === "object" ? m.cut : {};
  const out = {
    v: VERSION,
    n: str(m.n, 80),
    st: /^[A-Z]{2}$/.test(m.st || "") ? m.st : "",
    ph: normalizePhone(m.ph),
    em: /^[^\s@<>"]{1,64}@[^\s@<>"]{1,190}\.[A-Za-z]{2,}$/.test(m.em || "") ? m.em : "",
    tz: typeof m.tz === "string" && /^[A-Za-z_]+\/[A-Za-z_/+-]+$/.test(m.tz) ? m.tz.slice(0, 40) : "America/New_York",
    cut: { d: Number.isInteger(cut.d) && cut.d >= 0 && cut.d <= 6 ? cut.d : 4, h: Number.isInteger(cut.h) && cut.h >= 0 && cut.h <= 23 ? cut.h : 20,
      m: Number.isInteger(cut.m) && cut.m >= 0 && cut.m <= 59 ? cut.m : 0 },
    ful: (Array.isArray(m.ful) ? m.ful : []).slice(0, 4).map((f) => ({
      t: f && f.t === "delivery" ? "delivery" : "pickup",
      d: Number.isInteger(f && f.d) && f.d >= 0 && f.d <= 6 ? f.d : 0,
      w: str(f && f.w, 40),
      note: str(f && f.note, 160),
    })),
    zips: normalizeZips(m.zips),
    fee: num(m.fee, 0, 1000),
    min: num(m.min, 0, 10000),
    pay: str(m.pay, 160),
    lic: str(m.lic, 120),
    note: str(m.note, 400),
    items: (Array.isArray(m.items) ? m.items : []).slice(0, MAX_ITEMS).map((it) => ({
      n: str(it && it.n, 80),
      p: num(it && it.p, 0, 10000),
      d: str(it && it.d, 200),
      tags: TAGS.filter((t) => (Array.isArray(it && it.tags) ? it.tags : []).includes(t)),   // canonical order
      cal: num(it && it.cal, 0, 5000),
      pro: num(it && it.pro, 0, 500),
      sold: !!(it && it.sold),
    })).filter((it) => it.n),
  };
  if (!out.ful.length) out.ful = [{ t: "pickup", d: 0, w: "", note: "" }];
  return out;
}

/** Problems that stop a link from being useful. Empty list = ready to share. */
export function problems(menu) {
  const out = [];
  if (!menu.n) out.push("Add your business name.");
  if (!menu.ph && !menu.em) out.push("Add a mobile number (orders arrive as texts) or an email address.");
  if (!menu.items.length) out.push("Add at least one dish.");
  if (menu.items.some((i) => i.p === null)) out.push("Every dish needs a price.");
  if (menu.ful.some((f) => f.t === "delivery") && !menu.zips.length) out.push("List the ZIP codes you deliver to.");
  return out;
}

/** Local weekday, hour and minute of `now` in time zone `tz`. */
export function localParts(now, tz) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: tz, weekday: "short", hour: "numeric", minute: "numeric",
    hourCycle: "h23" }).formatToParts(now).map((p) => [p.type, p.value]));
  return { d: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(parts.weekday), h: Number(parts.hour) % 24, m: Number(parts.minute) };
}

/**
 * When this week's orders close, and which fulfilment days they're for.
 * Returns { minutesLeft, cutoff: {d,h,m}, next: [{t,d,w,note,daysAfterCutoff}] }.
 */
export function schedule(menu, now = new Date()) {
  const local = localParts(now, menu.tz);
  const nowMin = local.d * 1440 + local.h * 60 + local.m;
  let cutMin = menu.cut.d * 1440 + menu.cut.h * 60 + menu.cut.m;
  if (cutMin <= nowMin) cutMin += 7 * 1440;
  const next = menu.ful.map((f) => {
    let days = (f.d - menu.cut.d + 7) % 7;
    if (days === 0) days = 7;   // a fulfilment day equal to the cutoff day means the following week
    return { ...f, daysAfterCutoff: days };
  }).sort((a, b) => a.daysAfterCutoff - b.daysAfterCutoff);
  return { minutesLeft: cutMin - nowMin, cutoff: menu.cut, next };
}

export function formatTime(h, m) {
  const ampm = h < 12 ? "AM" : "PM";
  const hh = h % 12 === 0 ? 12 : h % 12;
  return m ? `${hh}:${String(m).padStart(2, "0")} ${ampm}` : `${hh} ${ampm}`;
}

export function formatLeft(minutes) {
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"}`;
  const h = Math.floor(minutes / 60);
  if (h < 48) return `${h} hour${h === 1 ? "" : "s"}`;
  const d = Math.floor(h / 24);
  return `${d} day${d === 1 ? "" : "s"}`;
}

export const money = (n) => (n === null || n === undefined ? "" : "$" + (Math.round(n * 100) / 100).toFixed(2).replace(/\.00$/, ""));

/**
 * Totals for a cart. cart: { itemIndex: quantity }. Returns { lines, subtotal, fee, total, belowMinimum }.
 */
export function totals(menu, cart, method) {
  const lines = [];
  let subtotal = 0;
  for (const [i, q] of Object.entries(cart || {})) {
    const item = menu.items[Number(i)];
    const qty = Math.max(0, Math.min(99, parseInt(q, 10) || 0));
    if (!item || item.sold || !qty) continue;
    const price = item.p || 0;
    lines.push({ name: item.n, qty, price, amount: Math.round(price * qty * 100) / 100 });
    subtotal += price * qty;
  }
  subtotal = Math.round(subtotal * 100) / 100;
  const fee = method === "delivery" && menu.fee ? menu.fee : 0;
  return { lines, subtotal, fee, total: Math.round((subtotal + fee) * 100) / 100, belowMinimum: !!(menu.min && subtotal < menu.min) };
}

export function zipAllowed(menu, zip) {
  return menu.zips.includes(String(zip || "").trim().slice(0, 5));
}

/** The text message (or email body) a customer sends. */
export function orderMessage(menu, order) {
  const t = totals(menu, order.cart, order.method);
  const f = menu.ful[order.ful] || menu.ful[0];
  const when = `${f.t === "delivery" ? "Delivery" : "Pickup"} ${DAYS[f.d]}${f.w ? " " + f.w : ""}`;
  const out = [`Order for ${menu.n}`];
  for (const l of t.lines) out.push(`${l.qty} x ${l.name}${l.price ? ` (${money(l.amount)})` : ""}`);
  out.push(`Subtotal ${money(t.subtotal)}${t.fee ? `, delivery ${money(t.fee)}` : ""}, total ${money(t.total)}`);
  out.push(when);
  if (f.t === "delivery" && order.address) out.push(`Deliver to: ${str(order.address, 160)} ${str(order.zip, 5)}`.trim());
  if (order.name) out.push(`Name: ${str(order.name, 60)}`);
  if (order.notes) out.push(`Notes: ${str(order.notes, 300)}`);
  return out.join("\n");
}

export function smsLink(phone, body) {
  // "?&body=" works on both iOS (which reads &body) and Android (which reads ?body).
  return `sms:${phone}?&body=${encodeURIComponent(body)}`;
}

export function mailLink(email, subject, body) {
  return `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

/** Sample menu for the "try it" button and the tests. Fictional business. */
export const SAMPLE = {
  v: 1, n: "Sunday Fuel Meal Prep (sample)", st: "TX", ph: "+15125550142", em: "", tz: "America/Chicago",
  cut: { d: 4, h: 20, m: 0 },
  ful: [{ t: "pickup", d: 0, w: "11 AM-2 PM", note: "Pickup at the shared kitchen on 5th St" }, { t: "delivery", d: 0, w: "3-6 PM", note: "" }],
  zips: ["78701", "78702", "78703", "78704"], fee: 5, min: 30, pay: "Pay at pickup or delivery: cash, card or Venmo",
  lic: "", note: "Meals keep 4 days in the fridge. Reheat to 165°F.",
  items: [
    { n: "Chicken, rice and roasted broccoli", p: 12, d: "Grilled chicken thigh, jasmine rice, broccoli, lemon-herb sauce", tags: ["GF", "DF", "HP"], cal: 560, pro: 42, sold: false },
    { n: "Turkey chili", p: 11, d: "Ground turkey, black beans, peppers; mild", tags: ["GF", "DF", "HP"], cal: 480, pro: 38, sold: false },
    { n: "Tofu peanut noodles", p: 11, d: "Rice noodles, crispy tofu, cabbage, peanut sauce", tags: ["VG", "DF"], cal: 610, pro: 24, sold: false },
    { n: "Overnight oats (2 jars)", p: 8, d: "Oats, chia, almond milk, berries", tags: ["V"], cal: 380, pro: 12, sold: false },
  ],
};
