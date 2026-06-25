# -*- coding: utf-8 -*-
"""KADER DZ Mini App backend.

Serves:
 - read-only content pages (guide/consular/services/about), generated from content.py
 - marketplace / roommate / travel browsing (reads the same JSON files the bot writes)
 - submission endpoints (item/listing/travel/inquiry) — validated via Telegram initData,
   written to the same storage modules the bot uses, with the admin notified directly
   over the Bot API (the running bot.py process then handles approve/reject taps as usual,
   since they all share the same JSON storage files on disk)
 - an admin dashboard (stats / pending approvals / broadcast), gated to ADMIN_IDS

Run with: uvicorn webapp_api:app --host 127.0.0.1 --port 8001
"""
import hashlib
import hmac
import os
import re
import time
from urllib.parse import parse_qsl

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import content as C
import home_banner_storage as BANNER
import inquiry_storage as INQS
import marketplace_storage as MKT
import travel_storage as TRV
import user_storage as US

load_dotenv()
BOT_TOKEN    = os.getenv("BOT_TOKEN")
INQUIRY_CHAT = os.getenv("INQUIRY_FORWARD_CHAT")
GROUP_IDS    = [int(x.strip()) for x in os.getenv("GROUP_IDS", "").split(",") if x.strip()]
ADMINS       = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()] or [872846255]
BOT_USERNAME = os.getenv("BOT_USERNAME", "DzHelpInRuss_Bot")
API_BASE     = f"https://api.telegram.org/bot{BOT_TOKEN}"

_DIR = os.path.dirname(__file__)
app = FastAPI()


# ══════════════════════════════════════════════════════════════════════════════
# Telegram initData validation
# ══════════════════════════════════════════════════════════════════════════════

def _validate_init_data(init_data: str) -> dict:
    """Validate the Telegram WebApp initData string, return the embedded user dict."""
    if not init_data:
        raise HTTPException(401, "missing init data")
    pairs = dict(parse_qsl(init_data, strict_parsing=False))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "missing hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc_hash, received_hash):
        raise HTTPException(401, "invalid hash")
    auth_date = int(pairs.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise HTTPException(401, "init data expired")
    import json as _json
    user = _json.loads(pairs.get("user", "{}"))
    return user


def _current_user(x_telegram_init_data: str = Header(default="")) -> dict:
    return _validate_init_data(x_telegram_init_data)


def _current_admin(x_telegram_init_data: str = Header(default="")) -> dict:
    user = _validate_init_data(x_telegram_init_data)
    if user.get("id") not in ADMINS:
        raise HTTPException(403, "admin only")
    return user


# ══════════════════════════════════════════════════════════════════════════════
# Direct Bot API helpers (this process is separate from the running bot.py)
# ══════════════════════════════════════════════════════════════════════════════

async def _tg_send_message(chat_id, text, reply_markup=None, parse_mode="MarkdownV2"):
    async with httpx.AsyncClient(timeout=15) as client:
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            await client.post(f"{API_BASE}/sendMessage", json=payload)
        except Exception:
            pass


async def _tg_send_photo(chat_id, photo_id, caption, reply_markup=None, parse_mode="MarkdownV2"):
    async with httpx.AsyncClient(timeout=15) as client:
        payload = {"chat_id": chat_id, "photo": photo_id, "caption": caption}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            await client.post(f"{API_BASE}/sendPhoto", json=payload)
        except Exception:
            pass


def _esc(text) -> str:
    text = str(text) if text else "—"
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)


def _approve_kb(prefix: str, item_id: str):
    return {"inline_keyboard": [[
        {"text": "✅ موافقة", "callback_data": f"{prefix}_app_{item_id}"},
        {"text": "❌ رفض",    "callback_data": f"{prefix}_rej_{item_id}"},
    ]]}


def _fwd_chat() -> str | None:
    return INQUIRY_CHAT or (str(ADMINS[0]) if ADMINS else None)


