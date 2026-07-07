const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

const INIT_DATA = tg?.initData || "";

function api(path, opts = {}) {
  opts.headers = Object.assign({ "Content-Type": "application/json", "X-Telegram-Init-Data": INIT_DATA }, opts.headers || {});
  return fetch(path, opts).then(async r => {
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
    return r.json();
  });
}

function esc(s) {
  return (s || "").toString().replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function emptyIllus() {
  return `<svg class="icon-svg empty-illus"><use href="#i-empty"/></svg>`;
}

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 2500);
}

function successPulse() {
  const ov = document.createElement("div");
  ov.className = "success-pulse";
  ov.innerHTML = `<div class="success-pulse-circle"><svg class="icon-svg"><use href="#i-check"/></svg></div>`;
  document.body.appendChild(ov);
  tg?.HapticFeedback?.notificationOccurred?.("success");
  setTimeout(() => ov.remove(), 900);
}

async function uploadPhoto(file) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch("/api/upload_photo", { method: "POST", headers: { "X-Telegram-Init-Data": INIT_DATA }, body: fd });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return (await r.json()).file_id;
}

function photoSlot(onDone) {
  const slot = document.createElement("div");
  slot.className = "photo-slot";
  slot.innerHTML = "📷";
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "image/*";
  input.style.display = "none";
  slot.appendChild(input);
  slot.onclick = () => { if (!slot.classList.contains("filled")) input.click(); };
  input.onchange = async () => {
    const file = input.files[0];
    if (!file) return;
    slot.classList.add("uploading");
    slot.innerHTML = "⏳";
    try {
      const fileId = await uploadPhoto(file);
      slot.classList.remove("uploading");
      slot.classList.add("filled");
      slot.innerHTML = `<img src="${URL.createObjectURL(file)}">`;
      onDone(fileId);
    } catch (e) {
      slot.classList.remove("uploading");
      slot.innerHTML = "📷";
      toast("⚠️ فشل رفع الصورة: " + e.message);
    }
  };
  return slot;
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// ── Router ──────────────────────────────────────────────────────────────────

const stack = [];
const elApp = document.getElementById("app");
const elBack = document.getElementById("backBtn");
const elTitle = document.getElementById("topTitle");
const elNav = document.getElementById("bottomNav");

function go(view, params = {}, title = "KADER DZ") {
  stack.push({ view, params, title });
  render();
}

function back() {
  if (stack.length > 1) { stack.pop(); render(); }
}

function resetTab(tab, view, params, title) {
  stack.length = 0;
  stack.push({ view, params, title, tab });
  render();
  setActiveNav(tab);
}

function setActiveNav(tab) {
  elNav.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
}

elBack.onclick = back;

function render() {
  const top = stack[stack.length - 1];
  elBack.classList.toggle("hidden", stack.length <= 1);
  elTitle.textContent = top.title;
  elApp.classList.remove("view-anim");
  elApp.innerHTML = "";
  VIEWS[top.view](top.params);
  window.scrollTo(0, 0);
  void elApp.offsetWidth;
  elApp.classList.add("view-anim");
}

elNav.querySelectorAll(".nav-item").forEach(btn => {
  btn.onclick = () => {
    const tab = btn.dataset.tab;
    if (tab === "home") resetTab("home", "home", {}, "");
    if (tab === "avito") resetTab("avito", "avito", {}, "🛒 Avito Algeria");
    if (tab === "roommate") resetTab("roommate", "roommate", {}, "🏠 شريك سكن");
    if (tab === "travel") resetTab("travel", "travel", {}, "🧳 هبطلي ولا طلعلي معاك");
    if (tab === "more") resetTab("more", "more", {}, "المزيد");
  };
});

// ── Data caches ───────────────────────────────────────────────────────────

let META = { categories: {}, cities: {}, routes: {} };

async function loadMeta() {
  META.categories = await api("/api/categories");
  META.cities = await api("/api/cities");
  META.routes = await api("/api/routes");
}

// ══════════════════════════════════════════════════════════════════════════
// HOME
// ══════════════════════════════════════════════════════════════════════════

function timeGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "صباح الخير";
  if (h < 18) return "مساء الخير";
  return "مساء الخير";
}

async function viewHome() {
  const firstName = tg?.initDataUnsafe?.user?.first_name || "";
  let heroTitle = firstName ? `${timeGreeting()} يا ${firstName} 👋` : "مرحبًا بك في KADER DZ 🇷🇺";
  let heroSubtitle = "مساعدك الشامل للدراسة والحياة في روسيا — تصفح، انشر، وتواصل مع المجتمع كله من هنا.";
  let statsLine = "";
  let counts = { avito_count: 0, roommate_count: 0, travel_count: 0 };
  try {
    const { text } = await api("/api/home_banner");
    if (text) { heroTitle = "📢 إعلان من الإدارة"; heroSubtitle = text; }
  } catch (e) { /* ignore, fall back to default welcome */ }
  try {
    const stats = await api("/api/stats");
    counts = stats;
    if (stats.posts_this_week > 0) statsLine = `<div class="hero-stat">+${stats.posts_this_week} إعلان ونشاط هذا الأسبوع</div>`;
  } catch (e) { /* ignore */ }

  const countLbl = n => n > 0 ? `${n} إعلان نشط` : "كن أول من ينشر";

  elApp.innerHTML = `
    <div class="hero">
      <div class="title">${esc(heroTitle)}</div>
      <div class="subtitle">${esc(heroSubtitle)}</div>
      ${statsLine}
    </div>

    <div class="feature-row">
      <button class="feature-card" data-go="travel">
        <span class="icon-circle t-rose"><svg class="icon-svg"><use href="#i-suitcase"/></svg></span>
        <span class="feature-text"><span class="label">هبطلي ولا طلعلي معاك</span><span class="feature-count">${countLbl(counts.travel_count)}</span></span>
        <span class="chevron">‹</span>
      </button>
      <button class="feature-card" data-go="avito">
        <span class="icon-circle"><svg class="icon-svg"><use href="#i-cart"/></svg></span>
        <span class="feature-text"><span class="label">Avito Algeria</span><span class="feature-count">${countLbl(counts.avito_count)}</span></span>
        <span class="chevron">‹</span>
      </button>
      <button class="feature-card" data-go="scamCheck">
        <span class="icon-circle t-danger"><svg class="icon-svg"><use href="#i-shield"/></svg></span>
        <span class="feature-text"><span class="label">شرلوك الجزائري</span><span class="feature-count">تحقق قبل ما تحول فلوسك</span></span>
        <span class="chevron">‹</span>
      </button>
    </div>

    <div class="section-title">الأدلة والخدمات</div>
    <div class="compact-grid">
      <button class="compact-tile" data-go="roommate"><span class="icon-circle t-green"><svg class="icon-svg"><use href="#i-users"/></svg></span><span class="label">شريك سكن</span></button>
      <button class="compact-tile" data-go="content" data-id="guide"><span class="icon-circle t-blue"><svg class="icon-svg"><use href="#i-book"/></svg></span><span class="label">دليلك الشامل</span></button>
      <button class="compact-tile" data-go="content" data-id="consular"><span class="icon-circle t-violet"><svg class="icon-svg"><use href="#i-building"/></svg></span><span class="label">الخدمات القنصلية</span></button>
      <button class="compact-tile" data-go="content" data-id="services"><span class="icon-circle t-teal"><svg class="icon-svg"><use href="#i-gear"/></svg></span><span class="label">الخدمات</span></button>
      <button class="compact-tile" data-go="inquiry"><span class="icon-circle t-amber"><svg class="icon-svg"><use href="#i-edit"/></svg></span><span class="label">تقديم استفسار</span></button>
      <button class="compact-tile" data-go="content" data-id="about"><span class="icon-circle t-slate"><svg class="icon-svg"><use href="#i-info"/></svg></span><span class="label">عن البوت</span></button>
    </div>`;
  elApp.querySelectorAll(".feature-card, .compact-tile").forEach(btn => {
    btn.onclick = () => {
      const v = btn.dataset.go;
      const label = btn.querySelector(".label").textContent;
      if (v === "content") go("contentCategory", { catId: btn.dataset.id }, label);
      else go(v, {}, label);
    };
  });
}

