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

function ltr(value) {
  const v = esc(value || "—");
  return v === "—" ? v : `<span class="ltr-field" dir="ltr">${v}</span>`;
}

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 2500);
}

const stack = [];
const elApp = document.getElementById("app");
const elBack = document.getElementById("backBtn");
const elTitle = document.getElementById("topTitle");

function go(view, params = {}, title = "👨‍💼 لوحة التحكم") {
  stack.push({ view, params, title });
  render();
}
function back() { if (stack.length > 1) { stack.pop(); render(); } }
elBack.onclick = back;

function render() {
  const top = stack[stack.length - 1];
  elBack.classList.toggle("hidden", stack.length <= 1);
  elTitle.textContent = top.title;
  elApp.classList.remove("view-anim");
  elApp.innerHTML = "";
  VIEWS[top.view](top.params);
  void elApp.offsetWidth;
  elApp.classList.add("view-anim");
}

// ══════════════════════════════════════════════════════════════════════════
// DASHBOARD
// ══════════════════════════════════════════════════════════════════════════

async function viewDashboard() {
  elApp.innerHTML = `<div id="stats"></div>
    <div class="section-title">الإجراءات</div>
    <div class="list-item" id="pendingBtn"><span class="title">📋 الطلبات المعلقة</span><span class="chevron">‹</span></div>
    <div class="list-item" id="scamManageBtn"><span class="title">🕵️ إدارة بلاغات شرلوك الجزائري</span><span class="chevron">‹</span></div>
    <div class="list-item" id="broadcastBtn"><span class="title">📤 بث رسالة</span><span class="chevron">‹</span></div>
    <div class="list-item" id="usersBtn"><span class="title">☑️ توثيق المستخدمين</span><span class="chevron">‹</span></div>`;
  document.getElementById("pendingBtn").onclick = () => go("pending", {}, "📋 الطلبات المعلقة");
  document.getElementById("scamManageBtn").onclick = () => go("scamManage", {}, "🕵️ إدارة بلاغات شرلوك الجزائري");
  document.getElementById("broadcastBtn").onclick = () => go("broadcast", {}, "📤 بث رسالة");
  document.getElementById("usersBtn").onclick = () => go("users", {}, "☑️ توثيق المستخدمين");
  try {
    const s = await api("/api/admin/stats");
    document.getElementById("stats").innerHTML = `
      <div class="stat-grid">
        <div class="stat-box"><div class="num">${s.total}</div><div class="lbl">إجمالي المستخدمين</div></div>
        <div class="stat-box"><div class="num">${s.new_today}</div><div class="lbl">جدد اليوم</div></div>
        <div class="stat-box"><div class="num">${s.pending_items + s.pending_listings + s.pending_travel + s.pending_inquiries + s.pending_scam_reports}</div><div class="lbl">طلبات معلقة</div></div>
        <div class="stat-box"><div class="num">${s.approved_items + s.approved_listings + s.approved_travel}</div><div class="lbl">إعلانات منشورة</div></div>
      </div>`;
  } catch (e) {
    elApp.innerHTML = `<div class="empty">🚫 غير مصرّح لك بالوصول لهذه اللوحة</div>`;
  }
}

// ══════════════════════════════════════════════════════════════════════════
// PENDING APPROVALS
// ══════════════════════════════════════════════════════════════════════════

const KIND_LABELS = { items: "🛒 إعلان سوق", listings: "🏠 إعلان سكن", travel: "🧳 رحلة", inquiries: "👥 استفسار جالية", scam_reports: "🕵️ بلاغ شرلوك الجزائري", scam_access_requests: "🔓 طلب اطلاع كامل" };
const KIND_SINGULAR = { items: "item", listings: "listing", travel: "travel", inquiries: "inquiry", scam_reports: "scam", scam_access_requests: "scam_access" };
const NO_PUBLISH_KINDS = new Set(["scam_reports", "scam_access_requests"]);