# ══════════════════════════════════════════════════════════════════════════════
# Content pages (guide / consular / services / about) — generated from content.py
# ══════════════════════════════════════════════════════════════════════════════

def _md2_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'§LINK§\1§§\2§LINKEND§', text)
    text = re.sub(r'\\([_*\[\]()~`>#+\-=|{}.!])', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'<b>\1</b>', text)
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'§LINK§(.+?)§§(.+?)§LINKEND§', r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    return text.replace("\n", "<br>")


CONTENT_TREE = [
    {"id": "guide", "icon": "📘", "title": "دليلك الشامل", "sections": [
        {"title": "قبل الوصول إلى روسيا", "pages": [
            ("تأشيرة الدخول", "VISA_GUIDE"),
            ("استمارة التأشيرة", "VISA_FORM"),
            ("موعد التأشيرة", "VISA_APPOINTMENT"),
            ("توثيق الوثائق", "AUTH_DOCUMENTS"),
            ("القنصلية الروسية", "CONSULATE_CONTACT"),
            ("السفارة الجزائرية في روسيا", "ALGERIAN_EMBASSY"),
            ("تواصل شركة الطيران", "AIRLINE_CONTACT"),
        ]},
        {"title": "بعد الوصول إلى روسيا", "pages": [
            ("فتح حساب بنكي", "BANK_ACCOUNT"),
            ("الحصول على شريحة هاتف", "SIM_CARD"),
            ("الضرائب والتأمين الاجتماعي", "TAX_SOCIAL"),
        ]},
    ]},
    {"id": "consular", "icon": "🏛️", "title": "الخدمات القنصلية", "sections": [
        {"title": None, "pages": [
            ("التسجيل القنصلي", "CONSULAR_REGISTRATION"),
            ("جواز السفر البيومتري", "CONSULAR_PASSPORT"),
            ("الحالة المدنية", "CONSULAR_CIVIL_STATUS"),
            ("الخدمة الوطنية", "CONSULAR_MILITARY"),
            ("الانتخابات", "CONSULAR_ELECTIONS"),
            ("وثائق أخرى", "CONSULAR_OTHER"),
            ("التواصل مع القنصلية", "CONSULAR_CONTACT"),
        ]},
    ]},
    {"id": "services", "icon": "⚙️", "title": "الخدمات", "sections": [
        {"title": None, "pages": [
            ("التسجيل الجامعي", "REGISTRATION_TEXT"),
            ("ترجمة الوثائق", "TRANSLATION_TEXT"),
            ("تحويل الأموال", "MONEY_TRANSFER"),
            ("استقبال في المطار", "AIRPORT_PICKUP"),
            ("استشارة", "CONSULTATION_TEXT"),
        ]},
    ]},
    {"id": "about", "icon": "ℹ️", "title": "عن البوت", "sections": [
        {"title": None, "pages": [
            ("نبذة عنا", "ABOUT_TEXT"),
            ("التواصل", "CONTACT_TEXT"),
            ("الموقع الرسمي", "WEBSITE_TEXT"),
            ("المساعدة", "HELP_TEXT"),
        ]},
    ]},
]


@app.get("/api/content")
def get_content_tree():
    out = []
    for cat in CONTENT_TREE:
        sections = []
        for sec in cat["sections"]:
            pages = [{"title": title, "slug": const, "body": _md2_html(getattr(C, const, ""))}
                      for title, const in sec["pages"]]
            sections.append({"title": sec["title"], "pages": pages})
        out.append({"id": cat["id"], "icon": cat["icon"], "title": cat["title"], "sections": sections})
    return out


# ══════════════════════════════════════════════════════════════════════════════
# Marketplace / roommate / travel — browsing
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/categories")
def categories():
    return MKT.CATEGORIES


@app.get("/api/cities")
def cities():
    return MKT.RUSSIAN_CITIES


@app.get("/api/routes")
def routes():
    return TRV.ROUTES


