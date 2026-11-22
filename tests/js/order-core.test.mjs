import test from "node:test";
import assert from "node:assert/strict";
import { encodeMenu, decodeMenu, clean, problems, schedule, totals, orderMessage, smsLink, normalizePhone, normalizeZips,
  zipAllowed, formatTime, formatLeft, money, SAMPLE, MAX_ITEMS } from "../../site/assets/order-core.js";

test("a menu survives the trip through a link", async () => {
  const frag = await encodeMenu(SAMPLE);
  assert.match(frag, /^1\.[A-Za-z0-9_-]+$/);
  const back = await decodeMenu("#" + frag);
  assert.deepEqual(back, clean(SAMPLE));
  assert.ok(frag.length < 1200, `sample link is ${frag.length} characters`);
});

test("plain (uncompressed) links decode too", async () => {
  const json = Buffer.from(JSON.stringify(clean(SAMPLE))).toString("base64url");
  assert.deepEqual(await decodeMenu("0." + json), clean(SAMPLE));
});

test("broken or foreign links are refused with a readable message", async () => {
  for (const bad of ["", "#", "#2.abc", "#1.!!!", "#0." + Buffer.from('{"v":99}').toString("base64url")]) {
    await assert.rejects(decodeMenu(bad), (e) => typeof e.message === "string" && e.message.length > 10, bad);
  }
});

test("cleaning drops unknown fields and clamps values", () => {
  const m = clean({ v: 1, n: "  A\u0007B  ", evil: "<script>", ph: "(512) 555-0142", em: "not an email", tz: "../../etc",
    cut: { d: 9, h: 30, m: -1 }, zips: "78701, 78702 abcde 1234 78701", fee: -5, min: "25",
    items: [{ n: "Bowl", p: "12.499", tags: ["GF", "BOGUS"], cal: 99999 }, { n: "" }] });
  assert.equal(m.n, "A B");
  assert.equal(m.evil, undefined);
  assert.equal(m.ph, "+15125550142");
  assert.equal(m.em, "");
  assert.equal(m.tz, "America/New_York");
  assert.deepEqual(m.cut, { d: 4, h: 20, m: 0 });
  assert.deepEqual(m.zips, ["78701", "78702"]);
  assert.equal(m.fee, null);
  assert.equal(m.min, 25);
  assert.equal(m.items.length, 1);
  assert.equal(m.items[0].p, 12.5);
  assert.deepEqual(m.items[0].tags, ["GF"]);
  assert.equal(m.items[0].cal, null);
  assert.equal(clean({ items: Array.from({ length: 99 }, (_, i) => ({ n: "x" + i, p: 1 })) }).items.length, MAX_ITEMS);
});

test("phones and ZIPs", () => {
  assert.equal(normalizePhone("512-555-0142"), "+15125550142");
  assert.equal(normalizePhone("1 (512) 555 0142"), "+15125550142");
  assert.equal(normalizePhone("+44 20 7946 0958"), "+442079460958");
  assert.equal(normalizePhone("555-0142"), "");
  assert.deepEqual(normalizeZips(["78704", "78701-1234", "x"]), ["78701", "78704"]);
  assert.ok(zipAllowed(clean(SAMPLE), "78704"));
  assert.ok(!zipAllowed(clean(SAMPLE), "10001"));
});

test("a link is only ready when it can take an order", () => {
  assert.deepEqual(problems(clean(SAMPLE)), []);
  const p = problems(clean({ ful: [{ t: "delivery", d: 0 }], items: [{ n: "x" }] }));
  assert.equal(p.length, 4);
});

test("weekly cutoff and fulfilment days", () => {
  const menu = clean(SAMPLE);   // orders close Thursday 8 PM Chicago time, fulfilment Sunday
  // Tuesday 2030-01-01 18:00 UTC = 12:00 noon in Chicago
  let s = schedule(menu, new Date("2030-01-01T18:00:00Z"));
  assert.equal(s.minutesLeft, 2 * 1440 + 8 * 60);
  assert.equal(s.next[0].daysAfterCutoff, 3);
  // Thursday 2030-01-03 at 20:30 Chicago (02:30 UTC Friday): this week is closed, next cutoff in ~7 days
  s = schedule(menu, new Date("2030-01-04T02:30:00Z"));
  assert.equal(s.minutesLeft, 7 * 1440 - 30);
  // A fulfilment day equal to the cutoff day means the following week
  const same = clean({ ...SAMPLE, ful: [{ t: "pickup", d: 4 }] });
  assert.equal(schedule(same, new Date("2030-01-01T18:00:00Z")).next[0].daysAfterCutoff, 7);
});

test("totals, minimum and delivery fee", () => {
  const menu = clean(SAMPLE);
  const t = totals(menu, { 0: 2, 1: 1, 7: 3, 2: "x" }, "delivery");
  assert.equal(t.subtotal, 35);
  assert.equal(t.fee, 5);
  assert.equal(t.total, 40);
  assert.equal(t.belowMinimum, false);
  assert.equal(totals(menu, { 3: 1 }, "pickup").belowMinimum, true);
  const sold = clean({ ...SAMPLE, items: SAMPLE.items.map((i, n) => ({ ...i, sold: n === 0 })) });
  assert.equal(totals(sold, { 0: 5 }, "pickup").lines.length, 0, "sold-out dishes can't be ordered");
});

test("the order message has everything the cook needs", () => {
  const menu = clean(SAMPLE);
  const msg = orderMessage(menu, { cart: { 0: 2 }, method: "delivery", ful: 1, name: "Sam", zip: "78704", address: "1 Main St", notes: "No onions" });
  assert.match(msg, /^Order for Sunday Fuel Meal Prep \(sample\)/);
  assert.match(msg, /2 x Chicken, rice and roasted broccoli \(\$24\)/);
  assert.match(msg, /total \$29/);
  assert.match(msg, /Delivery Sunday 3-6 PM/);
  assert.match(msg, /Deliver to: 1 Main St 78704/);
  assert.match(msg, /Name: Sam/);
  assert.match(msg, /Notes: No onions/);
  const link = smsLink(menu.ph, msg);
  assert.ok(link.startsWith("sms:+15125550142?&body=Order%20for"));
});

test("formatting helpers", () => {
  assert.equal(formatTime(20, 0), "8 PM");
  assert.equal(formatTime(0, 30), "12:30 AM");
  assert.equal(formatTime(12, 5), "12:05 PM");
  assert.equal(formatLeft(45), "45 minutes");
  assert.equal(formatLeft(61), "1 hour");
  assert.equal(formatLeft(3 * 1440), "3 days");
  assert.equal(money(12), "$12");
  assert.equal(money(12.5), "$12.50");
});
