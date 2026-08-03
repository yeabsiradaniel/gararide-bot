/* GaraRIde mini app — talks to the bot's API when available,
   falls back to baked-in demo data when hosted statically. */
"use strict";

/* ------------------------------------------------------------ Telegram */

const tg = window.Telegram && window.Telegram.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  tg.setHeaderColor("#f7f2e7");
  tg.setBackgroundColor("#f7f2e7");
}

const TG_ID = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user
  && tg.initDataUnsafe.user.id) || null;

function haptic(style = "light") {
  if (tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred(style);
}

function userName() {
  return (tg && tg.initDataUnsafe && tg.initDataUnsafe.user
    && (tg.initDataUnsafe.user.first_name || tg.initDataUnsafe.user.username)) || "ተጓዥ";
}

/* --------------------------------------------------------- demo fallback */

const DEMO_STOPS = [
  { id: "megenagna",   name: "መገናኛ" },
  { id: "hayahulet",   name: "ሀያሁለት (22 ማዞሪያ)" },
  { id: "edna",        name: "ኤድና ሞል" },
  { id: "medhanialem", name: "ቦሌ ሜድሃኒአለም" },
  { id: "dildiy",      name: "ቦሌ ድልድይ" },
  { id: "airport",     name: "ቦሌ አየር ማረፊያ" },
];

function demoRides() {
  const now = Date.now();
  const mk = (id, frm, to, mins, total, left, driver) => ({
    id, from_idx: frm, to_idx: to,
    direction: to > frm ? "m2b" : "b2m",
    from_name: DEMO_STOPS[frm].name, to_name: DEMO_STOPS[to].name,
    depart_at: new Date(now + mins * 60000).toISOString(),
    seats_total: total, seats_left: left,
    fare: fareFor(frm, to), solo: soloFor(frm, to), driver,
  });
  return [
    mk("D-1", 0, 5, 35, 3, 3, { name: "አበበ ከበደ", car: "Toyota Corolla", plate: "3-AA 21457", rating: 4.8, phone: "0911 22 33 44" }),
    mk("D-2", 1, 3, 65, 2, 2, { name: "ሠላም ተስፋዬ", car: "Suzuki Dzire", plate: "3-AA 88712", rating: 4.9, phone: "0912 34 45 56" }),
    mk("D-3", 5, 0, 95, 3, 3, { name: "ዳዊት ሞላ", car: "Hyundai Accent", plate: "3-AA 55203", rating: 4.7, phone: "0913 45 56 67" }),
    mk("D-4", 4, 1, 140, 2, 1, { name: "ሄኖክ ገብሬ", car: "Toyota Vitz", plate: "3-AA 30918", rating: 4.6, phone: "0914 56 67 78" }),
    mk("D-5", 0, 3, 180, 2, 0, { name: "ብርሃኑ አለሙ", car: "Toyota Corolla", plate: "3-AA 76240", rating: 4.5, phone: "0915 67 78 89" }),
    mk("D-6", 2, 5, 220, 3, 2, { name: "ምህረት ወላደ", car: "Suzuki Swift", plate: "3-AA 64182", rating: 4.9, phone: "0916 78 89 90" }),
  ];
}

/* ------------------------------------------------------------ state */

const fareFor = (f, t) => Math.max(40, 25 + 25 * Math.abs(t - f));
const soloFor = (f, t) => 60 + 60 * Math.abs(t - f);

const state = {
  online: true,
  stops: DEMO_STOPS,
  rides: [],
  apiBookings: [],        // bookings from the server (all users; filtered client-side)
  dir: "m2b",
  tab: "rides",
  openRide: null,
  filter: { from: "", to: "" },   // "" = any stop
  post: { from: 0, to: 5, time: "min:30", seats: 2, driver: "", car: "" },
};

const view = document.getElementById("view");
const dirSeg = document.getElementById("dirSeg");

async function loadState() {
  try {
    const res = await fetch("api/state", { signal: AbortSignal.timeout(2500) });
    if (!res.ok) throw new Error();
    const data = await res.json();
    state.online = true;
    state.stops = data.stops;
    state.rides = data.rides;
    state.apiBookings = data.bookings || [];
  } catch {
    state.online = false;
    state.rides = demoRides();
    state.apiBookings = [];
  }
}

/* ------------------------------------------------------ local demo data */

function readLocalBookings() {
  try { return JSON.parse(localStorage.getItem("gr_bookings") || "[]"); }
  catch { return []; }
}

function saveLocalBookings(all) {
  localStorage.setItem("gr_bookings", JSON.stringify(all));
}

/* ------------------------------------------------------------ helpers */

const pad = n => String(n).padStart(2, "0");

function fmtTime(iso) {
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function isTomorrow(iso) {
  const d = new Date(iso), now = new Date();
  return d.getDate() !== now.getDate() || d.getMonth() !== now.getMonth();
}

function fmtRel(iso) {
  if (isTomorrow(iso)) return "ነገ " + fmtTime(iso);
  const mins = Math.round((new Date(iso) - Date.now()) / 60000);
  if (mins < 2) return "አሁን";
  if (mins < 60) return `በ${mins} ደቂቃ`;
  const h = Math.floor(mins / 60), m = mins % 60;
  return m ? `በ${h} ሰዓት ${m} ደቂቃ` : `በ${h} ሰዓት`;
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function toast(msg) {
  let el = document.querySelector(".toast");
  if (!el) {
    el = document.createElement("div");
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  requestAnimationFrame(() => el.classList.add("show"));
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove("show"), 2600);
}

function seatPips(ride) {
  let out = '<span class="seat-pips" aria-label="መቀመጫዎች">';
  for (let i = 0; i < ride.seats_total; i++) {
    out += `<i class="${i < ride.seats_left ? "" : "taken"}"></i>`;
  }
  return out + "</span>";
}

function routeSpine(ride) {
  const lo = Math.min(ride.from_idx, ride.to_idx);
  const hi = Math.max(ride.from_idx, ride.to_idx);
  let out = '<div class="route-spine" aria-hidden="true">';
  for (let i = 0; i < state.stops.length; i++) {
    out += `<span class="dot ${i >= lo && i <= hi ? "on" : ""}"></span>`;
    if (i < state.stops.length - 1) {
      out += `<span class="line ${i >= lo && i < hi ? "on" : ""}"></span>`;
    }
  }
  return out + "</div>";
}

/* ------------------------------------------- segment filter + pricing */

function filterValid() {
  const { from, to } = state.filter;
  return from !== "" && to !== "" && from !== to;
}

function coversSegment(ride, f, t) {
  const dir = t > f ? "m2b" : "b2m";
  if (ride.direction !== dir) return false;
  const lo = Math.min(f, t), hi = Math.max(f, t);
  const rlo = Math.min(ride.from_idx, ride.to_idx);
  const rhi = Math.max(ride.from_idx, ride.to_idx);
  return rlo <= lo && rhi >= hi;
}

function visibleRides() {
  let rides = state.rides.filter(r => r.direction === state.dir);
  if (filterValid()) {
    rides = rides.filter(r => coversSegment(r, state.filter.from, state.filter.to));
  }
  return rides.sort((a, b) => new Date(a.depart_at) - new Date(b.depart_at));
}

function priceFor(ride) {
  if (filterValid()) {
    return { fare: fareFor(state.filter.from, state.filter.to),
             solo: soloFor(state.filter.from, state.filter.to) };
  }
  return { fare: ride.fare, solo: ride.solo };
}

function myBookings() {
  if (state.online) {
    return state.apiBookings
      .filter(b => TG_ID === null || b.rider_id === TG_ID)
      .map(b => {
        const ride = state.rides.find(r => r.id === b.ride_id);
        return {
          code: b.code, fare: b.fare,
          from_name: state.stops[b.from_idx] ? state.stops[b.from_idx].name : "—",
          to_name: state.stops[b.to_idx] ? state.stops[b.to_idx].name : "—",
          depart_at: ride ? ride.depart_at : null,
          driver: ride ? ride.driver : null,
        };
      });
  }
  return readLocalBookings().map(b => ({
    code: b.code, fare: b.ride.fare, from_name: b.ride.from_name,
    to_name: b.ride.to_name, depart_at: b.ride.depart_at, driver: b.ride.driver,
  }));
}

/* ------------------------------------------------------------ rides tab */

function renderRides() {
  const rides = visibleRides();
  const open = rides.filter(r => r.seats_left > 0);

  const opts = sel => `<option value="">ሁሉም</option>` + state.stops.map((s, i) =>
    `<option value="${i}" ${i === sel ? "selected" : ""}>${esc(s.name)}</option>`).join("");

  const filterRow = `
    <div class="filter-row">
      <select id="fltFrom" aria-label="ከየት">${opts(state.filter.from)}</select>
      <span class="filter-arrow">→</span>
      <select id="fltTo" aria-label="ወዴት">${opts(state.filter.to)}</select>
      <button class="refresh-btn" id="btnRefresh" aria-label="አድስ">↻</button>
    </div>`;

  if (!rides.length) {
    view.innerHTML = `
      <div class="view-pane">
        ${filterRow}
        <div class="empty">
          <div class="big">በዚህ መንገድ ላይ<br>ገና መኪና የለም።</div>
          <p>መቆሚያዎችን ይቀይሩ፣ ሌላ አቅጣጫ ይሞክሩ — ወይም እርስዎ መኪና ካለዎት የመጀመሪያው ይሁኑ።</p>
          <button class="cta" data-goto="post">🚙 መንገድ ልለጥፍ</button>
        </div>
      </div>`;
    return;
  }

  const items = rides.map((r, i) => {
    const full = r.seats_left <= 0;
    const isOpen = state.openRide === r.id;
    const price = priceFor(r);
    const fareSide = full
      ? `<span class="full-tag">ሞልቷል</span>`
      : `<div class="ride-fare">
           <span class="amount">${price.fare}<small> ብር</small></span>
           <span class="save">−${price.solo - price.fare} ብር ቁጠባ</span>
         </div>`;
    return `
    <li class="ride ${full ? "is-full" : ""} ${isOpen ? "is-open" : ""}" style="--i:${i}" data-id="${r.id}">
      <button class="ride-head" data-toggle="${r.id}" ${full ? "disabled" : ""}>
        <div class="ride-time">
          <span class="hhmm">${fmtTime(r.depart_at)}</span>
          <span class="rel">${fmtRel(r.depart_at)}</span>
        </div>
        <div class="ride-route">
          <div class="stops">${esc(r.from_name)}<span class="to">${esc(r.to_name)}</span></div>
          <div class="ride-meta">
            <span class="avatar">${esc(r.driver.name.trim()[0] || "ሹ")}</span>
            <span>${esc(r.driver.name)} · ${esc(r.driver.car)} · ★${r.driver.rating}</span>
            ${seatPips(r)}
          </div>
        </div>
        ${fareSide}
      </button>
      <div class="ride-details">
        <div class="ride-details-inner">
          <div class="ride-details-body">
            ${routeSpine(r)}
            <dl>
              <div class="detail-row"><dt>ሹፌር</dt><dd>${esc(r.driver.name)} — ${esc(r.driver.car)}</dd></div>
              <div class="detail-row"><dt>ደረጃ</dt><dd>★ ${r.driver.rating}</dd></div>
              <div class="detail-row"><dt>ቀሪ መቀመጫ</dt><dd>${r.seats_left} / ${r.seats_total}</dd></div>
              <div class="detail-row"><dt>ዋጋ</dt><dd>${price.fare} ብር (ብቻዎን ${price.solo} ብር)</dd></div>
            </dl>
            <button class="book-btn" data-book="${r.id}">ቦታ ያዝ — ${price.fare} ብር</button>
            <p class="pay-note">ክፍያው በቴሌብር በቀጥታ ለሹፌሩ — ለማሳየት ብቻ</p>
          </div>
        </div>
      </div>
    </li>`;
  }).join("");

  view.innerHTML = `
    <div class="view-pane">
      ${filterRow}
      <div class="rides-summary"><strong>${open.length}</strong> ክፍት መንገዶች · እስከ 60% ቁጠባ
        ${state.online ? "" : '<span class="offline-chip">የማሳያ ዳታ</span>'}
      </div>
      <ul class="ride-list">${items}</ul>
    </div>`;
}

async function bookRide(id) {
  const ride = state.rides.find(r => r.id === id);
  if (!ride) return;
  haptic("medium");
  const seg = filterValid()
    ? { from: state.filter.from, to: state.filter.to }
    : { from: ride.from_idx, to: ride.to_idx };
  const price = { fare: fareFor(seg.from, seg.to) };
  if (state.online) {
    try {
      const res = await fetch("api/book", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ride_id: id, name: userName(), rider_id: TG_ID,
                               from: seg.from, to: seg.to }),
      });
      const data = await res.json();
      if (!res.ok) {
        toast(data.error === "full" ? "😕 መኪናው ሞልቷል" : "ስህተት ተፈጥሯል");
        await loadState(); render();
        return;
      }
      ride.seats_left -= 1;
      showBooked(data.booking.code, ride, seg, data.booking.fare);
      await loadState();  // refresh bookings/seats for other tabs
      return;
    } catch { /* fall through to offline */ }
  }
  // offline / static-host demo mode
  ride.seats_left -= 1;
  const code = "GR-" + Math.random().toString(36).slice(2, 6).toUpperCase();
  const all = readLocalBookings();
  all.push({ code, ride: JSON.parse(JSON.stringify(ride)) });
  saveLocalBookings(all);
  showBooked(code, ride, seg, price.fare);
}