async function viewPending() {
  elApp.innerHTML = `<div id="pendingList"></div>`;
  const data = await api("/api/admin/pending");
  const list = document.getElementById("pendingList");
  let any = false;
  for (const [kind, arr] of Object.entries(data)) {
    if (!arr.length) continue;
    any = true;
    list.innerHTML += `<div class="section-title">${KIND_LABELS[kind]} (${arr.length})</div>`;
    for (const it of arr) {
      const card = document.createElement("div");
      card.className = "pending-card";
      card.innerHTML = pendingCardBody(kind, it);
      list.appendChild(card);
      const publishBtn = card.querySelector(".approve-publish");
      if (publishBtn) publishBtn.onclick = () => act("approve", KIND_SINGULAR[kind], it.id, card, true);
      card.querySelector(".approve-only").onclick = () => act("approve", KIND_SINGULAR[kind], it.id, card, false);
      card.querySelector(".reject").onclick = () => act("reject", KIND_SINGULAR[kind], it.id, card);
    }
  }
  if (!any) list.innerHTML = `<div class="empty">✅ لا توجد طلبات معلقة</div>`;
}

function pendingCardBody(kind, it) {
  let lines = "";
  if (kind === "items") {
    lines = `<div class="meta-line"><b>العنوان:</b> ${esc(it.title)}</div>
      <div class="meta-line"><b>السعر:</b> ${esc(it.price)} — <b>المدينة:</b> ${esc(it.city)}</div>
      <div class="meta-line"><b>الوصف:</b> ${esc(it.description)}</div>`;
  } else if (kind === "listings") {
    lines = `<div class="meta-line"><b>النوع:</b> ${it.type === "need" ? "يبحث" : "عنده غرفة"}</div>
      <div class="meta-line"><b>المدينة:</b> ${esc(it.city)} — <b>السعر:</b> ${esc(it.price)}</div>
      <div class="meta-line"><b>التفاصيل:</b> ${esc(it.description)}</div>`;
  } else if (kind === "travel") {
    lines = `<div class="meta-line"><b>الاتجاه:</b> ${esc(it.route)}</div>
      <div class="meta-line"><b>التاريخ:</b> ${esc(it.date)} — <b>التفاصيل:</b> ${esc(it.city)}</div>
      <div class="meta-line"><b>التواصل:</b> ${esc(it.contact)}</div>`;
  } else if (kind === "inquiries") {
    lines = `<div class="meta-line"><b>الاسم:</b> ${esc(it.name)} — <b>الهاتف:</b> ${esc(it.phone)}</div>
      <div class="meta-line"><b>الخدمة:</b> ${esc(it.service)}</div>
      <div class="meta-line"><b>ملاحظات:</b> ${esc(it.notes)}</div>`;
  } else if (kind === "scam_reports") {
    lines = `<div class="meta-line"><b>الاسم:</b> ${esc(it.full_name)} ${esc(it.surname)}</div>
      <div class="meta-line"><b>بالروسية:</b> ${esc(it.full_name_ru || "—")}</div>
      <div class="meta-line"><b>الهاتف:</b> ${ltr(it.phone)} — <b>CCP:</b> ${ltr(it.ccp)} — <b>المفتاح:</b> ${ltr(it.cle_rip)}</div>
      <div class="meta-line"><b>البطاقة:</b> ${ltr(it.card)} — <b>الجواز:</b> ${ltr(it.passport)}</div>
      <div class="meta-line"><b>Telegram ID:</b> ${ltr(it.telegram_user_id)} — <b>الميلاد:</b> ${esc(it.date_of_birth || "—")}</div>
      <div class="meta-line"><b>السبب:</b> ${esc(it.reason)}</div>`;
  } else if (kind === "scam_access_requests") {
    lines = `<div class="meta-line"><b>report_id:</b> ${esc(it.report_id)}</div>
      <div class="meta-line"><b>السبب:</b> ${esc(it.reason || "—")}</div>`;
  }
  const poster = kind === "scam_access_requests"
    ? (it.requester_username ? `@${esc(it.requester_username)}` : esc(it.requester_user_id))
    : (it.username ? `@${esc(it.username)}` : esc(it.first_name || "—"));
  const publishBtn = NO_PUBLISH_KINDS.has(kind) ? "" :
    `<button class="btn approve-publish" style="background:var(--success)">✅ قبول ونشر في المجموعات</button>`;
  return `${lines}<div class="meta-line"><b>${kind === "scam_access_requests" ? "الطالب" : "المرسل"}:</b> ${poster}</div>
    ${publishBtn}
    <div class="btn-row">
      <button class="btn approve-only secondary">✅ ${NO_PUBLISH_KINDS.has(kind) ? "موافقة" : "قبول فقط"}</button>
      <button class="btn reject danger">❌ رفض</button>
    </div>`;
}

