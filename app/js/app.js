/* Europe Trip PWA */
let tripData = null;
let activeTab = "today";
let currentView = "today";
let currentDay = null;
let currentItem = null;
let currentPdf = null;
let filterType = "all";

const NOTES_KEY = "europe-trip-day-notes";

const $ = (sel) => document.querySelector(sel);
const appEl = $("#app");
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

function attrEsc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
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

async function copyText(text) {
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    showToast("Copied!");
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
    showToast("Copied!");
  }
}

function bindCopyButtons(root) {
  (root || main).querySelectorAll("[data-copy-value]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      copyText(btn.dataset.copyValue);
    });
  });
}

function getDayNote(date) {
  try {
    const notes = JSON.parse(localStorage.getItem(NOTES_KEY) || "{}");
    return notes[date] || "";
  } catch {
    return "";
  }
}

function saveDayNote(date, text) {
  try {
    const notes = JSON.parse(localStorage.getItem(NOTES_KEY) || "{}");
    if (text.trim()) notes[date] = text;
    else delete notes[date];
    localStorage.setItem(NOTES_KEY, JSON.stringify(notes));
  } catch {
    /* ignore */
  }
}

function dayNotesHtml(date) {
  const note = getDayNote(date);
  return `
    <div class="detail-section day-notes">
      <h3>My notes</h3>
      <textarea class="day-notes-input" data-date="${esc(date)}" rows="3" placeholder="Room number, host tips, reminders…">${esc(note)}</textarea>
    </div>`;
}

function bindDayNotes() {
  main.querySelectorAll(".day-notes-input").forEach((el) => {
    let timer;
    const save = () => saveDayNote(el.dataset.date, el.value);
    el.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(save, 400);
    });
    el.addEventListener("blur", save);
  });
}

function timeSortKey(time) {
  if (!time) return 99999;
  const m = String(time).match(/(\d{1,2}):(\d{2})/);
  if (!m) return 99999;
  return parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
}

function parseItemDateTime(dateStr, timeStr) {
  if (!timeStr) return null;
  const m = String(timeStr).match(/(\d{1,2}):(\d{2})/);
  if (!m) return null;
  const h = m[1].padStart(2, "0");
  const min = m[2];
  return new Date(`${dateStr}T${h}:${min}:00`);
}

function sortedDayItems(day) {
  return day.items
    .map((id) => tripData.items[id])
    .filter(Boolean)
    .sort((a, b) => timeSortKey(a.time) - timeSortKey(b.time));
}

function dayWarnings(day) {
  const msgs = [];
  for (const id of day.items) {
    const item = tripData.items[id];
    if (!item?.warning) continue;
    const tip = item.tips?.find((t) => t.includes("⚠️") || /conflict|verify|rebook/i.test(t));
    msgs.push(tip || item.summary || item.title);
  }
  return msgs;
}

function warningsBannerHtml(day) {
  const msgs = dayWarnings(day);
  if (!msgs.length) return "";
  return `
    <div class="warn-banner" role="alert">
      <strong>⚠️ Schedule alert</strong>
      ${msgs.map((m) => `<p>${esc(m.replace(/^⚠️\s*/, ""))}</p>`).join("")}
    </div>`;
}

function detailRowHtml(label, val, copyable = false) {
  if (!val) return "";
  const copyBtn = copyable
    ? `<button type="button" class="copy-btn" data-copy-value="${attrEsc(val)}">Copy</button>`
    : "";
  return `
    <div class="detail-row${copyable ? " has-copy" : ""}">
      <span class="label">${esc(label)}</span>
      <span class="value">${esc(val)}${copyBtn}</span>
    </div>`;
}

function getTodayDay() {
  const today = todayStr();
  return tripData.days.find((d) => d.date === today) || null;
}

function isDuringTrip() {
  const today = todayStr();
  return today >= tripData.trip.start && today <= tripData.trip.end;
}