@app.get("/api/items")
def list_items(category: str | None = None, q: str | None = None, sort: str | None = None):
    items = MKT.get_approved_items()
    if category and category != "all":
        items = [i for i in items if i["category"] == category]
    if q:
        ql = q.strip().lower()
        items = [i for i in items if ql in i["title"].lower() or ql in i["description"].lower()
                  or ql in i["city"].lower()]
    if sort in ("asc", "desc"):
        items = sorted(items, key=lambda i: MKT._price_key(i["price"]), reverse=(sort == "desc"))
    return items


def _with_verified(record: dict) -> dict:
    users = US.load_users()
    return {**record, "seller_verified": US.is_verified(users, record["user_id"])}


@app.get("/api/items/{item_id}")
def get_item(item_id: str):
    item = MKT.get_item_by_id(item_id)
    if not item or item["status"] != "approved":
        raise HTTPException(404, "not found")
    return _with_verified(item)


@app.get("/api/listings")
def list_listings(city: str | None = None, metro: str | None = None, sort: str | None = None,
                  q: str | None = None):
    listings = MKT.filter_listings(city_key=city, metro=metro, sort_price=sort)
    if q:
        ql = q.strip().lower()
        listings = [l for l in listings if ql in l["description"].lower() or ql in l["city"].lower()]
    return listings


@app.get("/api/listings/{listing_id}")
def get_listing(listing_id: str):
    lst = MKT.get_listing_by_id(listing_id)
    if not lst or lst["status"] != "approved":
        raise HTTPException(404, "not found")
    return _with_verified(lst)


@app.get("/api/travel")
def list_travel():
    return TRV.get_approved_posts()


@app.get("/api/travel/{post_id}")
def get_travel(post_id: str):
    post = TRV.get_post_by_id(post_id)
    if not post or post["status"] != "approved":
        raise HTTPException(404, "not found")
    return _with_verified(post)


@app.get("/api/photo/{file_id}")
async def get_photo(file_id: str):
    if not BOT_TOKEN:
        raise HTTPException(404, "no bot token configured")
    async with httpx.AsyncClient(timeout=15) as client:
        meta = await client.get(f"{API_BASE}/getFile", params={"file_id": file_id})
        data = meta.json()
        if not data.get("ok"):
            raise HTTPException(404, "file not found")
        file_path = data["result"]["file_path"]
        file_resp = await client.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}")
    return Response(content=file_resp.content, media_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.post("/api/upload_photo")
async def upload_photo(file: UploadFile = File(...), x_telegram_init_data: str = Header(default="")):
    """Browsers can't produce a Telegram file_id directly — relay the image to the
    admin chat (silently) to obtain one, then hand that file_id back to the client."""
    _current_user(x_telegram_init_data)
    fwd = _fwd_chat()
    if not fwd:
        raise HTTPException(500, "no relay chat configured")
    content_bytes = await file.read()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_BASE}/sendPhoto",
            data={"chat_id": fwd, "caption": "📷 صورة مرفوعة من التطبيق المصغر"},
            files={"photo": (file.filename or "photo.jpg", content_bytes, file.content_type or "image/jpeg")},
        )
    data = resp.json()
    if not data.get("ok"):
        raise HTTPException(502, "upload failed")
    largest = data["result"]["photo"][-1]
    return {"file_id": largest["file_id"]}


# ══════════════════════════════════════════════════════════════════════════════
# Home banner (temporary broadcast override on the mini app home screen)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/home_banner")
def get_home_banner():
    return {"text": BANNER.get_active_banner()}


# ══════════════════════════════════════════════════════════════════════════════
# Submission forms
# ══════════════════════════════════════════════════════════════════════════════

class ItemSubmit(BaseModel):
    category: str
    title: str
    price: str
    city: str
    description: str
    photo_id: str


class ListingSubmit(BaseModel):
    type: str
    room_type: str
    city_key: str
    city: str
    price: str
    metro_distance: str
    description: str
    photos: list[str] = []


class TravelSubmit(BaseModel):
    route: str
    date: str
    flight: str = "—"
    city: str
    contact: str
    note: str = "—"