// ══════════════════════════════════════════════════════════════════════════
// MORE (secondary sections, reachable from bottom nav)
// ══════════════════════════════════════════════════════════════════════════

function viewMore() {
  elApp.innerHTML = `
    <div class="list-item" data-go="content" data-id="guide"><span class="row-icon t-blue"><svg class="icon-svg"><use href="#i-book"/></svg></span><span class="title">دليلك الشامل</span><span class="chevron">‹</span></div>
    <div class="list-item" data-go="content" data-id="consular"><span class="row-icon t-violet"><svg class="icon-svg"><use href="#i-building"/></svg></span><span class="title">الخدمات القنصلية</span><span class="chevron">‹</span></div>
    <div class="list-item" data-go="content" data-id="services"><span class="row-icon t-teal"><svg class="icon-svg"><use href="#i-gear"/></svg></span><span class="title">الخدمات</span><span class="chevron">‹</span></div>
    <div class="list-item" data-go="inquiry"><span class="row-icon t-amber"><svg class="icon-svg"><use href="#i-edit"/></svg></span><span class="title">تقديم استفسار</span><span class="chevron">‹</span></div>
    <div class="list-item" data-go="content" data-id="about"><span class="row-icon t-slate"><svg class="icon-svg"><use href="#i-info"/></svg></span><span class="title">عن البوت</span><span class="chevron">‹</span></div>`;
  elApp.querySelectorAll(".list-item").forEach(el => {
    el.onclick = () => {
      const v = el.dataset.go;
      const label = el.querySelector(".title").textContent;
      if (v === "content") go("contentCategory", { catId: el.dataset.id }, label);
      else go(v, {}, label);
    };
  });
}

// ══════════════════════════════════════════════════════════════════════════
// CONTENT (guide / consular / services / about)
// ══════════════════════════════════════════════════════════════════════════

let CONTENT_TREE = null;

async function viewContentCategory({ catId }) {
  if (!CONTENT_TREE) CONTENT_TREE = await api("/api/content");
  const cat = CONTENT_TREE.find(c => c.id === catId);
  let html = "";
  for (const sec of cat.sections) {
    if (sec.title) html += `<div class="section-title">${esc(sec.title)}</div>`;
    for (const page of sec.pages) {
      html += `<div class="list-item" data-slug="${page.slug}">
        <span class="title">${esc(page.title)}</span><span class="chevron">‹</span>
      </div>`;
    }
  }
  elApp.innerHTML = html;
  elApp.querySelectorAll(".list-item").forEach(el => {
    el.onclick = () => {
      const page = cat.sections.flatMap(s => s.pages).find(p => p.slug === el.dataset.slug);
      go("contentPage", { page }, page.title);
    };
  });
}

function viewContentPage({ page }) {
  elApp.innerHTML = `<div class="page-body">${page.body}</div>`;
}

// ══════════════════════════════════════════════════════════════════════════
// AVITO ALGERIA
// ══════════════════════════════════════════════════════════════════════════

const avitoState = { category: "all", q: "", sort: "" };

async function viewAvito() {
  elApp.innerHTML = `
    <div class="search-bar"><svg class="icon-svg"><use href="#i-search"/></svg><input id="avitoSearch" placeholder="بحث عن منتج، مدينة..."></div>
    <div class="segmented" id="avitoSort">
      <div class="seg" data-v="">🔄 الأحدث</div>
      <div class="seg" data-v="asc">💰 الأرخص أولًا</div>
      <div class="seg" data-v="desc">💎 الأغلى أولًا</div>
    </div>
    <div id="avitoFilters" class="filters"></div>
    <div id="avitoGrid" class="grid"></div>
    <div id="avitoEmpty" class="empty hidden">${emptyIllus()}لا توجد إعلانات بهذه المعايير</div>
    <button class="fab" id="avitoPostBtn" aria-label="نشر إعلان مجانًا"><svg class="icon-svg"><use href="#i-plus"/></svg></button>`;
  renderAvitoFilters();
  renderSegmented(document.getElementById("avitoSort"), avitoState.sort, v => { avitoState.sort = v; loadAvitoGrid(); });
  document.getElementById("avitoSearch").oninput = debounce(e => { avitoState.q = e.target.value; loadAvitoGrid(); }, 350);
  loadAvitoGrid();
  document.getElementById("avitoPostBtn").onclick = () => go("avitoPost", {}, "نشر إعلان جديد");
}

function renderSegmented(el, active, onPick) {
  el.querySelectorAll(".seg").forEach(seg => {
    seg.classList.toggle("active", seg.dataset.v === active);
    seg.onclick = () => { onPick(seg.dataset.v); el.querySelectorAll(".seg").forEach(s => s.classList.toggle("active", s === seg)); };
  });
}

function renderAvitoFilters() {
  const el = document.getElementById("avitoFilters");
  el.innerHTML = "";
  const chips = [["all", "🔄 الكل"], ...Object.entries(META.categories)];
  for (const [key, label] of chips) {
    const chip = document.createElement("button");
    chip.className = "chip" + (avitoState.category === key ? " active" : "");
    chip.textContent = label;
    chip.onclick = () => { avitoState.category = key; renderAvitoFilters(); loadAvitoGrid(); };
    el.appendChild(chip);
  }
}

