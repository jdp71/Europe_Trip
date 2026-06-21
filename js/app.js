/* Europe Trip PWA */
let tripData = null;
let currentView = "days";
let currentDay = null;
let currentItem = null;
let filterType = "all";

const $ = (sel) => document.querySelector(sel);
const main = $("#main");
const headerTitle = $("#header-title");
const headerSub = $("#header-sub");
const backBtn = $("#back-btn");
const offlineBadge = $("#offline-badge");

function esc(s) {
  if (!s) return "";
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function typeLabel(t) {
  return { hotel: "Hotel", transport: "Transport", activity: "Activity" }[t] || t;
}

function showToast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  t.classList.remove("hidden");
  setTimeout(() => t.classList.remove("show"), 2500);
}

function updateHeader() {
  if (currentItem) {
    headerTitle.textContent = currentItem.title;
    headerSub.textContent = typeLabel(currentItem.type);
    backBtn.classList.remove("hidden");
  } else if (currentDay) {
    headerTitle.textContent = currentDay.label;
    headerSub.textContent = currentDay.location;
    backBtn.classList.remove("hidden");
  } else {
    headerTitle.textContent = tripData.trip.title;
    headerSub.textContent = `${tripData.trip.start} → ${tripData.trip.end}`;
    backBtn.classList.add("hidden");
  }
}

function todayStr() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

function mapSrc(obj) {
  return (obj && (obj.map_data || obj.map)) || "";
}

function photoSrc(obj) {
  return (obj && (obj.photo_data || obj.photo)) || "";
}

function renderDays() {
  currentDay = null;
  currentItem = null;
  updateHeader();

  const today = todayStr();
  let html = `
    <div class="hero">
      <h2>${esc(tripData.trip.subtitle)}</h2>
      <p>${esc(tripData.trip.route)}</p>
    </div>
    <div id="install-hint" class="install-banner hidden">
      <strong>Install for offline use</strong>
      Tap Share → <em>Add to Home Screen</em> in Safari. Open the app once while online to cache all documents.
    </div>
  `;

  for (const day of tripData.days) {
    const isToday = day.date === today;
    const count = day.items.length;
    const thumb = photoSrc(day)
      ? `<img class="day-thumb" src="${photoSrc(day)}" alt="${esc(day.city || day.location)}" loading="lazy">`
      : "";
    html += `
      <button class="day-card${isToday ? " today" : ""}${photoSrc(day) ? " has-photo" : ""}" data-date="${day.date}">
        ${thumb}
        <div class="day-card-body">
          <div class="day-date">${esc(day.date)}${isToday ? " · Today" : ""}</div>
          <div class="day-label">${esc(day.label)}</div>
          <div class="day-loc">${esc(day.location)}</div>
          <div class="day-count${count ? "" : " empty"}">${count ? count + " booking" + (count > 1 ? "s" : "") : "Free day"}</div>
        </div>
      </button>`;
  }

  main.innerHTML = html;

  if (!window.matchMedia("(display-mode: standalone)").matches) {
    $("#install-hint")?.classList.remove("hidden");
  }

  main.querySelectorAll(".day-card").forEach((el) => {
    el.addEventListener("click", () => openDay(el.dataset.date));
  });
}

function renderDay(date) {
  currentDay = tripData.days.find((d) => d.date === date);
  currentItem = null;
  updateHeader();

  if (!currentDay) return renderDays();

  let html = "";
  if (photoSrc(currentDay) || mapSrc(currentDay)) {
    html += `<div class="day-hero">`;
    const dayPhoto = photoSrc(currentDay);
    if (dayPhoto) {
      html += `
        <div class="day-hero-photo-wrap">
          <img class="day-hero-photo" src="${dayPhoto}" alt="${esc(currentDay.city || currentDay.location)}">
          <div class="day-hero-overlay">
            <div class="day-hero-city">${esc(currentDay.city || currentDay.location)}</div>
          </div>
        </div>`;
    }
    const dayMap = mapSrc(currentDay);
    if (dayMap) {
      html += `
        <div class="map-section">
          <img class="city-map" src="${dayMap}" alt="Map of ${esc(currentDay.city || currentDay.location)}">
          ${currentDay.maps_url ? `<a class="btn btn-secondary map-link-btn" href="${esc(currentDay.maps_url)}" target="_blank" rel="noopener">Open in Maps</a>` : ""}
          ${currentDay.photo_credit ? `<div class="photo-credit">${esc(currentDay.photo_credit)}</div>` : ""}
        </div>`;
    }
    html += `</div>`;
  }

  if (!currentDay.items.length) {
    html = `<div class="detail-section"><p style="color:var(--muted)">No booked activities — travel or free day.</p></div>`;
  } else {
    for (const id of currentDay.items) {
      html += itemCardHtml(tripData.items[id]);
    }
  }
  main.innerHTML = html;
  bindItemCards();
}