async function act(action, kind, id, card, publish) {
  try {
    const body = action === "approve" ? { kind, id, publish } : { kind, id };
    await api(`/api/admin/${action}`, { method: "POST", body: JSON.stringify(body) });
    toast(action === "approve" ? "✅ تمت الموافقة" : "❌ تم الرفض");
    card.remove();
  } catch (e) { toast("⚠️ " + e.message); }
}

// ══════════════════════════════════════════════════════════════════════════
// SCAM REPORTS MANAGEMENT (approved records — edit / delete)
// ══════════════════════════════════════════════════════════════════════════

const SCAM_EDIT_FIELDS = [
  ["full_name", "الاسم الكامل"], ["surname", "اللقب"], ["full_name_ru", "الاسم بالروسية"],
  ["date_of_birth", "تاريخ الميلاد"], ["telegram_user_id", "معرّف تيليجرام"], ["phone", "الهاتف"],
  ["ccp", "CCP"], ["cle_rip", "المفتاح / RIP"], ["card", "البطاقة"], ["passport", "جواز السفر"],
];

async function viewScamManage() {
  elApp.innerHTML = `
    <button class="btn" id="scamAddBtn">➕ إضافة نصاب جديد</button>
    <div class="scam-edit-form hidden" id="scamAddForm"></div>
    <div class="section-title">البلاغات المنشورة</div>
    <div id="scamManageList"></div>`;
  const addBtn = document.getElementById("scamAddBtn");
  const addForm = document.getElementById("scamAddForm");
  addBtn.onclick = () => {
    const opening = addForm.classList.contains("hidden");
    addForm.classList.toggle("hidden", !opening);
    addBtn.textContent = opening ? "✖️ إغلاق" : "➕ إضافة نصاب جديد";
    if (opening && !addForm.dataset.built) {
      addForm.innerHTML = scamEditFormHtml({});
      addForm.dataset.built = "1";
      addForm.querySelector(".cancel-scam").onclick = () => { addForm.classList.add("hidden"); addBtn.textContent = "➕ إضافة نصاب جديد"; };
      addForm.querySelector(".save-scam").textContent = "➕ إضافة ونشر";
      addForm.querySelector(".save-scam").onclick = async () => {
        const body = {};
        addForm.querySelectorAll("[data-key]").forEach(el => body[el.dataset.key] = el.value.trim());
        if (!body.full_name) { toast("⚠️ الاسم الكامل مطلوب"); return; }
        try {
          await api("/api/admin/scam/add", { method: "POST", body: JSON.stringify(body) });
          toast("✅ تمت الإضافة والنشر");
          addForm.classList.add("hidden");
          addForm.dataset.built = "";
          addBtn.textContent = "➕ إضافة نصاب جديد";
          loadScamManageList();
        } catch (e) { toast("⚠️ " + e.message); }
      };
    }
  };
  await loadScamManageList();
}

async function loadScamManageList() {
  const list = document.getElementById("scamManageList");
  list.innerHTML = "";
  const reports = await api("/api/admin/scam/reports");
  if (!reports.length) { list.innerHTML = `<div class="empty">لا توجد بلاغات منشورة بعد</div>`; return; }
  for (const r of reports) {
    const card = document.createElement("div");
    card.className = "pending-card";
    card.innerHTML = scamManageCardBody(r);
    list.appendChild(card);
    wireScamManageCard(card, r);
  }
}