function getNextUp() {
  const now = new Date();
  const today = todayStr();
  let best = null;
  let bestDt = null;

  for (const day of tripData.days) {
    for (const id of day.items) {
      const item = tripData.items[id];
      if (!item) continue;
      const dt = parseItemDateTime(day.date, item.time);
      if (dt) {
        if (dt >= now && (!bestDt || dt < bestDt)) {
          best = { item, day, dt };
          bestDt = dt;
        }
      } else if (day.date >= today && !best) {
        best = { item, day, dt: null };
      }
    }
  }
  return best;
}

function nextUpCardHtml() {
  const next = getNextUp();
  if (!next) return "";
  const timeLabel = next.item.time || (next.day.date === todayStr() ? "Today" : next.day.date);
  return `
    <div class="next-up-card">
      <div class="next-up-label">Next up</div>
      <button type="button" class="next-up-body" data-id="${esc(next.item.id)}">
        <span class="next-up-time">${esc(timeLabel)}</span>
        <span class="next-up-title">${esc(next.item.summary || next.item.title)}</span>
        <span class="next-up-meta">${esc(next.day.location)}</span>
      </button>
    </div>`;
}

function bindNextUp() {
  main.querySelectorAll(".next-up-body[data-id]").forEach((el) => {
    el.addEventListener("click", () => {
      const item = tripData.items[el.dataset.id];
      if (item?.date) {
        currentDay = tripData.days.find((d) => d.date === item.date) || null;
      }
      openItem(el.dataset.id);
    });
  });
}

function updateHeader() {
  if (currentView === "pdf" && currentPdf) {
    headerTitle.textContent = currentPdf.title;
    headerSub.textContent = "PDF";
    backBtn.classList.remove("hidden");
    backBtn.classList.add("labeled");
  } else {
    backBtn.classList.remove("labeled");
    if (currentItem) {
      headerTitle.textContent = currentItem.title;
      headerSub.textContent = typeLabel(currentItem.type);
      backBtn.classList.remove("hidden");
    } else if (currentDay) {
      headerTitle.textContent = currentDay.label;
      headerSub.textContent = currentDay.location;
      backBtn.classList.remove("hidden");
    } else if (currentView === "today" || activeTab === "today") {
      const td = getTodayDay();
      headerTitle.textContent = "Today";
      headerSub.textContent = td ? td.location : tripData.trip.subtitle;
      backBtn.classList.add("hidden");
    } else {
      headerTitle.textContent = tripData.trip.title;
      headerSub.textContent = `${tripData.trip.start} → ${tripData.trip.end}`;
      backBtn.classList.add("hidden");
    }
  }
}

function todayStr() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

function photoSrc(obj) {
  return (obj && (obj.photo || obj.photo_data)) || "";
}

let pdfjsReady = null;

function ensurePdfJs() {
  if (window.pdfjsLib) {
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = "./vendor/pdf.worker.min.js";
    return Promise.resolve(window.pdfjsLib);
  }
  if (pdfjsReady) return pdfjsReady;
  pdfjsReady = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "./vendor/pdf.min.js";
    script.onload = () => {
      window.pdfjsLib.GlobalWorkerOptions.workerSrc = "./vendor/pdf.worker.min.js";
      resolve(window.pdfjsLib);
    };
    script.onerror = () => reject(new Error("Could not load PDF viewer"));
    document.head.appendChild(script);
  });
  return pdfjsReady;
}