class InquirySubmit(BaseModel):
    name: str
    phone: str
    service: str
    notes: str = "—"
    target: str = "admin"  # "admin" or "community"


@app.post("/api/submit/item")
async def submit_item(body: ItemSubmit, x_telegram_init_data: str = Header(default="")):
    user = _current_user(x_telegram_init_data)
    if not body.photo_id:
        raise HTTPException(400, "photo required")
    item = MKT.add_item(
        user_id=user["id"], username=user.get("username"), first_name=user.get("first_name"),
        category=body.category, title=body.title, price=body.price,
        city=body.city, description=body.description, photo_id=body.photo_id,
    )
    cat_label = MKT.CATEGORIES.get(item["category"], item["category"])
    seller = f"@{_esc(item['username'])}" if item.get("username") else _esc(item.get("first_name"))
    msg = (
        "🛒 *إعلان جديد — Avito Algeria \\(عبر الواجهة\\)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *البائع:* {_esc(item['first_name'])} \\({seller}\\)\n"
        f"🆔 *ID:* `{item['user_id']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 *الفئة:* {_esc(cat_label)}\n"
        f"📝 *العنوان:* {_esc(item['title'])}\n"
        f"💰 *السعر:* {_esc(item['price'])}\n"
        f"📍 *المدينة:* {_esc(item['city'])}\n"
        f"💬 *الوصف:* {_esc(item['description'])}\n"
        f"🆔 *item\\_id:* `{item['id']}`"
    )
    fwd = _fwd_chat()
    if fwd:
        await _tg_send_photo(int(fwd), item["photo_id"], msg, _approve_kb("mkt", item["id"]))
    return {"ok": True, "id": item["id"]}


@app.post("/api/submit/listing")
async def submit_listing(body: ListingSubmit, x_telegram_init_data: str = Header(default="")):
    user = _current_user(x_telegram_init_data)
    photos = body.photos[:2]
    lst = MKT.add_listing(
        user_id=user["id"], username=user.get("username"), first_name=user.get("first_name"),
        listing_type=body.type, room_type=body.room_type, city=body.city,
        city_key=body.city_key, price=body.price, metro_distance=body.metro_distance,
        description=body.description, photos=photos,
    )
    rtype = MKT.ROOMMATE_TYPES.get(lst["type"], lst["type"])
    rroom = MKT.ROOM_TYPES.get(lst.get("room_type", ""), "")
    metro = MKT.METRO_DISTANCES.get(lst.get("metro_distance", ""), "")
    poster = f"@{_esc(lst['username'])}" if lst.get("username") else _esc(lst.get("first_name"))
    msg = (
        "🏠 *إعلان سكن جديد \\(عبر الواجهة\\)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *المُعلن:* {_esc(lst['first_name'])} \\({poster}\\)\n"
        f"🆔 *ID:* `{lst['user_id']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔖 *النوع:* {_esc(rtype)}\n"
        f"🛏️ *الوحدة:* {_esc(rroom)}\n"
        f"📍 *المدينة:* {_esc(lst['city'])}\n"
        f"💰 *السعر:* {_esc(lst['price'])}\n"
        f"🚇 *المترو:* {_esc(metro)}\n"
        f"💬 *التفاصيل:* {_esc(lst['description'])}\n"
        f"🆔 *listing\\_id:* `{lst['id']}`"
    )
    fwd = _fwd_chat()
    if fwd:
        if photos:
            await _tg_send_photo(int(fwd), photos[0], msg, _approve_kb("rm", lst["id"]))
        else:
            await _tg_send_message(int(fwd), msg, _approve_kb("rm", lst["id"]))
    return {"ok": True, "id": lst["id"]}


