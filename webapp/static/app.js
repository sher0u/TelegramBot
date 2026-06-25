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

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 2500);
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
    if (tab === "home") resetTab("home", "home", {}, "KaderDzbot");
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

async function viewHome() {
  let heroTitle = "مرحبًا بك في KADER DZ 🇷🇺";
  let heroSubtitle = "مساعدك الشامل للدراسة والحياة في روسيا — تصفح، انشر، وتواصل مع المجتمع كله من هنا.";
  try {
    const { text } = await api("/api/home_banner");
    if (text) { heroTitle = "📢 إعلان من الإدارة"; heroSubtitle = text; }
  } catch (e) { /* ignore, fall back to default welcome */ }

  elApp.innerHTML = `
    <div class="hero">
      <div class="title">${esc(heroTitle)}</div>
      <div class="subtitle">${esc(heroSubtitle)}</div>
    </div>
    <div class="home-grid">
      <button class="home-tile" data-go="content" data-id="guide"><span class="icon-circle">📘</span><span class="label">دليلك الشامل</span></button>
      <button class="home-tile" data-go="content" data-id="consular"><span class="icon-circle">🏛️</span><span class="label">الخدمات القنصلية</span></button>
      <button class="home-tile" data-go="content" data-id="services"><span class="icon-circle">⚙️</span><span class="label">الخدمات</span></button>
      <button class="home-tile" data-go="avito"><span class="icon-circle">🛒</span><span class="label">Avito Algeria</span></button>
      <button class="home-tile" data-go="roommate"><span class="icon-circle">🏠</span><span class="label">شريك سكن</span></button>
      <button class="home-tile" data-go="travel"><span class="icon-circle">🧳</span><span class="label">هبطلي ولا طلعلي معاك</span></button>
      <button class="home-tile" data-go="inquiry"><span class="icon-circle">📝</span><span class="label">تقديم استفسار</span></button>
      <button class="home-tile" data-go="content" data-id="about"><span class="icon-circle">ℹ️</span><span class="label">عن البوت</span></button>
    </div>`;
  elApp.querySelectorAll(".home-tile").forEach(btn => {
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
    <div class="list-item" data-go="content" data-id="guide"><span class="title">📘 دليلك الشامل</span><span class="chevron">‹</span></div>
    <div class="list-item" data-go="content" data-id="consular"><span class="title">🏛️ الخدمات القنصلية</span><span class="chevron">‹</span></div>
    <div class="list-item" data-go="content" data-id="services"><span class="title">⚙️ الخدمات</span><span class="chevron">‹</span></div>
    <div class="list-item" data-go="inquiry"><span class="title">📝 تقديم استفسار</span><span class="chevron">‹</span></div>
    <div class="list-item" data-go="content" data-id="about"><span class="title">ℹ️ عن البوت</span><span class="chevron">‹</span></div>`;
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
    <div class="search-bar"><span class="icon">🔍</span><input id="avitoSearch" placeholder="بحث عن منتج، مدينة..."></div>
    <div class="segmented" id="avitoSort">
      <div class="seg" data-v="">🔄 الأحدث</div>
      <div class="seg" data-v="asc">💰 الأرخص أولًا</div>
      <div class="seg" data-v="desc">💎 الأغلى أولًا</div>
    </div>
    <div id="avitoFilters" class="filters"></div>
    <div id="avitoGrid" class="grid"></div>
    <div id="avitoEmpty" class="empty hidden">😔 لا توجد إعلانات بهذه المعايير</div>
    <button class="btn fab" id="avitoPostBtn">➕ نشر إعلان مجانًا</button>`;
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

async function loadAvitoGrid() {
  const grid = document.getElementById("avitoGrid");
  const empty = document.getElementById("avitoEmpty");
  showSkeleton(grid);
  empty.classList.add("hidden");
  const qs = new URLSearchParams({ category: avitoState.category, q: avitoState.q, sort: avitoState.sort });
  const items = await api(`/api/items?${qs}`);
  grid.innerHTML = "";
  empty.classList.toggle("hidden", items.length > 0);
  if (!items.length) empty.innerHTML = `<span class="emoji">😔</span>لا توجد إعلانات بهذه المعايير`;
  for (const item of items) {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="img-wrap">
        ${item.photo_id ? `<img src="/api/photo/${item.photo_id}" onerror="this.parentElement.innerHTML='<span class=placeholder-icon>📦</span>'">` : `<span class="placeholder-icon">📦</span>`}
        <span class="cat-badge">${catEmoji(item.category)}</span>
        <span class="price-badge">${esc(item.price)}</span>
      </div>
      <div class="body">
        <div class="title">${esc(item.title)}</div>
        <div class="meta">📍 ${esc(item.city)}</div>
      </div>`;
    card.onclick = () => openAvitoDetail(item.id);
    grid.appendChild(card);
  }
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
    <div class="detail-row"><b>البائع:</b> ${seller}</div>
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
    <div class="form-group"><label>السعر</label><input id="f_price" placeholder="مثال: 50 000 DZD"></div>
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
    <div class="search-bar"><span class="icon">🔍</span><input id="rmSearch" placeholder="بحث عن مدينة، تفاصيل..."></div>
    <div class="segmented" id="rmSort">
      <div class="seg" data-v="">🔄 الأحدث</div>
      <div class="seg" data-v="asc">💰 الأرخص أولًا</div>
      <div class="seg" data-v="desc">💎 الأغلى أولًا</div>
    </div>
    <div id="rmFilters" class="filters"></div>
    <div id="rmGrid" class="grid"></div>
    <div id="rmEmpty" class="empty hidden">😔 لا توجد إعلانات بعد</div>
    <button class="btn fab" id="rmPostBtn">➕ نشر إعلان سكن</button>`;
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
  if (!items.length) empty.innerHTML = `<span class="emoji">😔</span>لا توجد إعلانات بهذه المعايير`;
  for (const item of items) {
    const card = document.createElement("div");
    card.className = "card";
    const rtype = item.type === "need" ? "🔍 يبحث" : "🏠 عنده غرفة";
    const roomBadge = item.room_type === "studio" ? "🏠" : "🛏️";
    const photo = (item.photos || [])[0];
    card.innerHTML = `
      <div class="img-wrap">
        ${photo ? `<img src="/api/photo/${photo}" onerror="this.parentElement.innerHTML='<span class=placeholder-icon>🏠</span>'">` : `<span class="placeholder-icon">🏠</span>`}
        <span class="cat-badge">${roomBadge}</span>
        <span class="price-badge">${esc(item.price)}</span>
      </div>
      <div class="body">
        <div class="title">${rtype} — ${esc(item.city)}</div>
        <div class="meta">🚇 ${item.metro_distance === "near" ? "قريب من المترو" : "بعيد عن المترو"}</div>
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
    <div class="detail-row"><b>المُعلن:</b> ${poster}</div>
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
    <div class="form-group"><label>السعر الشهري</label><input id="f_price" placeholder="مثال: 15 000 ₽"></div>
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
    <div id="trvGrid" class="grid"></div>
    <div id="trvEmpty" class="empty hidden">😔 لا توجد رحلات بعد</div>
    <button class="btn fab" id="trvPostBtn">➕ أضف رحلتك</button>`;
  loadTravelGrid();
  document.getElementById("trvPostBtn").onclick = () => go("travelPost", {}, "أضف رحلتك");
}

async function loadTravelGrid() {
  const grid = document.getElementById("trvGrid");
  const empty = document.getElementById("trvEmpty");
  showSkeleton(grid);
  empty.classList.add("hidden");
  const posts = await api("/api/travel");
  grid.innerHTML = "";
  empty.classList.toggle("hidden", posts.length > 0);
  if (!posts.length) empty.innerHTML = `<span class="emoji">😔</span>لا توجد رحلات بعد`;
  const ROUTE_SHORT = { alg_to_msk: "الجزائر ⟸ روسيا", msk_to_alg: "روسيا ⟸ الجزائر" };
  for (const p of posts) {
    const card = document.createElement("div");
    card.className = "card";
    const dirEmoji = p.route === "alg_to_msk" ? "🇩🇿 ➡️ 🇷🇺" : "🇷🇺 ➡️ 🇩🇿";
    card.innerHTML = `
      <div class="img-wrap">
        <span class="placeholder-icon">🧳</span>
        <span class="cat-badge" style="width:auto; padding:3px 8px; font-size:12px;">${dirEmoji}</span>
        <span class="price-badge">📅 ${esc(p.date)}</span>
      </div>
      <div class="body">
        <div class="title">${ROUTE_SHORT[p.route] || esc(p.route)}</div>
        <div class="meta">📍 ${esc(p.city)}</div>
      </div>`;
    card.onclick = () => openTravelDetail(p.id);
    grid.appendChild(card);
  }
}

async function openTravelDetail(id) {
  const p = await api(`/api/travel/${id}`);
  showDetail(`
    <h2>${esc(META.routes[p.route] || p.route)}</h2>
    <div class="detail-row"><b>التاريخ:</b> ${esc(p.date)}</div>
    <div class="detail-row"><b>الطيران:</b> ${esc(p.flight)}</div>
    <div class="detail-row"><b>التفاصيل:</b> ${esc(p.city)}</div>
    <div class="detail-row"><b>التواصل:</b> ${esc(p.contact)}</div>
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
    <div class="form-group"><label>رقم الهاتف</label><input id="f_phone" placeholder="+213... أو +7..."></div>
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
      toast("✅ تم استلام استفسارك");
      back();
    } catch (e) { toast("⚠️ " + e.message); }
  };
}

// ── Detail sheet helper ─────────────────────────────────────────────────────

function showDetail(html) {
  const wrap = document.createElement("div");
  wrap.className = "detail";
  wrap.innerHTML = `<div class="detail-card"><button class="detail-close">✕</button><div>${html}</div></div>`;
  wrap.onclick = (e) => { if (e.target === wrap) wrap.remove(); };
  wrap.querySelector(".detail-close").onclick = () => wrap.remove();
  wrap.querySelectorAll(".detail-card img").forEach(img => {
    img.style.cursor = "zoom-in";
    img.onclick = (e) => { e.stopPropagation(); openFullscreenImage(img.src); };
  });
  document.body.appendChild(wrap);
}

function openFullscreenImage(src) {
  const ov = document.createElement("div");
  ov.className = "img-fullscreen";
  ov.innerHTML = `<button class="img-fullscreen-close">✕</button><img src="${src}">`;
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
};

(async () => {
  await loadMeta();
  go("home", {}, "KaderDzbot");
  setActiveNav("home");
})();