function showSkeleton(grid, count = 6) {
  grid.innerHTML = "";
  for (let i = 0; i < count; i++) {
    const sk = document.createElement("div");
    sk.className = "skel-card";
    sk.innerHTML = `<div class="skel-img"></div><div class="skel-line"></div><div class="skel-line short"></div>`;
    grid.appendChild(sk);
  }
}

function catEmoji(key) {
  const label = META.categories[key] || "";
  return label.split(" ")[0] || "📦";
}

const CAT_TINT = { electronics: "t-blue", furniture: "t-amber", clothes: "t-rose", algerian: "t-green", other: "t-slate" };
function catTint(key) { return CAT_TINT[key] || "t-slate"; }

function expiryTag(rec) {
  if (!rec.expires_at) return "";
  const daysLeft = (new Date(rec.expires_at) - Date.now()) / 86400000;
  if (daysLeft > 0 && daysLeft <= 3) return `<span class="expiry-tag">⏳ ينتهي قريبًا</span>`;
  return "";
}

function formatPrice(price) {
  const s = esc(price);
  const m = s.match(/^([\d\s.,]+)(.*)$/);
  if (!m || !m[1].trim()) return s;
  return `<span class="price-num">${m[1].trim()}</span><span class="price-cur">${m[2].trim()}</span>`;
}

async function loadAvitoGrid() {
  const grid = document.getElementById("avitoGrid");
  const empty = document.getElementById("avitoEmpty");
  showSkeleton(grid);
  empty.classList.add("hidden");
  const qs = new URLSearchParams({ category: avitoState.category, q: avitoState.q, sort: avitoState.sort });
  const items = await api(`/api/items?${qs}`);
  grid.innerHTML = "";
  empty.classList.toggle("hidden", items.length > 0);
  if (!items.length) empty.innerHTML = `${emptyIllus()}لا توجد إعلانات بهذه المعايير`;
  for (const [idx, item] of items.entries()) {
    const card = document.createElement("div");
    card.className = "card";
    card.style.setProperty("--i", idx % 10);
    const seller = item.username ? `@${esc(item.username)}` : esc(item.first_name || "—");
    card.innerHTML = `
      <div class="img-wrap">
        ${item.photo_id ? `<img src="/api/photo/${item.photo_id}" onerror="this.parentElement.innerHTML='<span class=placeholder-icon>📦</span>'">` : `<span class="placeholder-icon">📦</span>`}
        <span class="cat-badge ${catTint(item.category)}">${catEmoji(item.category)}</span>
        <span class="price-badge">${formatPrice(item.price)}</span>
      </div>
      <div class="body">
        <div class="title">${esc(item.title)}</div>
        <div class="meta">📍 ${esc(item.city)}</div>
        <div class="meta">👤 ${seller}${verifiedBadge(item)}</div>
        ${expiryTag(item)}
      </div>`;
    card.onclick = () => openAvitoDetail(item.id);
    grid.appendChild(card);
  }
}

function verifiedBadge(record) {
  return record.seller_verified ? ' <span class="verified-badge" title="معلن موثّق"><svg class="icon-svg"><use href="#i-check"/></svg>موثّق</span>' : "";
}

async function openAvitoDetail(id) {
  const item = await api(`/api/items/${id}`);
  const seller = item.username ? `@${esc(item.username)}` : esc(item.first_name);
  const contact = item.username
    ? `<a class="btn" href="https://t.me/${item.username}">💬 تواصل عبر تيليجرام</a>`
    : `<div class="detail-row" style="color:var(--hint)">للتواصل، استخدم البوت مباشرة</div>`;
  showDetail(`
    ${item.photo_id ? `<img src="/api/photo/${item.photo_id}">` : ""}
    <h2>${esc(item.title)}</h2>
    <div class="detail-row"><b>السعر:</b> ${esc(item.price)}</div>
    <div class="detail-row"><b>المدينة:</b> ${esc(item.city)}</div>
    <div class="detail-row"><b>الوصف:</b> ${esc(item.description)}</div>
    <div class="detail-row"><b>البائع:</b> ${seller}${verifiedBadge(item)}</div>
    ${contact}`);
}

function viewAvitoPost() {
  elApp.innerHTML = `
    <div class="form-group"><label>صورة المنتج (مطلوبة)</label><div class="photo-slots" id="photoSlots"></div></div>
    <div class="form-group">
      <label>الفئة</label>
      <div class="option-row" id="catPills"></div>
    </div>
    <div class="form-group"><label>عنوان الإعلان</label><input id="f_title" placeholder="مثال: iPhone 14 — حالة ممتازة"></div>
    <div class="form-group"><label>السعر</label><input id="f_price" class="ltr-field" dir="ltr" placeholder="مثال: 50 000 DZD"></div>
    <div class="form-group"><label>المدينة</label><input id="f_city" placeholder="مثال: موسكو"></div>
    <div class="form-group"><label>الوصف</label><textarea id="f_desc" placeholder="تفاصيل المنتج..."></textarea></div>
    <button class="btn" id="submitBtn">نشر الإعلان</button>`;
  let selectedCat = null, photoId = null;
  document.getElementById("photoSlots").appendChild(photoSlot(fid => { photoId = fid; }));
  const pills = document.getElementById("catPills");
  for (const [key, label] of Object.entries(META.categories)) {
    const pill = document.createElement("div");
    pill.className = "option-pill";
    pill.textContent = label;
    pill.onclick = () => {
      selectedCat = key;
      pills.querySelectorAll(".option-pill").forEach(p => p.classList.remove("selected"));
      pill.classList.add("selected");
    };
    pills.appendChild(pill);
  }
  document.getElementById("submitBtn").onclick = async () => {
    const title = document.getElementById("f_title").value.trim();
    const price = document.getElementById("f_price").value.trim();
    const city = document.getElementById("f_city").value.trim();
    const desc = document.getElementById("f_desc").value.trim();
    if (!photoId) { toast("⚠️ يجب إضافة صورة للمنتج"); return; }
    if (!selectedCat || !title || !price || !city || !desc) { toast("⚠️ يرجى تعبئة جميع الحقول"); return; }
    try {
      await api("/api/submit/item", { method: "POST", body: JSON.stringify({ category: selectedCat, title, price, city, description: desc, photo_id: photoId }) });
      successPulse();
      toast("✅ تم استلام إعلانك، بانتظار المراجعة");
      back();
    } catch (e) { toast("⚠️ " + e.message); }
  };
}

// ══════════════════════════════════════════════════════════════════════════
// ROOMMATE
// ══════════════════════════════════════════════════════════════════════════