@app.post("/api/submit/travel")
async def submit_travel(body: TravelSubmit, x_telegram_init_data: str = Header(default="")):
    user = _current_user(x_telegram_init_data)
    post = TRV.add_post(
        user_id=user["id"], username=user.get("username"), first_name=user.get("first_name"),
        route=body.route, date=body.date, flight=body.flight, city=body.city,
        contact=body.contact, note=body.note,
    )
    route_lbl = _esc(TRV.ROUTES.get(post["route"], post["route"]))
    poster = f"@{_esc(post['username'])}" if post.get("username") else _esc(post.get("first_name"))
    msg = (
        "🧳 *رحلة جديدة — هبطلي ولا طلعلي معاك \\(عبر الواجهة\\)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *المُعلن:* {_esc(post['first_name'])} \\({poster}\\)\n"
        f"🆔 *ID:* `{post['user_id']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧭 *الاتجاه:* {route_lbl}\n"
        f"📅 *التاريخ:* {_esc(post['date'])}\n"
        f"✈️ *الطيران:* {_esc(post.get('flight'))}\n"
        f"📍 *التفاصيل:* {_esc(post['city'])}\n"
        f"📞 *التواصل:* {_esc(post['contact'])}\n"
        f"💬 *ملاحظة:* {_esc(post.get('note'))}\n"
        f"🆔 *post\\_id:* `{post['id']}`"
    )
    fwd = _fwd_chat()
    if fwd:
        await _tg_send_message(int(fwd), msg, _approve_kb("trv", post["id"]))
    return {"ok": True, "id": post["id"]}


@app.post("/api/submit/inquiry")
async def submit_inquiry(body: InquirySubmit, x_telegram_init_data: str = Header(default="")):
    user = _current_user(x_telegram_init_data)
    username_part = f"@{_esc(user.get('username'))}" if user.get("username") else "—"

    if body.target == "community":
        item = INQS.add_inquiry(
            user_id=user["id"], username=user.get("username"), first_name=user.get("first_name"),
            name=body.name, phone=body.phone, service=body.service, notes=body.notes,
        )
        msg = (
            "👥 *استفسار جديد — موجّه للجالية \\(عبر الواجهة\\)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *المرسل:* {_esc(user.get('first_name'))} \\({username_part}\\)\n"
            f"🆔 *ID:* `{user['id']}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 *الاسم:* {_esc(item['name'])}\n"
            f"📱 *الهاتف:* {_esc(item['phone'])}\n"
            f"🎯 *الخدمة:* {_esc(item['service'])}\n"
            f"💬 *ملاحظات:* {_esc(item['notes'])}\n"
            f"🆔 *inq\\_id:* `{item['id']}`"
        )
        fwd = _fwd_chat()
        if fwd:
            await _tg_send_message(int(fwd), msg, _approve_kb("inq", item["id"]))
        return {"ok": True, "id": item["id"]}

    msg = (
        "📥 *استفسار جديد — موجّه للإدارة \\(عبر الواجهة\\)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *المرسل:* {_esc(user.get('first_name'))} \\({username_part}\\)\n"
        f"🆔 *ID:* `{user['id']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 *الاسم:* {_esc(body.name)}\n"
        f"📱 *الهاتف:* {_esc(body.phone)}\n"
        f"🎯 *الخدمة:* {_esc(body.service)}\n"
        f"💬 *ملاحظات:* {_esc(body.notes)}"
    )
    fwd = _fwd_chat()
    if fwd:
        await _tg_send_message(int(fwd), msg)
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════════
# Admin dashboard
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/admin/check")
def admin_check(x_telegram_init_data: str = Header(default="")):
    _current_admin(x_telegram_init_data)
    return {"ok": True}


@app.get("/api/admin/stats")
def admin_stats(x_telegram_init_data: str = Header(default="")):
    _current_admin(x_telegram_init_data)
    users = US.load_users()
    s = US.get_stats(users)
    return {
        **s,
        "pending_items": len([i for i in MKT.get_all_items() if i["status"] == "pending"]),
        "pending_listings": len([l for l in MKT.get_all_listings() if l["status"] == "pending"]),
        "pending_travel": len([p for p in TRV.get_all_posts() if p["status"] == "pending"]),
        "pending_inquiries": len([i for i in INQS.get_all() if i["status"] == "pending"]),
        "approved_items": len(MKT.get_approved_items()),
        "approved_listings": len(MKT.get_approved_listings()),
        "approved_travel": len(TRV.get_approved_posts()),
    }


