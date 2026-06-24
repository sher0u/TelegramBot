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
    <div class="list-item" id="broadcastBtn"><span class="title">📤 بث رسالة</span><span class="chevron">‹</span></div>`;
  document.getElementById("pendingBtn").onclick = () => go("pending", {}, "📋 الطلبات المعلقة");
  document.getElementById("broadcastBtn").onclick = () => go("broadcast", {}, "📤 بث رسالة");
  try {
    const s = await api("/api/admin/stats");
    document.getElementById("stats").innerHTML = `
      <div class="stat-grid">
        <div class="stat-box"><div class="num">${s.total}</div><div class="lbl">إجمالي المستخدمين</div></div>
        <div class="stat-box"><div class="num">${s.new_today}</div><div class="lbl">جدد اليوم</div></div>
        <div class="stat-box"><div class="num">${s.pending_items + s.pending_listings + s.pending_travel + s.pending_inquiries}</div><div class="lbl">طلبات معلقة</div></div>
        <div class="stat-box"><div class="num">${s.approved_items + s.approved_listings + s.approved_travel}</div><div class="lbl">إعلانات منشورة</div></div>
      </div>`;
  } catch (e) {
    elApp.innerHTML = `<div class="empty">🚫 غير مصرّح لك بالوصول لهذه اللوحة</div>`;
  }
}

// ══════════════════════════════════════════════════════════════════════════
// PENDING APPROVALS
// ══════════════════════════════════════════════════════════════════════════

const KIND_LABELS = { items: "🛒 إعلان سوق", listings: "🏠 إعلان سكن", travel: "🧳 رحلة", inquiries: "👥 استفسار جالية" };
const KIND_SINGULAR = { items: "item", listings: "listing", travel: "travel", inquiries: "inquiry" };

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
      card.querySelector(".approve").onclick = () => act("approve", KIND_SINGULAR[kind], it.id, card);
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
  }
  const poster = it.username ? `@${esc(it.username)}` : esc(it.first_name || "—");
  return `${lines}<div class="meta-line"><b>المرسل:</b> ${poster}</div>
    <div class="btn-row">
      <button class="btn approve" style="background:var(--success)">✅ موافقة</button>
      <button class="btn reject danger">❌ رفض</button>
    </div>`;
}

async function act(action, kind, id, card) {
  try {
    await api(`/api/admin/${action}`, { method: "POST", body: JSON.stringify({ kind, id }) });
    toast(action === "approve" ? "✅ تمت الموافقة" : "❌ تم الرفض");
    card.remove();
  } catch (e) { toast("⚠️ " + e.message); }
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

const VIEWS = { dashboard: viewDashboard, pending: viewPending, broadcast: viewBroadcast };

go("dashboard", {}, "👨‍💼 لوحة التحكم");