const rmState = { city: "all", q: "", sort: "" };

async function viewRoommate() {
  elApp.innerHTML = `
    <div class="search-bar"><svg class="icon-svg"><use href="#i-search"/></svg><input id="rmSearch" placeholder="بحث عن مدينة، تفاصيل..."></div>
    <div class="segmented" id="rmSort">
      <div class="seg" data-v="">🔄 الأحدث</div>
      <div class="seg" data-v="asc">💰 الأرخص أولًا</div>
      <div class="seg" data-v="desc">💎 الأغلى أولًا</div>
    </div>
    <div id="rmFilters" class="filters"></div>
    <div id="rmGrid" class="grid"></div>
    <div id="rmEmpty" class="empty hidden">${emptyIllus()}لا توجد إعلانات بعد</div>
    <button class="fab" id="rmPostBtn" aria-label="نشر إعلان سكن"><svg class="icon-svg"><use href="#i-plus"/></svg></button>`;
  renderRmFilters();
  renderSegmented(document.getElementById("rmSort"), rmState.sort, v => { rmState.sort = v; loadRmGrid(); });
  document.getElementById("rmSearch").oninput = debounce(e => { rmState.q = e.target.value; loadRmGrid(); }, 350);
  loadRmGrid();
  document.getElementById("rmPostBtn").onclick = () => go("roommatePost", {}, "نشر إعلان سكن");
}

function renderRmFilters() {
  const el = document.getElementById("rmFilters");
  el.innerHTML = "";
  const chips = [["all", "🔄 كل المدن"], ...Object.entries(META.cities)];
  for (const [key, label] of chips) {
    const chip = document.createElement("button");
    chip.className = "chip" + (rmState.city === key ? " active" : "");
    chip.textContent = label;
    chip.onclick = () => { rmState.city = key; renderRmFilters(); loadRmGrid(); };
    el.appendChild(chip);
  }
}

async function loadRmGrid() {
  const grid = document.getElementById("rmGrid");
  const empty = document.getElementById("rmEmpty");
  showSkeleton(grid);
  empty.classList.add("hidden");
  const qs = new URLSearchParams({ city: rmState.city, q: rmState.q, sort: rmState.sort });
  const items = await api(`/api/listings?${qs}`);
  grid.innerHTML = "";
  empty.classList.toggle("hidden", items.length > 0);
  if (!items.length) empty.innerHTML = `${emptyIllus()}لا توجد إعلانات بهذه المعايير`;
  for (const [idx, item] of items.entries()) {
    const card = document.createElement("div");
    card.className = "card";
    card.style.setProperty("--i", idx % 10);
    const rtype = item.type === "need" ? "🔍 يبحث" : "🏠 عنده غرفة";
    const roomBadge = item.room_type === "studio" ? "🏠" : "🛏️";
    const roomTint = item.room_type === "studio" ? "t-teal" : "t-violet";
    const photo = (item.photos || [])[0];
    const poster = item.username ? `@${esc(item.username)}` : esc(item.first_name || "—");
    card.innerHTML = `
      <div class="img-wrap">
        ${photo ? `<img src="/api/photo/${photo}" onerror="this.parentElement.innerHTML='<span class=placeholder-icon>🏠</span>'">` : `<span class="placeholder-icon">🏠</span>`}
        <span class="cat-badge ${roomTint}">${roomBadge}</span>
        <span class="price-badge">${formatPrice(item.price)}</span>
      </div>
      <div class="body">
        <div class="title">${rtype} — ${esc(item.city)}</div>
        <div class="meta"><span class="metro-pill ${item.metro_distance === "near" ? "near" : "far"}"><svg class="icon-svg"><use href="#i-metro"/></svg>${item.metro_distance === "near" ? "قريب من المترو" : "بعيد عن المترو"}</span></div>
        <div class="meta">👤 ${poster}${verifiedBadge(item)}</div>
        ${expiryTag(item)}
      </div>`;
    card.onclick = () => openRmDetail(item.id);
    grid.appendChild(card);
  }
}

async function openRmDetail(id) {
  const item = await api(`/api/listings/${id}`);
  const poster = item.username ? `@${esc(item.username)}` : esc(item.first_name);
  const contact = item.username
    ? `<a class="btn" href="https://t.me/${item.username}">💬 تواصل عبر تيليجرام</a>`
    : `<div class="detail-row" style="color:var(--hint)">للتواصل، استخدم البوت مباشرة</div>`;
  const rtype = item.type === "need" ? "🔍 يبحث عن شريك سكن" : "🏠 عنده غرفة/وحدة";
  const photosHtml = (item.photos || []).map(p => `<img src="/api/photo/${p}">`).join("");
  showDetail(`
    ${photosHtml}
    <h2>${rtype}</h2>
    <div class="detail-row"><b>المدينة:</b> ${esc(item.city)}</div>
    <div class="detail-row"><b>السعر:</b> ${esc(item.price)}</div>
    <div class="detail-row"><b>المترو:</b> ${item.metro_distance === "near" ? "قريب" : "بعيد"}</div>
    <div class="detail-row"><b>التفاصيل:</b> ${esc(item.description)}</div>
    <div class="detail-row"><b>المُعلن:</b> ${poster}${verifiedBadge(item)}</div>
    ${contact}`);
}