def _user_post_count(user_id: int) -> int:
    n = len([i for i in MKT.get_all_items() if i["user_id"] == user_id and i["status"] == "approved"])
    n += len([l for l in MKT.get_all_listings() if l["user_id"] == user_id and l["status"] == "approved"])
    n += len([p for p in TRV.get_all_posts() if p["user_id"] == user_id and p["status"] == "approved"])
    return n


@app.get("/api/admin/users")
def admin_search_users(q: str = "", x_telegram_init_data: str = Header(default="")):
    _current_admin(x_telegram_init_data)
    users = US.load_users()
    results = US.search_users(users, q)
    for r in results:
        r["post_count"] = _user_post_count(r["user_id"])
    return results


class VerifyBody(BaseModel):
    user_id: int
    verified: bool


@app.post("/api/admin/verify")
def admin_verify_user(body: VerifyBody, x_telegram_init_data: str = Header(default="")):
    _current_admin(x_telegram_init_data)
    users = US.load_users()
    if str(body.user_id) not in users:
        raise HTTPException(404, "user not found")
    US.set_verified(users, body.user_id, body.verified)
    return {"ok": True}


@app.get("/api/admin/pending")
def admin_pending(x_telegram_init_data: str = Header(default="")):
    _current_admin(x_telegram_init_data)
    return {
        "items": [i for i in MKT.get_all_items() if i["status"] == "pending"],
        "listings": [l for l in MKT.get_all_listings() if l["status"] == "pending"],
        "travel": [p for p in TRV.get_all_posts() if p["status"] == "pending"],
        "inquiries": [i for i in INQS.get_all() if i["status"] == "pending"],
    }


async def _notify_groups(text: str, contact_user_id: int | None = None, photo_id: str | None = None):
    rows = []
    if contact_user_id:
        rows.append([{"text": "💬 تواصل مع المعلن", "url": f"tg://user?id={contact_user_id}"}])
    rows.append([{"text": "🤖 الانتقال إلى البوت", "url": f"https://t.me/{BOT_USERNAME}"}])
    kb = {"inline_keyboard": rows}
    for gid in GROUP_IDS:
        if photo_id:
            await _tg_send_photo(gid, photo_id, text, kb)
        else:
            await _tg_send_message(gid, text, kb)


class ApproveBody(BaseModel):
    kind: str  # item | listing | travel | inquiry
    id: str
    publish: bool = True  # also post to groups + broadcast teaser, vs. accept-only