function itemCardHtml(item) {
  if (!item) return "";
  const meta = [item.time, item.confirmation ? `#${item.confirmation}` : ""].filter(Boolean).join(" · ");
  return `
    <button class="item-card type-${item.type}${item.warning ? " warning" : ""}" data-id="${item.id}">
      <div class="item-type">${typeLabel(item.type)}</div>
      <div class="item-title">${esc(item.summary || item.title)}</div>
      ${meta ? `<div class="item-meta">${esc(meta)}</div>` : ""}
    </button>`;
}

function bindItemCards() {
  main.querySelectorAll(".item-card[data-id]").forEach((el) => {
    el.addEventListener("click", () => openItem(el.dataset.id));
  });
}

function renderItem(id) {
  currentItem = tripData.items[id];
  updateHeader();
  if (!currentItem) return;

  const i = currentItem;
  const rows = [];
  const add = (label, val) => { if (val) rows.push({ label, val }); };

  add("Date", i.end_date && i.end_date !== i.date ? `${i.date} → ${i.end_date}` : i.date);
  add("Time", i.time ? (i.end_time ? `${i.time} – ${i.end_time}` : i.time) : "");
  add("Location", i.location);
  add("Address", i.address);
  add("Provider", i.provider);
  add("Confirmation", i.confirmation);
  add("PIN", i.pin);
  add("Guests", i.guests);
  add("Passengers", i.passengers?.join(", "));
  add("Price", i.price);
  add("Duration", i.duration);
  add("Check-in", i.check_in);
  add("Check-out", i.check_out);
  add("Phone", i.phone);
  add("Email", i.email);

  let html = "";

  const itemMap = i.map_data || i.map_image;
  if (itemMap) {
    html += `
      <div class="detail-section map-section">
        <h3>Location map</h3>
        <img class="city-map item-map" src="${itemMap}" alt="Map for ${esc(i.title)}">
        ${i.maps_url ? `<a class="btn btn-secondary map-link-btn" href="${esc(i.maps_url)}" target="_blank" rel="noopener">Open in Maps</a>` : ""}
      </div>`;
  }

  html += `
    <div class="detail-section">
      <h3>Details</h3>
      <div class="detail-grid">
        ${rows.map((r) => `<div class="detail-row"><span class="label">${esc(r.label)}</span><span class="value">${esc(r.val)}</span></div>`).join("")}
      </div>
    </div>`;

  if (i.qr_svg) {
    html += `
      <div class="detail-section">
        <h3>QR Code</h3>
        <div class="qr-wrap">${i.qr_svg}</div>
        <div class="qr-caption">${esc(i.qr_data)}</div>
      </div>`;
  }

  const btns = [];
  if (i.pdf) btns.push(`<a class="btn btn-pdf" href="${i.pdf}" target="_blank" rel="noopener">View PDF</a>`);
  for (const link of i.links || []) {
    btns.push(`<a class="btn btn-primary" href="${esc(link.url)}" target="_blank" rel="noopener">${esc(link.label)}</a>`);
  }
  if (i.phone && !i.phone.includes("contact")) {
    btns.push(`<a class="btn btn-secondary" href="tel:${i.phone.replace(/\s/g, "")}">Call</a>`);
  }
  if (i.email) {
    btns.push(`<a class="btn btn-secondary" href="mailto:${i.email}">Email</a>`);
  }
  if (i.address) {
    btns.push(`<a class="btn btn-secondary" href="https://maps.google.com/?q=${encodeURIComponent(i.address)}" target="_blank" rel="noopener">Maps</a>`);
  }

  if (btns.length) {
    html += `<div class="detail-section"><h3>Actions</h3><div class="btn-row">${btns.join("")}</div></div>`;
  }

  if (i.tips?.length) {
    html += `<div class="detail-section"><h3>Important</h3><ul class="tips-list">${i.tips.map((t) => `<li>${esc(t)}</li>`).join("")}</ul></div>`;
  }

  if (i.body) {
    html += `<div class="detail-section"><h3>Full document text</h3><div class="body-text">${esc(i.body)}</div></div>`;
  }

  main.innerHTML = html;
}