function viewRoommatePost() {
  elApp.innerHTML = `
    <div class="form-group"><label>صور الوحدة (اختياري، حتى صورتين)</label><div class="photo-slots" id="photoSlots"></div></div>
    <div class="form-group"><label>نوع الإعلان</label>
      <div class="option-row">
        <div class="option-pill" data-v="need">🔍 أبحث عن شريك</div>
        <div class="option-pill" data-v="have">🏠 عندي غرفة</div>
      </div>
    </div>
    <div class="form-group"><label>نوع الوحدة</label>
      <div class="option-row">
        <div class="option-pill" data-rv="room1">🛏️ غرفة في شقة</div>
        <div class="option-pill" data-rv="studio">🏠 استوديو</div>
      </div>
    </div>
    <div class="form-group"><label>المدينة</label><input id="f_city" placeholder="مثال: موسكو"></div>
    <div class="form-group"><label>السعر الشهري</label><input id="f_price" class="ltr-field" dir="ltr" placeholder="مثال: 15 000 ₽"></div>
    <div class="form-group"><label>المسافة من المترو</label>
      <div class="option-row">
        <div class="option-pill" data-mv="near">🚇 قريب</div>
        <div class="option-pill" data-mv="far">🚌 بعيد</div>
      </div>
    </div>
    <div class="form-group"><label>تفاصيل إضافية</label><textarea id="f_desc" placeholder="للطلاب، قريبة من الجامعة..."></textarea></div>
    <button class="btn" id="submitBtn">نشر الإعلان</button>`;
  let type = null, roomType = null, metro = null;
  const photos = [null, null];
  const slotsEl = document.getElementById("photoSlots");
  slotsEl.appendChild(photoSlot(fid => { photos[0] = fid; }));
  slotsEl.appendChild(photoSlot(fid => { photos[1] = fid; }));
  elApp.querySelectorAll("[data-v]").forEach(p => p.onclick = () => {
    type = p.dataset.v;
    elApp.querySelectorAll("[data-v]").forEach(x => x.classList.remove("selected"));
    p.classList.add("selected");
  });
  elApp.querySelectorAll("[data-rv]").forEach(p => p.onclick = () => {
    roomType = p.dataset.rv;
    elApp.querySelectorAll("[data-rv]").forEach(x => x.classList.remove("selected"));
    p.classList.add("selected");
  });
  elApp.querySelectorAll("[data-mv]").forEach(p => p.onclick = () => {
    metro = p.dataset.mv;
    elApp.querySelectorAll("[data-mv]").forEach(x => x.classList.remove("selected"));
    p.classList.add("selected");
  });
  document.getElementById("submitBtn").onclick = async () => {
    const city = document.getElementById("f_city").value.trim();
    const price = document.getElementById("f_price").value.trim();
    const desc = document.getElementById("f_desc").value.trim();
    if (!type || !roomType || !metro || !city || !price || !desc) { toast("⚠️ يرجى تعبئة جميع الحقول"); return; }
    try {
      await api("/api/submit/listing", { method: "POST", body: JSON.stringify({
        type, room_type: roomType, city_key: "other", city, price, metro_distance: metro, description: desc,
        photos: photos.filter(Boolean),
      })});
      successPulse();
      toast("✅ تم استلام إعلانك، بانتظار المراجعة");
      back();
    } catch (e) { toast("⚠️ " + e.message); }
  };
}

// ══════════════════════════════════════════════════════════════════════════
// TRAVEL COMPANION
// ══════════════════════════════════════════════════════════════════════════

async function viewTravel() {
  elApp.innerHTML = `
    <div id="trvGrid" class="trip-list"></div>
    <div id="trvEmpty" class="empty hidden">${emptyIllus()}لا توجد رحلات بعد</div>
    <button class="fab" id="trvPostBtn" aria-label="أضف رحلتك"><svg class="icon-svg"><use href="#i-plus"/></svg></button>`;
  loadTravelGrid();
  document.getElementById("trvPostBtn").onclick = () => go("travelPost", {}, "أضف رحلتك");
}

function showTripSkeleton(list, count = 4) {
  list.innerHTML = "";
  for (let i = 0; i < count; i++) {
    const sk = document.createElement("div");
    sk.className = "trip-card";
    sk.innerHTML = `
      <div class="trip-route">
        <div class="trip-city"><span class="skel-line" style="width:34px;height:34px;border-radius:50%;margin:0"></span><span class="skel-line short" style="margin:8px 0 0"></span></div>
        <div class="trip-path"></div>
        <div class="trip-city"><span class="skel-line" style="width:34px;height:34px;border-radius:50%;margin:0"></span><span class="skel-line short" style="margin:8px 0 0"></span></div>
      </div>
      <div class="trip-stub"><span class="skel-line short"></span></div>`;
    list.appendChild(sk);
  }
}

const ROUTE_ENDS = {
  alg_to_msk: { from: ["DZ", "الجزائر", "t-green"], to: ["RU", "روسيا", "t-blue"] },
  msk_to_alg: { from: ["RU", "روسيا", "t-blue"],   to: ["DZ", "الجزائر", "t-green"] },
};

async function loadTravelGrid() {
  const list = document.getElementById("trvGrid");
  const empty = document.getElementById("trvEmpty");
  showTripSkeleton(list);
  empty.classList.add("hidden");
  const posts = await api("/api/travel");
  list.innerHTML = "";
  empty.classList.toggle("hidden", posts.length > 0);
  if (!posts.length) empty.innerHTML = `${emptyIllus()}لا توجد رحلات بعد`;
  for (const [idx, p] of posts.entries()) {
    const card = document.createElement("div");
    card.className = "trip-card";
    card.style.setProperty("--i", idx % 10);
    const ends = ROUTE_ENDS[p.route] || { from: ["—", "—", "t-slate"], to: ["—", "—", "t-slate"] };
    card.innerHTML = `
      <div class="trip-route">
        <div class="trip-city"><span class="trip-dir">من</span><span class="flag ${ends.from[2]}">${ends.from[0]}</span><span class="code">${esc(ends.from[1])}</span></div>
        <div class="trip-path"><svg class="icon-svg"><use href="#i-plane"/></svg></div>
        <div class="trip-city"><span class="trip-dir">إلى</span><span class="flag ${ends.to[2]}">${ends.to[0]}</span><span class="code">${esc(ends.to[1])}</span></div>
      </div>
      <div class="trip-stub">
        <span class="trip-notch start"></span><span class="trip-notch end"></span>
        <div class="trip-date">📅 ${esc(p.date)}</div>
        <div class="trip-info">📍 ${esc(p.city)}</div>
        <div class="trip-info">👤 ${p.username ? `@${esc(p.username)}` : esc(p.first_name || "—")}${verifiedBadge(p)}</div>
        ${expiryTag(p)}
      </div>`;
    card.onclick = () => openTravelDetail(p.id);
    list.appendChild(card);
  }
}

async function openTravelDetail(id) {
  const p = await api(`/api/travel/${id}`);
  showDetail(`
    <h2>${esc(META.routes[p.route] || p.route)}</h2>
    <div class="detail-row"><b>التاريخ:</b> ${esc(p.date)}</div>
    <div class="detail-row"><b>الطيران:</b> ${esc(p.flight)}</div>
    <div class="detail-row"><b>التفاصيل:</b> ${esc(p.city)}</div>
    <div class="detail-row"><b>التواصل:</b> ${esc(p.contact)}${verifiedBadge(p)}</div>
    <div class="detail-row"><b>ملاحظة:</b> ${esc(p.note)}</div>`);
}