@app.post("/api/admin/approve")
async def admin_approve(body: ApproveBody, x_telegram_init_data: str = Header(default="")):
    _current_admin(x_telegram_init_data)
    if body.kind == "item":
        item = MKT.get_item_by_id(body.id)
        if not item:
            raise HTTPException(404, "not found")
        MKT.approve_item(body.id)
        await _tg_send_message(item["user_id"], C.MKT_APPROVED_NOTIFY)
        if body.publish:
            cat = MKT.CATEGORIES.get(item["category"], item["category"])
            text = (f"🛒 *Avito Algeria* — {_esc(cat)}\n📝 *{_esc(item['title'])}*\n"
                    f"💰 {_esc(item['price'])}\n📍 {_esc(item['city'])}\n💬 {_esc(item['description'])}")
            await _notify_groups(text, item["user_id"], photo_id=item.get("photo_id"))
    elif body.kind == "listing":
        lst = MKT.get_listing_by_id(body.id)
        if not lst:
            raise HTTPException(404, "not found")
        MKT.approve_listing(body.id)
        await _tg_send_message(lst["user_id"], C.RM_APPROVED_NOTIFY)
        if body.publish:
            text = (f"🏠 *إيجاد شريك سكن*\n📍 {_esc(lst['city'])}\n💰 {_esc(lst['price'])}\n"
                    f"💬 {_esc(lst['description'])}")
            photos = lst.get("photos") or []
            await _notify_groups(text, lst["user_id"], photo_id=(photos[0] if photos else None))
    elif body.kind == "travel":
        post = TRV.get_post_by_id(body.id)
        if not post:
            raise HTTPException(404, "not found")
        TRV.approve_post(body.id)
        await _tg_send_message(post["user_id"], C.TRV_APPROVED_NOTIFY)
        if body.publish:
            route = _esc(TRV.ROUTES.get(post["route"], post["route"]))
            text = (f"🧳 *هبطلي ولا طلعلي معاك*\n🧭 {route}\n📅 {_esc(post['date'])}\n"
                    f"📍 {_esc(post['city'])}\n📞 {_esc(post['contact'])}")
            await _notify_groups(text, post["user_id"])
    elif body.kind == "inquiry":
        item = INQS.get_by_id(body.id)
        if not item:
            raise HTTPException(404, "not found")
        INQS.approve_inquiry(body.id)
        await _tg_send_message(item["user_id"], C.INQ_APPROVED_NOTIFY)
        if body.publish:
            text = (f"👥 *استفسار من الجالية*\n📛 {_esc(item['name'])}\n🎯 {_esc(item['service'])}\n"
                    f"💬 {_esc(item['notes'])}")
            await _notify_groups(text, item["user_id"])
    else:
        raise HTTPException(400, "unknown kind")
    return {"ok": True}


@app.post("/api/admin/reject")
async def admin_reject(body: ApproveBody, x_telegram_init_data: str = Header(default="")):
    _current_admin(x_telegram_init_data)
    if body.kind == "item":
        item = MKT.get_item_by_id(body.id)
        if item:
            MKT.delete_item(body.id)
            await _tg_send_message(item["user_id"], C.MKT_REJECTED_NOTIFY)
    elif body.kind == "listing":
        lst = MKT.get_listing_by_id(body.id)
        if lst:
            MKT.delete_listing(body.id)
            await _tg_send_message(lst["user_id"], C.RM_REJECTED_NOTIFY)
    elif body.kind == "travel":
        post = TRV.get_post_by_id(body.id)
        if post:
            TRV.delete_post(body.id)
            await _tg_send_message(post["user_id"], C.TRV_REJECTED_NOTIFY)
    elif body.kind == "inquiry":
        item = INQS.get_by_id(body.id)
        if item:
            INQS.delete_inquiry(body.id)
            await _tg_send_message(item["user_id"], C.INQ_REJECTED_NOTIFY)
    else:
        raise HTTPException(400, "unknown kind")
    return {"ok": True}


class BroadcastBody(BaseModel):
    message: str
    send_users: bool = True
    send_groups: bool = False
    publish_app: bool = False


@app.post("/api/admin/broadcast")
async def admin_broadcast(body: BroadcastBody, x_telegram_init_data: str = Header(default="")):
    _current_admin(x_telegram_init_data)
    sent = 0
    if body.send_users:
        users = US.load_users()
        ids = US.get_user_ids(users)
        for uid in ids:
            await _tg_send_message(uid, body.message, parse_mode=None)
            sent += 1
    if body.send_groups:
        for gid in GROUP_IDS:
            await _tg_send_message(gid, body.message, parse_mode=None)
    if body.publish_app:
        BANNER.set_banner(body.message, hours=24)
    return {
        "ok": True, "sent": sent,
        "groups": len(GROUP_IDS) if body.send_groups else 0,
        "published_app": body.publish_app,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Static frontend
# ══════════════════════════════════════════════════════════════════════════════

app.mount("/static", StaticFiles(directory=os.path.join(_DIR, "webapp", "static")), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(_DIR, "webapp", "index.html"))


@app.get("/admin")
def admin_page():
    return FileResponse(os.path.join(_DIR, "webapp", "admin.html"))