function renderAll() {
  currentDay = null;
  currentItem = null;
  updateHeader();

  const types = ["all", "hotel", "transport", "activity"];
  let html = `<div class="filter-bar">${types.map((t) => `<button class="chip${filterType === t ? " active" : ""}" data-filter="${t}">${t === "all" ? "All" : typeLabel(t)}</button>`).join("")}</div>`;

  const sorted = Object.values(tripData.items).sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time));
  for (const item of sorted) {
    if (filterType !== "all" && item.type !== filterType) continue;
    html += itemCardHtml(item);
  }

  main.innerHTML = html;
  main.querySelectorAll(".chip").forEach((el) => {
    el.addEventListener("click", () => { filterType = el.dataset.filter; renderAll(); });
  });
  bindItemCards();
}

function renderDocs() {
  currentDay = null;
  currentItem = null;
  updateHeader();
  main.innerHTML = `<p style="color:var(--muted);margin-bottom:12px;font-size:.88rem">All original booking PDFs — available offline after first load.</p>`;

  const list = document.createElement("div");
  list.className = "pdf-list";

  for (const pdf of tripData.pdfs.sort()) {
    const name = pdf.split("/").pop().replace(".pdf", "");
    const el = document.createElement("a");
    el.className = "item-card";
    el.href = `documents/${pdf}`;
    el.target = "_blank";
    el.rel = "noopener";
    el.innerHTML = `<div class="item-type">PDF</div><div class="item-title">${esc(name)}</div><div class="item-meta">${esc(pdf)}</div>`;
    list.appendChild(el);
  }
  main.appendChild(list);
}

function openDay(date) {
  currentView = "day";
  renderDay(date);
}

function openItem(id) {
  currentView = "item";
  renderItem(id);
}

function goBack() {
  if (currentView === "item") {
    if (currentDay) { currentView = "day"; renderDay(currentDay.date); }
    else { currentView = "all"; renderAll(); setActiveTab("all"); }
  } else if (currentView === "day") {
    currentView = "days";
    currentDay = null;
    renderDays();
    setActiveTab("days");
  }
}

function setActiveTab(view) {
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.view === view);
  });
}

function navigate(view) {
  currentView = view;
  currentDay = null;
  currentItem = null;
  setActiveTab(view);
  if (view === "days") renderDays();
  else if (view === "all") renderAll();
  else if (view === "docs") renderDocs();
}

async function loadData() {
  const res = await fetch("trip-data.json");
  if (!res.ok) throw new Error("Failed to load trip data");
  tripData = await res.json();
}

function updateOnlineStatus() {
  const offline = !navigator.onLine;
  offlineBadge.classList.toggle("hidden", !offline);
}

async function registerSW() {
  if (!("serviceWorker" in navigator)) return;
  try {
    const reg = await navigator.serviceWorker.register("./sw.js");
    if (reg.installing) {
      reg.installing.addEventListener("statechange", () => {
        if (reg.installing?.state === "installed" && navigator.serviceWorker.controller) {
          showToast("Update ready — refresh to apply");
        }
      });
    }
  } catch (e) {
    console.warn("SW registration failed:", e);
  }
}

async function init() {
  backBtn.addEventListener("click", goBack);
  document.querySelectorAll(".tab").forEach((t) => {
    t.addEventListener("click", () => navigate(t.dataset.view));
  });
  window.addEventListener("online", updateOnlineStatus);
  window.addEventListener("offline", updateOnlineStatus);
  updateOnlineStatus();

  try {
    await loadData();
    renderDays();
    await registerSW();
  } catch (e) {
    main.innerHTML = `<div class="detail-section"><p>Could not load trip data. Make sure you opened the app via a web server (not file://).</p><p style="margin-top:8px;color:var(--muted);font-size:.85rem">${esc(e.message)}</p></div>`;
  }
}

init();