function showBooked(code, ride, seg, fare) {
  state.openRide = null;
  render();
  const li = document.querySelector(`.ride[data-id="${ride.id}"]`);
  if (li) {
    li.classList.add("is-open");
    li.querySelector(".ride-details-inner").innerHTML = `
      <div class="booked-banner">
        <div>🎉 ቦታዎ ተያዟል!</div>
        <div class="code">${esc(code)}</div>
        <p>🕐 ${fmtTime(ride.depart_at)} በ${esc(state.stops[seg.from].name)} ይጠብቁ።<br>
        💳 ${fare} ብር በቴሌብር ለሹፌሩ (${esc((ride.driver && ride.driver.phone) || "—")})</p>
      </div>`;
    li.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  toast("🎉 ቦታ ተያዟል!");
  haptic("heavy");
}

async function cancelBooking(code) {
  haptic("medium");
  if (state.online) {
    try {
      const res = await fetch("api/cancel", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });
      if (!res.ok) throw new Error();
      await loadState();
      render();
      toast("✅ ቦታዎ ተሰርዟል");
      return;
    } catch { /* fall through */ }
  }
  saveLocalBookings(readLocalBookings().filter(b => b.code !== code));
  render();
  toast("✅ ቦታዎ ተሰርዟል");
}

/* ------------------------------------------------------------ post tab */

