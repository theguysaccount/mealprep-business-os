// Small behaviours for the static pages: the state picker, copy buttons, and the self-test hook.
const toast = document.getElementById("toast");

function say(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("on");
  clearTimeout(say.t);
  say.t = setTimeout(() => toast.classList.remove("on"), 1800);
}

function track(name) {
  try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: "event/" + name, title: name, event: true }); } catch (e) { /* never break the page */ }
}

for (const select of document.querySelectorAll("select.jump")) {
  select.addEventListener("change", () => { if (select.value) { track("state_pick"); location.href = select.value; } });
}

for (const button of document.querySelectorAll("[data-copy]")) {
  button.addEventListener("click", async () => {
    const text = button.dataset.copy || location.href.split("?")[0];
    try { await navigator.clipboard.writeText(text); say(button.dataset.done || "Link copied"); } catch (e) { window.prompt("Copy this:", text); }
    track(button.dataset.event || "copy_link");
  });
}

for (const a of document.querySelectorAll("a[data-track]")) a.addEventListener("click", () => track(a.dataset.track));

if (new URLSearchParams(location.search).has("selftest")) import("./selftest.js").then((m) => m.page());