function renderDays() {
  currentView = "days";
  currentDay = null;
  currentItem = null;
  updateHeader();

  const today = todayStr();
  let html = `
    <div class="hero">
      <h2>${esc(tripData.trip.subtitle)}</h2>
      <p>${esc(tripData.trip.route)}</p>
    </div>
    ${nextUpCardHtml()}
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
  bindNextUp();
}

function renderToday() {
  currentView = "today";
  currentDay = null;
  currentItem = null;
  updateHeader();

  const today = todayStr();
  const day = getTodayDay();

  if (!day || !isDuringTrip()) {
    main.innerHTML = `
      <div class="detail-section">
        <h3>${isDuringTrip() ? "No plan for today" : "Trip dates"}</h3>
        <p style="color:var(--muted);line-height:1.5">${isDuringTrip()
          ? "Nothing scheduled for today."
          : `Your trip runs ${esc(tripData.trip.start)} → ${esc(tripData.trip.end)}.`}</p>
        <p style="margin-top:12px"><button type="button" class="btn btn-primary" data-goto-days>View all days</button></p>
      </div>
      ${nextUpCardHtml()}`;
    main.querySelector("[data-goto-days]")?.addEventListener("click", () => navigate("days"));
    bindNextUp();
    return;
  }

  let html = `
    <div class="today-header">
      <div class="today-date">${esc(day.label)}</div>
      <div class="today-loc">${esc(day.location)}</div>
    </div>
    ${nextUpCardHtml()}
    ${warningsBannerHtml(day)}`;

  const dayPhoto = photoSrc(day);
  if (dayPhoto) {
    html += `
      <div class="day-hero">
        <div class="day-hero-photo-wrap">
          <img class="day-hero-photo" src="${dayPhoto}" alt="${esc(day.city || day.location)}">
          <div class="day-hero-overlay">
            <div class="day-hero-city">${esc(day.city || day.location)}</div>
          </div>
        </div>
      </div>`;
  }

  html += dayNotesHtml(day.date);

  if (!day.items.length) {
    html += `<div class="detail-section"><p style="color:var(--muted)">No booked activities — travel or free day.</p></div>`;
  } else {
    html += dayScheduleHtml(day);
  }

  main.innerHTML = html;
  bindItemCards();
  bindDayNotes();
  bindNextUp();
}

function dayScheduleHtml(day) {
  const items = sortedDayItems(day);
  if (items.length >= 2 || items.some((i) => i.time)) {
    return `<div class="timeline">${items.map((item) => timelineItemHtml(item)).join("")}</div>`;
  }
  return items.map((item) => itemCardHtml(item)).join("");
}

function timelineItemHtml(item) {
  if (!item) return "";
  const timeLabel = item.time || "—";
  const meta = item.confirmation ? `#${item.confirmation}` : "";
  return `
    <div class="timeline-item type-${item.type}${item.warning ? " warning" : ""}">
      <div class="timeline-time">${esc(timeLabel)}</div>
      <div class="timeline-track">
        <div class="timeline-dot"></div>
        <button type="button" class="timeline-card item-card type-${item.type}${item.warning ? " warning" : ""}" data-id="${item.id}">
          <div class="item-type">${typeLabel(item.type)}</div>
          <div class="item-title">${esc(item.summary || item.title)}</div>
          ${meta ? `<div class="item-meta">${esc(meta)}</div>` : ""}
        </button>
      </div>
    </div>`;
}

function renderDay(date) {
  currentView = "day";
  currentDay = tripData.days.find((d) => d.date === date);
  currentItem = null;
  updateHeader();

  if (!currentDay) return activeTab === "today" ? renderToday() : renderDays();

  let html = warningsBannerHtml(currentDay);
  const dayPhoto = photoSrc(currentDay);
  if (dayPhoto) {
    html += `
      <div class="day-hero">
        <div class="day-hero-photo-wrap">
          <img class="day-hero-photo" src="${dayPhoto}" alt="${esc(currentDay.city || currentDay.location)}">
          <div class="day-hero-overlay">
            <div class="day-hero-city">${esc(currentDay.city || currentDay.location)}</div>
          </div>
        </div>
        ${currentDay.photo_credit ? `<div class="photo-credit">${esc(currentDay.photo_credit)}</div>` : ""}
      </div>`;
  }

  html += dayNotesHtml(currentDay.date);

  if (!currentDay.items.length) {
    html += `<div class="detail-section"><p style="color:var(--muted)">No booked activities — travel or free day.</p></div>`;
  } else {
    html += dayScheduleHtml(currentDay);
  }
  main.innerHTML = html;
  bindItemCards();
  bindDayNotes();
}