const TIME_CHOICES = [
  ["min:30", "በ30 ደቂቃ"], ["min:60", "በ1 ሰዓት"], ["min:120", "በ2 ሰዓት"],
  ["tom:7", "ነገ ጠዋት 07:00"], ["tom:8", "ነገ ጠዋት 08:00"],
];

function resolveDepart(choice) {
  if (choice.startsWith("min:")) {
    return new Date(Date.now() + parseInt(choice.slice(4), 10) * 60000);
  }
  const hour = parseInt(choice.slice(4), 10);
  const d = new Date();
  d.setDate(d.getDate() + 1);
  d.setHours(hour, 0, 0, 0);
  return d;
}

function renderPost() {
  const p = state.post;
  const stopOpts = sel => state.stops.map((s, i) =>
    `<option value="${i}" ${i === sel ? "selected" : ""}>${esc(s.name)}</option>`).join("");
  const chips = TIME_CHOICES.map(([key, label]) =>
    `<button class="chip ${p.time === key ? "is-on" : ""}" data-time="${key}">${label}</button>`).join("");
  const fare = fareFor(p.from, p.to);
  const solo = soloFor(p.from, p.to);
  const invalid = p.from === p.to;

  view.innerHTML = `
    <div class="view-pane post-form">
      <h2>መንገድ ልለጥፍ</h2>
      <p style="color:var(--ink-60);font-size:0.85rem">ነጻ መቀመጫዎን ያካፈሉ — ተጓዦች በማንኛውም መቆሚያ መጫን ይችላሉ።</p>

      <div class="field">
        <label>ሙሉ ስም</label>
        <input class="text-input" id="fDriver" placeholder="ለምሳሌ፦ አበበ ከበደ" value="${esc(p.driver)}">
      </div>
      <div class="field">
        <label>የመኪና አይነትና ሰሌዳ</label>
        <input class="text-input" id="fCar" placeholder="ለምሳሌ፦ Corolla 3-AA 12345" value="${esc(p.car)}">
      </div>
      <div class="field">
        <label>መንገድ</label>
        <div class="stop-selects">
          <select id="fFrom" aria-label="መነሻ">${stopOpts(p.from)}</select>
          <button class="swap" id="fSwap" aria-label="ቀይር">⇄</button>
          <select id="fTo" aria-label="መድረሻ">${stopOpts(p.to)}</select>
        </div>
      </div>
      <div class="field">
        <label>መነሻ ሰዓት</label>
        <div class="chip-row">${chips}</div>
      </div>
      <div class="field">
        <label>ነጻ መቀመጫ</label>
        <div class="stepper">
          <button id="seatMinus" aria-label="ቀንስ">−</button>
          <span class="val">${p.seats}</span>
          <button id="seatPlus" aria-label="ጨምር">+</button>
        </div>
      </div>

      <div class="fare-preview">
        <span class="amount">${fare}<small> ብር / መቀመጫ</small></span>
        <span class="vs">ተጓዥ ብቻውን ${solo} ብር<br>ይከፍል ነበር</span>
      </div>

      <button class="submit-btn" id="fSubmit" ${invalid ? "disabled" : ""}>
        ${invalid ? "መነሻና መድረሻ አንድ መሆን አይችሉም" : "መንገዱን ለጥፍ ✅"}
      </button>
    </div>`;
}