function viewTravelPost() {
  elApp.innerHTML = `
    <div class="form-group"><label>الاتجاه</label>
      <div class="option-row">
        <div class="option-pill" data-r="alg_to_msk">🇩🇿 ➡️ 🇷🇺  الجزائر إلى روسيا</div>
        <div class="option-pill" data-r="msk_to_alg">🇷🇺 ➡️ 🇩🇿  روسيا إلى الجزائر</div>
      </div>
    </div>
    <div class="form-group"><label>تاريخ السفر</label><input type="date" id="f_date"></div>
    <div class="form-group"><label>معلومات الطيران (اختياري)</label><input id="f_flight" placeholder="مثال: Aeroflot SU1234"></div>
    <div class="form-group"><label>تفاصيل المغادرة/الوصول</label><input id="f_city" placeholder="مثال: مطار الجزائر — شيريميتيفو"></div>
    <div class="form-group"><label>وسيلة التواصل</label><input id="f_contact" placeholder="مثال: @username"></div>
    <div class="form-group"><label>ملاحظة</label><textarea id="f_note" placeholder="اختياري"></textarea></div>
    <button class="btn" id="submitBtn">نشر الرحلة</button>`;
  let route = null;
  elApp.querySelectorAll("[data-r]").forEach(p => p.onclick = () => {
    route = p.dataset.r;
    elApp.querySelectorAll("[data-r]").forEach(x => x.classList.remove("selected"));
    p.classList.add("selected");
  });
  document.getElementById("submitBtn").onclick = async () => {
    const date = document.getElementById("f_date").value.trim();
    const flight = document.getElementById("f_flight").value.trim() || "—";
    const city = document.getElementById("f_city").value.trim();
    const contact = document.getElementById("f_contact").value.trim();
    const note = document.getElementById("f_note").value.trim() || "—";
    if (!route || !date || !city || !contact) { toast("⚠️ يرجى تعبئة الحقول المطلوبة"); return; }
    try {
      await api("/api/submit/travel", { method: "POST", body: JSON.stringify({ route, date, flight, city, contact, note }) });
      successPulse();
      toast("✅ تم استلام رحلتك، بانتظار المراجعة");
      back();
    } catch (e) { toast("⚠️ " + e.message); }
  };
}

// ══════════════════════════════════════════════════════════════════════════
// INQUIRY FORM
// ══════════════════════════════════════════════════════════════════════════

function viewInquiry() {
  elApp.innerHTML = `
    <div class="form-group"><label>إلى من تريد توجيه استفسارك؟</label>
      <div class="option-row">
        <div class="option-pill" data-t="admin">👨‍💼 الإدارة</div>
        <div class="option-pill" data-t="community">👥 الجالية</div>
      </div>
    </div>
    <div class="form-group"><label>الاسم الكامل</label><input id="f_name"></div>
    <div class="form-group"><label>رقم الهاتف</label><input id="f_phone" class="ltr-field" dir="ltr" type="tel" placeholder="+213... أو +7..."></div>
    <div class="form-group"><label>الخدمة المطلوبة</label>
      <div class="option-row">
        <div class="option-pill" data-s="🎓 تسجيل جامعي">🎓 تسجيل جامعي</div>
        <div class="option-pill" data-s="📑 ترجمة وثائق">📑 ترجمة وثائق</div>
        <div class="option-pill" data-s="🗣️ استشارة عامة">🗣️ استشارة عامة</div>
        <div class="option-pill" data-s="❓ أخرى">❓ أخرى</div>
      </div>
    </div>
    <div class="form-group"><label>ملاحظات إضافية</label><textarea id="f_notes"></textarea></div>
    <button class="btn" id="submitBtn">إرسال الاستفسار</button>`;
  let target = "admin", service = null;
  elApp.querySelectorAll("[data-t]").forEach(p => p.onclick = () => {
    target = p.dataset.t;
    elApp.querySelectorAll("[data-t]").forEach(x => x.classList.remove("selected"));
    p.classList.add("selected");
  });
  elApp.querySelectorAll("[data-s]").forEach(p => p.onclick = () => {
    service = p.dataset.s;
    elApp.querySelectorAll("[data-s]").forEach(x => x.classList.remove("selected"));
    p.classList.add("selected");
  });
  document.getElementById("submitBtn").onclick = async () => {
    const name = document.getElementById("f_name").value.trim();
    const phone = document.getElementById("f_phone").value.trim();
    const notes = document.getElementById("f_notes").value.trim() || "—";
    if (!name || !phone || !service) { toast("⚠️ يرجى تعبئة جميع الحقول"); return; }
    try {
      await api("/api/submit/inquiry", { method: "POST", body: JSON.stringify({ name, phone, service, notes, target }) });
      successPulse();
      toast("✅ تم استلام استفسارك");
      back();
    } catch (e) { toast("⚠️ " + e.message); }
  };
}

// ══════════════════════════════════════════════════════════════════════════
// شرلوك الجزائري — SCAM CHECK & REPORT
// ══════════════════════════════════════════════════════════════════════════

const SCAM_FIELDS = [
  ["full_name", "الاسم الكامل", "مثال: أحمد", true],
  ["phone", "رقم الهاتف", "", true],
  ["ccp", "رقم CCP", "", true],
  ["surname", "اللقب", "مثال: بن علي", false],
  ["full_name_ru", "الاسم بالروسية", "مثال: Ахмед", false],
  ["date_of_birth", "تاريخ الميلاد", "", false],
  ["telegram_user_id", "معرّف تيليجرام (ID)", "مثال: 123456789", false],
  ["cle_rip", "المفتاح / RIP", "", false],
  ["card", "رقم البطاقة البنكية", "", false],
  ["passport", "رقم جواز السفر", "", false],
];

function normalizePhone(country, raw) {
  let digits = (raw || "").replace(/\D/g, "");
  if (country === "dz") {
    if (digits.startsWith("213")) digits = digits.slice(3);
    else if (digits.startsWith("0")) digits = digits.slice(1);
    return "+213" + digits;
  }
  if (digits.startsWith("8") && digits.length === 11) digits = digits.slice(1);
  else if (digits.startsWith("7")) digits = digits.slice(1);
  return "+7" + digits;
}

function phoneFieldHtml(idPrefix) {
  return `<div class="form-group">
    <label>رقم الهاتف</label>
    <div class="phone-country" id="${idPrefix}_phone_country" data-value="">
      <button type="button" class="option-pill" data-c="dz">🇩🇿 جزائري (يبدأ بـ 0)</button>
      <button type="button" class="option-pill" data-c="ru">🇷🇺 روسي</button>
    </div>
    <input id="${idPrefix}_phone" class="ltr-field" dir="ltr" placeholder="اختر الدولة أولًا">
  </div>`;
}

function scamFieldHtml(idPrefix, [key, label, placeholder]) {
  if (key === "phone") return phoneFieldHtml(idPrefix);
  const type = key === "date_of_birth" ? "date" : "text";
  const ltr = ["telegram_user_id", "ccp", "cle_rip", "card", "passport"].includes(key) ? ' class="ltr-field" dir="ltr"' : "";
  return `<div class="form-group"><label>${label}</label><input id="${idPrefix}_${key}" type="${type}"${ltr} placeholder="${placeholder}"></div>`;
}