function scamManageCardBody(r) {
  return `
    <div class="meta-line"><b>الاسم:</b> ${esc(r.full_name)} ${esc(r.surname)}</div>
    <div class="meta-line"><b>بالروسية:</b> ${esc(r.full_name_ru || "—")}</div>
    <div class="meta-line"><b>الهاتف:</b> ${ltr(r.phone)} — <b>CCP:</b> ${ltr(r.ccp)} — <b>المفتاح:</b> ${ltr(r.cle_rip)}</div>
    <div class="meta-line"><b>البطاقة:</b> ${ltr(r.card)} — <b>الجواز:</b> ${ltr(r.passport)}</div>
    <div class="meta-line"><b>Telegram ID:</b> ${ltr(r.telegram_user_id)} — <b>الميلاد:</b> ${esc(r.date_of_birth || "—")}</div>
    <div class="meta-line"><b>السبب:</b> ${esc(r.reason)}</div>
    <div class="btn-row">
      <button class="btn edit-scam secondary">✏️ تعديل</button>
      <button class="btn delete-scam danger">🗑️ حذف</button>
    </div>
    <div class="scam-edit-form hidden"></div>`;
}

const SCAM_LTR_KEYS = new Set(["telegram_user_id", "phone", "ccp", "cle_rip", "card", "passport"]);

function scamEditFormHtml(r) {
  const fields = SCAM_EDIT_FIELDS.map(([key, label]) => {
    const ltrAttr = SCAM_LTR_KEYS.has(key) ? ' class="ltr-field" dir="ltr"' : "";
    return `<div class="form-group"><label>${label}</label><input data-key="${key}"${ltrAttr} value="${esc(r[key] || "")}"></div>`;
  }).join("");
  return `${fields}
    <div class="form-group"><label>سبب البلاغ</label><textarea data-key="reason">${esc(r.reason || "")}</textarea></div>
    <div class="btn-row">
      <button class="btn save-scam" style="background:var(--success)">💾 حفظ</button>
      <button class="btn cancel-scam secondary">إلغاء</button>
    </div>`;
}

function wireScamManageCard(card, r) {
  const editBtn = card.querySelector(".edit-scam");
  const deleteBtn = card.querySelector(".delete-scam");
  const formWrap = card.querySelector(".scam-edit-form");

  editBtn.onclick = () => {
    const opening = formWrap.classList.contains("hidden");
    formWrap.classList.toggle("hidden", !opening);
    editBtn.textContent = opening ? "✖️ إغلاق التعديل" : "✏️ تعديل";
    if (opening && !formWrap.dataset.built) {
      formWrap.innerHTML = scamEditFormHtml(r);
      formWrap.dataset.built = "1";
      formWrap.querySelector(".cancel-scam").onclick = () => { formWrap.classList.add("hidden"); editBtn.textContent = "✏️ تعديل"; };
      formWrap.querySelector(".save-scam").onclick = async () => {
        const body = { id: r.id };
        formWrap.querySelectorAll("[data-key]").forEach(el => body[el.dataset.key] = el.value.trim());
        try {
          await api("/api/admin/scam/edit", { method: "POST", body: JSON.stringify(body) });
          Object.assign(r, body);
          card.innerHTML = scamManageCardBody(r);
          wireScamManageCard(card, r);
          toast("✅ تم الحفظ");
        } catch (e) { toast("⚠️ " + e.message); }
      };
    }
  };

  let confirming = false;
  deleteBtn.onclick = async () => {
    if (!confirming) {
      confirming = true;
      deleteBtn.textContent = "‼️ اضغط مرة أخرى للتأكيد";
      setTimeout(() => { confirming = false; deleteBtn.textContent = "🗑️ حذف"; }, 3000);
      return;
    }
    try {
      await api("/api/admin/scam/delete", { method: "POST", body: JSON.stringify({ id: r.id }) });
      toast("🗑️ تم الحذف");
      card.remove();
    } catch (e) { toast("⚠️ " + e.message); }
  };
}

// ══════════════════════════════════════════════════════════════════════════
// BROADCAST
// ══════════════════════════════════════════════════════════════════════════