async function submitPost() {
  const p = state.post;
  if (p.from === p.to) return;
  haptic("medium");
  const departISO = resolveDepart(p.time).toISOString();
  if (state.online) {
    try {
      const res = await fetch("api/rides", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from: p.from, to: p.to, depart_at: departISO, seats: p.seats,
          driver_name: p.driver || userName(), car: p.car, driver_id: TG_ID,
        }),
      });
      if (!res.ok) throw new Error();
      await loadState();
      state.dir = p.to > p.from ? "m2b" : "b2m";
      setDir(state.dir);
      switchTab("rides");
      toast("✅ መንገድዎ ተለጥፏል!");
      return;
    } catch { /* fall through */ }
  }
  const ride = {
    id: "L-" + Date.now(), from_idx: p.from, to_idx: p.to,
    direction: p.to > p.from ? "m2b" : "b2m",
    from_name: state.stops[p.from].name, to_name: state.stops[p.to].name,
    depart_at: departISO,
    seats_total: p.seats, seats_left: p.seats,
    fare: fareFor(p.from, p.to), solo: soloFor(p.from, p.to),
    driver: { name: p.driver || userName(), car: p.car || "—", plate: "", rating: 5.0, phone: "(ለማሳየት)" },
  };
  state.rides.push(ride);
  state.dir = ride.direction;
  setDir(state.dir);
  switchTab("rides");
  toast("✅ መንገድዎ ተለጥፏል!");
}