function scamFieldsHtml(idPrefix) {
  const primary = SCAM_FIELDS.filter(f => f[3]).map(f => scamFieldHtml(idPrefix, f)).join("");
  const secondary = SCAM_FIELDS.filter(f => !f[3]).map(f => scamFieldHtml(idPrefix, f)).join("");
  return `${primary}
    <details class="scam-more">
      <summary>بيانات إضافية (اختياري)</summary>
      ${secondary}
    </details>`;
}

function wireScamPhoneToggle(idPrefix) {
  const wrap = document.getElementById(`${idPrefix}_phone_country`);
  wrap.querySelectorAll(".option-pill").forEach(btn => {
    btn.onclick = () => {
      wrap.dataset.value = btn.dataset.c;
      wrap.querySelectorAll(".option-pill").forEach(b => b.classList.toggle("selected", b === btn));
      document.getElementById(`${idPrefix}_phone`).placeholder = btn.dataset.c === "dz" ? "مثال: 0555123456" : "مثال: 9161234567";
    };
  });
}

function readScamFields(idPrefix) {
  const out = {};
  for (const [key] of SCAM_FIELDS) out[key] = document.getElementById(`${idPrefix}_${key}`).value.trim();
  const country = document.getElementById(`${idPrefix}_phone_country`).dataset.value;
  if (out.phone) out.phone = country ? normalizePhone(country, out.phone) : out.phone;
  return out;
}

function viewScamCheck() {
  elApp.innerHTML = `
    <div class="hero" style="background:var(--danger)">
      <div class="title">🕵️ شرلوك الجزائري</div>
      <div class="subtitle">تحقق من معلومات الشخص قبل ما تحول له فلوسك، أو بلّغ عن نصاب.</div>
    </div>
    <a class="guarantor-box" href="https://t.me/Yousfi_Abdelkader" target="_blank" rel="noopener">
      <span class="row-icon t-teal"><svg class="icon-svg"><use href="#i-shield"/></svg></span>
      <span class="feature-text"><span class="label">🛡️ ضامن موثوق</span><span class="feature-count">لتفادي أي خطر، تواصل معي شخصيًا لإتمام التحويل بأمان</span></span>
      <span class="chevron">‹</span>
    </a>
    <button class="btn" id="scamGoQuickBtn">🔍 بحث سريع</button>
    <button class="btn secondary" id="scamGoFullBtn">🕵️ بحث تفصيلي كمحقق</button>
    <button class="btn secondary" id="scamGoReportBtn">🚩 بلّغ عن نصاب</button>`;
  document.getElementById("scamGoQuickBtn").onclick = () => go("scamQuickSearch", {}, "🔍 بحث سريع");
  document.getElementById("scamGoFullBtn").onclick = () => go("scamCheckForm", {}, "🕵️ بحث تفصيلي");
  document.getElementById("scamGoReportBtn").onclick = () => go("scamReport", {}, "بلّغ عن نصاب");
}

function viewScamQuickSearch() {
  elApp.innerHTML = `
    <div class="form-group">
      <label>اكتب أي معلومة تعرفها عن الشخص</label>
      <input id="quickQuery" placeholder="اسم، رقم هاتف، CCP، جواز سفر، معرّف تيليجرام...">
    </div>
    <button class="btn" id="quickSearchBtn">تحقق الآن</button>
    <div id="scamResults"></div>`;
  const input = document.getElementById("quickQuery");
  const run = async () => {
    const q = input.value.trim();
    if (!q) { toast("⚠️ اكتب معلومة واحدة على الأقل للبحث"); return; }
    const results = document.getElementById("scamResults");
    results.innerHTML = `<div class="empty">جارِ البحث...</div>`;
    try {
      const res = await api("/api/scam/search", { method: "POST", body: JSON.stringify({ query: q }) });
      renderScamResults(res);
    } catch (e) { results.innerHTML = ""; toast("⚠️ " + e.message); }
  };
  document.getElementById("quickSearchBtn").onclick = run;
  input.onkeydown = (e) => { if (e.key === "Enter") run(); };
}

function scamPhoneNeedsCountry(idPrefix) {
  const raw = document.getElementById(`${idPrefix}_phone`).value.trim();
  const country = document.getElementById(`${idPrefix}_phone_country`).dataset.value;
  return !!raw && !country;
}

function viewScamCheckForm() {
  elApp.innerHTML = `
    <div class="section-title">🕵️ عبّي كل معلومة تعرفها عن الشخص لتحقق دقيق</div>
    ${scamFieldsHtml("chk")}
    <button class="btn" id="scamCheckBtn">تحقق الآن</button>
    <div id="scamResults"></div>`;
  wireScamPhoneToggle("chk");
  document.getElementById("scamCheckBtn").onclick = async () => {
    if (scamPhoneNeedsCountry("chk")) { toast("⚠️ اختر الدولة (جزائري أو روسي) لرقم الهاتف"); return; }
    const fields = readScamFields("chk");
    if (!Object.values(fields).some(Boolean)) { toast("⚠️ عبّي معلومة واحدة على الأقل"); return; }
    const results = document.getElementById("scamResults");
    results.innerHTML = `<div class="empty">جارِ البحث...</div>`;
    try {
      const res = await api("/api/scam/search", { method: "POST", body: JSON.stringify(fields) });
      renderScamResults(res);
    } catch (e) { results.innerHTML = ""; toast("⚠️ " + e.message); }
  };
}