function itemCardHtml(item) {
  if (!item) return "";
  const meta = [item.time, item.confirmation ? `#${item.confirmation}` : ""].filter(Boolean).join(" · ");
  const copyBtn = item.confirmation
    ? `<button type="button" class="copy-chip" data-copy-value="${attrEsc(item.confirmation)}">Copy #</button>`
    : "";
  return `
    <button class="item-card type-${item.type}${item.warning ? " warning" : ""}" data-id="${item.id}">
      <div class="item-type">${typeLabel(item.type)}</div>
      <div class="item-title">${esc(item.summary || item.title)}</div>
      ${meta ? `<div class="item-meta">${esc(meta)} ${copyBtn}</div>` : copyBtn ? `<div class="item-meta">${copyBtn}</div>` : ""}
    </button>`;
}

function bindItemCards() {
  main.querySelectorAll(".item-card[data-id], .timeline-card[data-id]").forEach((el) => {
    el.addEventListener("click", (e) => {
      if (e.target.closest(".copy-chip")) return;
      openItem(el.dataset.id);
    });
  });
  bindCopyButtons(main);
}

function renderItem(id) {
  currentView = "item";
  currentItem = tripData.items[id];
  if (currentItem?.date && !currentDay) {
    currentDay = tripData.days.find((d) => d.date === currentItem.date) || null;
  }
  updateHeader();
  if (!currentItem) return;

  const i = currentItem;
  const rows = [];
  const add = (label, val, copy = false) => { if (val) rows.push({ label, val, copy }); };

  add("Date", i.end_date && i.end_date !== i.date ? `${i.date} → ${i.end_date}` : i.date);
  add("Time", i.time ? (i.end_time ? `${i.time} – ${i.end_time}` : i.time) : "");
  add("Location", i.location);
  add("Address", i.address, true);
  add("Provider", i.provider);
  add("Confirmation", i.confirmation, true);
  add("PIN", i.pin, true);
  add("Guests", i.guests);
  add("Passengers", i.passengers?.join(", "));
  add("Price", i.price);
  add("Duration", i.duration);
  add("Check-in", i.check_in);
  add("Check-out", i.check_out);
  add("Phone", i.phone, Boolean(i.phone && !i.phone.includes("contact")));
  add("Email", i.email);

  let html = "";

  if (i.warning) {
    const warn = i.tips?.find((t) => t.includes("⚠️") || /conflict|verify|rebook/i.test(t)) || "Review this booking carefully.";
    html += `
      <div class="warn-banner" role="alert">
        <strong>⚠️ Schedule alert</strong>
        <p>${esc(warn.replace(/^⚠️\s*/, ""))}</p>
      </div>`;
  }

  html += `
    <div class="detail-section">
      <h3>Details</h3>
      <div class="detail-grid">
        ${rows.map((r) => detailRowHtml(r.label, r.val, r.copy)).join("")}
      </div>
    </div>`;

  if (i.qr_svg) {
    html += `
      <div class="detail-section">
        <h3>QR Code</h3>
        <div class="qr-wrap">${i.qr_svg}</div>
        <div class="qr-caption">
          ${esc(i.qr_data)}
          ${i.qr_data ? `<button type="button" class="copy-btn" data-copy-value="${attrEsc(i.qr_data)}">Copy code</button>` : ""}
        </div>
      </div>`;
  }

  const btns = [];
  if (i.pdf) {
    btns.push(`<button type="button" class="btn btn-pdf" data-pdf="${esc(i.pdf)}" data-pdf-title="${esc(i.title)}">View PDF</button>`);
  }
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
  main.querySelectorAll("[data-pdf]").forEach((el) => {
    el.addEventListener("click", () => openPdf(el.dataset.pdf, el.dataset.pdfTitle));
  });
  bindCopyButtons(main);
}

function openPdf(path, title) {
  currentPdf = { path, title };
  currentView = "pdf";
  appEl.classList.add("view-pdf");
  renderPdf();
}

function renderPdf() {
  updateHeader();
  main.innerHTML = `
    <div class="pdf-viewer">
      <div class="pdf-status">Loading PDF…</div>
      <div class="pdf-pages hidden"></div>
    </div>`;
  loadPdfPages();
}