/* ------------------------------------------------------------ mine tab */

function renderMine() {
  const bookings = myBookings();
  if (!bookings.length) {
    view.innerHTML = `
      <div class="view-pane empty">
        <div class="big">ገና ቦታ<br>አልያዙም።</div>
        <p>ከመንገዶች ዝርዝር ውስጥ መኪና ይምረጡ እና «ቦታ ያዝ» ይበሉ — የቦታ ኮድዎ እዚህ ይታያል።</p>
        <button class="cta" data-goto="rides">🚗 መንገዶችን ማየት</button>
      </div>`;
    return;
  }
  const items = bookings.map(b => `
    <li class="mine-item">
      <div class="mine-main">
        <div class="code">${esc(b.code)}</div>
        <div class="line2">🕐 ${b.depart_at ? fmtTime(b.depart_at) + (isTomorrow(b.depart_at) ? " (ነገ)" : "") : "—"} · ${esc(b.from_name)} → ${esc(b.to_name)} · ${b.fare} ብር</div>
        ${b.driver ? `<div class="line2">🚗 ${esc(b.driver.name)}${b.driver.phone ? " — " + esc(b.driver.phone) : ""}</div>` : ""}
      </div>
      <button class="cancel-btn" data-cancel="${esc(b.code)}">ሰርዝ</button>
    </li>`).join("");
  view.innerHTML = `<div class="view-pane"><ul class="mine-list">${items}</ul></div>`;
}