function renderScamResults(res) {
  const results = document.getElementById("scamResults");
  if (res.mode === "none") {
    results.innerHTML = `<div class="empty">${emptyIllus()}لا توجد بلاغات مطابقة — لكن هذا لا يعني أن الشخص موثوق، ابقَ حذرًا دائمًا</div>`;
    return;
  }
  if (res.mode === "guarantor") {
    const g = res.results[0];
    results.innerHTML = `
      <div class="guarantor-result">
        <span class="row-icon t-green"><svg class="icon-svg"><use href="#i-check"/></svg></span>
        <div class="feature-text">
          <span class="label">✅ هذا شخص ضامن موثوق</span>
          <span class="feature-count">${esc(g.full_name)} — ${esc(g.full_name_ru)}</span>
          <span class="feature-count ltr-field" dir="ltr">${esc(g.phone)}</span>
        </div>
      </div>`;
    return;
  }
  if (res.mode === "candidates") {
    results.innerHTML = `<div class="section-title">نتائج مطابقة للاسم — اختر الشخص الصحيح</div>` +
      res.results.map(c => `
        <div class="list-item" data-id="${c.id}">
          <span class="row-icon t-danger"><svg class="icon-svg"><use href="#i-shield"/></svg></span>
          <span class="title">${esc(c.full_name)} ${esc(c.surname)}${c.date_of_birth ? " — " + esc(c.date_of_birth) : ""}</span>
          <span class="chevron">‹</span>
        </div>`).join("");
    results.querySelectorAll(".list-item").forEach(el => {
      el.onclick = async () => {
        try {
          const detail = await api(`/api/scam/report/${el.dataset.id}`);
          showScamDetail(detail);
        } catch (e) { toast("⚠️ " + e.message); }
      };
    });
    return;
  }
  results.innerHTML = `<div class="section-title">⚠️ تم العثور على ${res.results.length} بلاغ</div>`;
  res.results.forEach(r => {
    const card = document.createElement("div");
    card.className = "list-item";
    card.innerHTML = `
      <span class="row-icon t-danger"><svg class="icon-svg"><use href="#i-shield"/></svg></span>
      <span class="title">${esc(r.full_name)} ${esc(r.surname)}</span>
      <span class="chevron">‹</span>`;
    card.onclick = () => showScamDetail(r);
    results.appendChild(card);
  });
}

function showScamDetail(r) {
  const photosHtml = (r.photos || []).map(p => `<img src="/api/photo/${p}">`).join("");
  const wrap = showDetail(`
    ${photosHtml}
    <h2>⚠️ ${esc(r.full_name)} ${esc(r.surname)}</h2>
    ${r.full_name_ru ? `<div class="detail-row"><b>بالروسية:</b> ${esc(r.full_name_ru)}</div>` : ""}
    <div class="detail-row"><b>تاريخ الميلاد:</b> ${esc(r.date_of_birth || "—")}</div>
    <div class="detail-row"><b>معرّف تيليجرام:</b> ${esc(r.telegram_user_id || "—")}</div>
    <div class="detail-row"><b>الهاتف:</b> ${esc(r.phone || "—")}</div>
    <div class="detail-row"><b>CCP:</b> ${esc(r.ccp || "—")}</div>
    <div class="detail-row"><b>المفتاح/RIP:</b> ${esc(r.cle_rip || "—")}</div>
    <div class="detail-row"><b>البطاقة:</b> ${esc(r.card || "—")}</div>
    <div class="detail-row"><b>جواز السفر:</b> ${esc(r.passport || "—")}</div>
    <div class="detail-row"><b>سبب البلاغ:</b> ${esc(r.reason)}</div>
    <div class="scam-access-box">
      <textarea id="scamAccessReason" placeholder="اختياري: لماذا تريد التفاصيل الكاملة؟"></textarea>
      <button class="btn secondary" id="scamAccessBtn">🔓 طلب رؤية التفاصيل الكاملة</button>
    </div>`);
  wrap.querySelector("#scamAccessBtn").onclick = async () => {
    try {
      await api("/api/scam/request_access", {
        method: "POST",
        body: JSON.stringify({ report_id: r.id, reason: wrap.querySelector("#scamAccessReason").value.trim() }),
      });
      toast("✅ تم إرسال طلبك للإدارة");
      wrap.querySelector("#scamAccessBtn").disabled = true;
    } catch (e) { toast("⚠️ " + e.message); }
  };
}

function viewScamReport() {
  elApp.innerHTML = `
    ${scamFieldsHtml("rep")}
    <div class="form-group"><label>سبب البلاغ (مطلوب)</label><textarea id="rep_reason" placeholder="اشرح ماذا حدث بالتفصيل..."></textarea></div>
    <div class="form-group"><label>صور إثبات (اختياري)</label><div class="photo-slots" id="scamPhotoSlots"></div></div>
    <button class="btn" id="scamReportSubmit">إرسال البلاغ</button>`;
  wireScamPhoneToggle("rep");
  const photos = [];
  const slotsEl = document.getElementById("scamPhotoSlots");
  for (let i = 0; i < 3; i++) slotsEl.appendChild(photoSlot(fid => photos.push(fid)));
  document.getElementById("scamReportSubmit").onclick = async () => {
    if (scamPhoneNeedsCountry("rep")) { toast("⚠️ اختر الدولة (جزائري أو روسي) لرقم الهاتف"); return; }
    const fields = readScamFields("rep");
    const reason = document.getElementById("rep_reason").value.trim();
    if (!Object.values(fields).some(Boolean)) { toast("⚠️ عبّي معلومة واحدة على الأقل عن الشخص"); return; }
    if (!reason) { toast("⚠️ يرجى ذكر سبب البلاغ"); return; }
    try {
      await api("/api/scam/report", { method: "POST", body: JSON.stringify({ ...fields, reason, photos }) });
      successPulse();
      toast("✅ تم استلام بلاغك، بانتظار المراجعة");
      back();
    } catch (e) { toast("⚠️ " + e.message); }
  };
}

// ── Detail sheet helper ─────────────────────────────────────────────────────

function showDetail(html) {
  const wrap = document.createElement("div");
  wrap.className = "detail";
  wrap.innerHTML = `<div class="detail-card"><button class="detail-close"><svg class="icon-svg"><use href="#i-close"/></svg></button><div>${html}</div></div>`;
  wrap.onclick = (e) => { if (e.target === wrap) wrap.remove(); };
  wrap.querySelector(".detail-close").onclick = () => wrap.remove();
  wrap.querySelectorAll(".detail-card img").forEach(img => {
    img.style.cursor = "zoom-in";
    img.onclick = (e) => { e.stopPropagation(); openFullscreenImage(img.src); };
  });
  document.body.appendChild(wrap);
  return wrap;
}

function openFullscreenImage(src) {
  const ov = document.createElement("div");
  ov.className = "img-fullscreen";
  ov.innerHTML = `<button class="img-fullscreen-close"><svg class="icon-svg"><use href="#i-close"/></svg></button><img src="${src}">`;
  ov.onclick = () => ov.remove();
  document.body.appendChild(ov);
}

// ── View registry ─────────────────────────────────────────────────────────

const VIEWS = {
  home: viewHome,
  more: viewMore,
  contentCategory: viewContentCategory,
  contentPage: viewContentPage,
  avito: viewAvito,
  avitoPost: viewAvitoPost,
  roommate: viewRoommate,
  roommatePost: viewRoommatePost,
  travel: viewTravel,
  travelPost: viewTravelPost,
  inquiry: viewInquiry,
  scamCheck: viewScamCheck,
  scamQuickSearch: viewScamQuickSearch,
  scamCheckForm: viewScamCheckForm,
  scamReport: viewScamReport,
};

(async () => {
  await loadMeta();
  go("home", {}, "");
  setActiveNav("home");
})();