async function loadPdfPages() {
  const statusEl = main.querySelector(".pdf-status");
  const pagesEl = main.querySelector(".pdf-pages");
  try {
    const pdfjsLib = await ensurePdfJs();
    const pdf = await pdfjsLib.getDocument(currentPdf.path).promise;
    statusEl.textContent = `Rendering ${pdf.numPages} page${pdf.numPages > 1 ? "s" : ""}…`;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const containerWidth = main.clientWidth || window.innerWidth;

    for (let num = 1; num <= pdf.numPages; num++) {
      const page = await pdf.getPage(num);
      const baseViewport = page.getViewport({ scale: 1 });
      const scale = Math.min((containerWidth - 16) / baseViewport.width, 2.5);
      const viewport = page.getViewport({ scale });
      const canvas = document.createElement("canvas");
      canvas.className = "pdf-page";
      const ctx = canvas.getContext("2d");
      canvas.width = Math.floor(viewport.width * dpr);
      canvas.height = Math.floor(viewport.height * dpr);
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      pagesEl.appendChild(canvas);
      await page.render({ canvasContext: ctx, viewport }).promise;
    }

    statusEl.classList.add("hidden");
    pagesEl.classList.remove("hidden");
  } catch (err) {
    statusEl.textContent = `Could not open PDF. ${err.message || "Try again while online."}`;
    console.error("PDF load failed:", err);
  }
}

function renderAll() {
  currentView = "all";
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
  currentView = "docs";
  currentDay = null;
  currentItem = null;
  updateHeader();
  main.innerHTML = `<p style="color:var(--muted);margin-bottom:12px;font-size:.88rem">All original booking PDFs — available offline after first load.</p>`;

  const list = document.createElement("div");
  list.className = "pdf-list";

  for (const pdf of tripData.pdfs.sort()) {
    const name = pdf.split("/").pop().replace(".pdf", "");
    const el = document.createElement("button");
    el.type = "button";
    el.className = "item-card";
    el.innerHTML = `<div class="item-type">PDF</div><div class="item-title">${esc(name)}</div><div class="item-meta">${esc(pdf)}</div>`;
    el.addEventListener("click", () => openPdf(`documents/${pdf}`, name));
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
  if (currentView === "pdf") {
    currentPdf = null;
    appEl.classList.remove("view-pdf");
    if (currentItem) {
      currentView = "item";
      renderItem(currentItem.id);
      return;
    }
    currentView = "docs";
    renderDocs();
    setActiveTab("docs");
    return;
  }
  if (currentView === "item") {
    if (currentDay) {
      currentView = "day";
      renderDay(currentDay.date);
    } else {
      currentView = activeTab;
      navigate(activeTab);
    }
  } else if (currentView === "day") {
    currentDay = null;
    currentView = activeTab;
    if (activeTab === "today") renderToday();
    else renderDays();
    setActiveTab(activeTab);
  }
}

function setActiveTab(view) {
  activeTab = view;
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.view === view);
  });
}

function navigate(view) {
  activeTab = view;
  currentView = view;
  currentDay = null;
  currentItem = null;
  currentPdf = null;
  appEl.classList.remove("view-pdf");
  setActiveTab(view);
  if (view === "today") renderToday();
  else if (view === "days") renderDays();
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
  if (!main || !backBtn) {
    document.body.insertAdjacentHTML(
      "beforeend",
      '<p style="padding:16px;color:#b91c1c">App failed to start. Try refreshing the page.</p>'
    );
    return;
  }

  backBtn.addEventListener("click", goBack);
  document.querySelectorAll(".tab").forEach((t) => {
    t.addEventListener("click", () => navigate(t.dataset.view));
  });
  window.addEventListener("online", updateOnlineStatus);
  window.addEventListener("offline", updateOnlineStatus);
  updateOnlineStatus();

  try {
    await loadData();
    if (isDuringTrip()) navigate("today");
    else navigate("days");
  } catch (e) {
    main.innerHTML = `<div class="detail-section"><p>Could not load trip data.</p><p style="margin-top:8px;color:var(--muted);font-size:.85rem">${esc(e.message)}</p><p style="margin-top:12px"><button type="button" class="btn btn-primary" id="retry-load">Try again</button></p></div>`;
    document.getElementById("retry-load")?.addEventListener("click", () => init());
  }
}

init();