/* ------------------------------------------------------------ chrome */

function render() {
  if (state.tab === "rides") renderRides();
  else if (state.tab === "post") renderPost();
  else renderMine();
}

function switchTab(tab) {
  state.tab = tab;
  document.querySelectorAll(".tab").forEach(t =>
    t.classList.toggle("is-active", t.dataset.tab === tab));
  render();
  view.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}

function setDir(dir) {
  state.dir = dir;
  dirSeg.dataset.dir = dir;
  dirSeg.querySelectorAll(".seg-btn").forEach(b =>
    b.classList.toggle("is-active", b.dataset.dir === dir));
}

/* ------------------------------------------------------------ events */

dirSeg.addEventListener("click", e => {
  const btn = e.target.closest(".seg-btn");
  if (!btn) return;
  haptic();
  setDir(btn.dataset.dir);
  if (state.tab !== "rides") switchTab("rides");
  else render();
});

document.querySelector(".tabbar").addEventListener("click", e => {
  const tab = e.target.closest(".tab");
  if (tab) { haptic(); switchTab(tab.dataset.tab); }
});

view.addEventListener("click", async e => {
  const toggle = e.target.closest("[data-toggle]");
  if (toggle) {
    const id = toggle.dataset.toggle;
    state.openRide = state.openRide === id ? null : id;
    haptic();
    render();
    return;
  }
  const book = e.target.closest("[data-book]");
  if (book) { await bookRide(book.dataset.book); return; }
  const cancel = e.target.closest("[data-cancel]");
  if (cancel) { await cancelBooking(cancel.dataset.cancel); return; }
  const goto = e.target.closest("[data-goto]");
  if (goto) { switchTab(goto.dataset.goto); return; }
  const timeChip = e.target.closest("[data-time]");
  if (timeChip) { state.post.time = timeChip.dataset.time; haptic(); renderPost(); return; }
  if (e.target.closest("#seatMinus")) {
    state.post.seats = Math.max(1, state.post.seats - 1); haptic(); renderPost(); return;
  }
  if (e.target.closest("#seatPlus")) {
    state.post.seats = Math.min(4, state.post.seats + 1); haptic(); renderPost(); return;
  }
  if (e.target.closest("#fSwap")) {
    [state.post.from, state.post.to] = [state.post.to, state.post.from];
    haptic(); renderPost(); return;
  }
  if (e.target.closest("#fSubmit")) { await submitPost(); return; }
  if (e.target.closest("#btnRefresh")) {
    haptic();
    await loadState();
    render();
    toast(state.online ? "↻ ተዘምኗል" : "ከመስመር ውጪ — የማሳያ ዳታ");
    return;
  }
});

view.addEventListener("change", e => {
  if (e.target.id === "fFrom") { state.post.from = +e.target.value; renderPost(); }
  if (e.target.id === "fTo") { state.post.to = +e.target.value; renderPost(); }
  if (e.target.id === "fltFrom") {
    state.filter.from = e.target.value === "" ? "" : +e.target.value;
    state.openRide = null; haptic(); renderRides();
  }
  if (e.target.id === "fltTo") {
    state.filter.to = e.target.value === "" ? "" : +e.target.value;
    state.openRide = null; haptic(); renderRides();
  }
});

view.addEventListener("input", e => {
  if (e.target.id === "fDriver") state.post.driver = e.target.value;
  if (e.target.id === "fCar") state.post.car = e.target.value;
});

/* ------------------------------------------------------------ boot */

(async function boot() {
  setDir("m2b");
  await loadState();
  render();
  // keep relative times and live rides fresh
  setInterval(async () => {
    if (state.online && state.tab === "rides" && !state.openRide) {
      await loadState();
      render();
    }
  }, 30000);
})();