function viewBroadcast() {
  elApp.innerHTML = `
    <div class="form-group"><label>نص الرسالة</label><textarea id="msg" style="min-height:120px"></textarea></div>
    <div class="form-group"><label>أين تريد النشر؟</label>
      <div class="option-row">
        <div class="option-pill selected" data-dst="users">📨 المستخدمون</div>
        <div class="option-pill" data-dst="groups">📣 المجموعات</div>
        <div class="option-pill" data-dst="app">📲 التطبيق المصغر</div>
      </div>
    </div>
    <button class="btn" id="sendBtn">إرسال البث</button>`;
  const dest = { users: true, groups: false, app: false };
  elApp.querySelectorAll("[data-dst]").forEach(p => p.onclick = () => {
    dest[p.dataset.dst] = !dest[p.dataset.dst];
    p.classList.toggle("selected", dest[p.dataset.dst]);
  });
  document.getElementById("sendBtn").onclick = async () => {
    const message = document.getElementById("msg").value.trim();
    if (!message) { toast("⚠️ اكتب رسالة أولًا"); return; }
    if (!dest.users && !dest.groups && !dest.app) { toast("⚠️ اختر وجهة واحدة على الأقل"); return; }
    try {
      const res = await api("/api/admin/broadcast", { method: "POST", body: JSON.stringify({
        message, send_users: dest.users, send_groups: dest.groups, publish_app: dest.app,
      })});
      toast(`✅ تم الإرسال${dest.users ? ` إلى ${res.sent} مستخدم` : ""}`);
      back();
    } catch (e) { toast("⚠️ " + e.message); }
  };
}

// ══════════════════════════════════════════════════════════════════════════
// VERIFIED USERS
// ══════════════════════════════════════════════════════════════════════════

function viewUsers() {
  elApp.innerHTML = `
    <div class="search-bar"><span class="icon">🔍</span><input id="userSearch" placeholder="بحث بالاسم، اليوزر، أو الـID"></div>
    <div id="usersList"></div>`;
  document.getElementById("userSearch").oninput = debounce(async (e) => {
    const q = e.target.value.trim();
    const list = document.getElementById("usersList");
    if (!q) { list.innerHTML = ""; return; }
    const results = await api(`/api/admin/users?q=${encodeURIComponent(q)}`);
    list.innerHTML = "";
    if (!results.length) { list.innerHTML = `<div class="empty">😔 لا توجد نتائج</div>`; return; }
    for (const u of results) {
      const card = document.createElement("div");
      card.className = "pending-card";
      const label = u.username ? `@${esc(u.username)}` : esc(u.name || "—");
      const joined = u.joined ? new Date(u.joined).toLocaleDateString("ar-DZ") : "—";
      card.innerHTML = `
        <div class="meta-line"><b>الاسم:</b> ${esc(u.name || "—")} (${label})</div>
        <div class="meta-line"><b>ID:</b> ${u.user_id}</div>
        <div class="meta-line"><b>عضو منذ:</b> ${joined} — <b>إعلانات منشورة:</b> ${u.post_count}</div>
        <button class="btn verify-toggle"></button>`;
      renderVerifyButton(card, u);
      list.appendChild(card);
    }
  }, 350);
}

function renderVerifyButton(card, u) {
  const btn = card.querySelector(".verify-toggle");
  btn.className = "btn verify-toggle" + (u.verified ? " danger" : "");
  if (!u.verified) btn.style.background = "var(--success)";
  btn.textContent = u.verified ? "❌ إلغاء التوثيق" : "☑️ توثيق هذا المستخدم";
  btn.onclick = async () => {
    try {
      await api("/api/admin/verify", { method: "POST", body: JSON.stringify({ user_id: u.user_id, verified: !u.verified }) });
      u.verified = !u.verified;
      toast(u.verified ? "✅ تم التوثيق" : "تم إلغاء التوثيق");
      renderVerifyButton(card, u);
    } catch (e) { toast("⚠️ " + e.message); }
  };
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

const VIEWS = { dashboard: viewDashboard, pending: viewPending, scamManage: viewScamManage, broadcast: viewBroadcast, users: viewUsers };

go("dashboard", {}, "👨‍💼 لوحة التحكم");
