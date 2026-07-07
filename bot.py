# -*- coding: utf-8 -*-
"""KADER DZ Telegram Bot — main entry point."""
import asyncio
import logging
import os
import warnings

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import content as C
import keyboards as KB
import inquiry_storage as INQS
import marketplace_storage as MKT
import scam_storage as SCAM
import travel_storage as TRV
from admin import get_admin_handlers
from user_storage import (
    add_user, get_user_ids, is_teaser_snoozed, is_verified, load_users, save_users, snooze_teasers,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN    = os.getenv("BOT_TOKEN")
INQUIRY_CHAT = os.getenv("INQUIRY_FORWARD_CHAT")
GROUP_IDS    = [int(x.strip()) for x in os.getenv("GROUP_IDS", "").split(",") if x.strip()]

# ── Conversation states ───────────────────────────────────────────────────────

_INQ_TARGET, _INQ_PHONE, _INQ_SERVICE, _INQ_NOTES = range(4)

# Marketplace post: choose category → title → price → city → desc → photo
_MKT_CAT, _MKT_TITLE, _MKT_PRICE, _MKT_CITY, _MKT_DESC, _MKT_PHOTO = range(10, 16)

# Roommate post: type → room_type → city_choice → city_text → price → metro → desc
_RM_TYPE, _RM_ROOM_TYPE, _RM_CITY_CHOICE, _RM_CITY_TEXT, _RM_PRICE, _RM_METRO, _RM_DESC = range(20, 27)

# Travel post: route → date → flight → city → contact → note
_TRV_ROUTE, _TRV_DATE, _TRV_FLIGHT, _TRV_CITY, _TRV_CONTACT, _TRV_NOTE = range(30, 36)

# شرلوك الجزائري — check: free-text query → pick from name candidates
_SCAM_CHECK_QUERY, _SCAM_CHECK_PICK = range(40, 42)

# شرلوك الجزائري — report: name → 7 optional fields (looped) → reason → photo
_SCAM_NAME, _SCAM_OPTIONAL, _SCAM_REASON, _SCAM_PHOTO = range(50, 54)

SCAM_OPTIONAL_STEPS = [
    ("surname",          "SCAM_REPORT_SURNAME"),
    ("date_of_birth",    "SCAM_REPORT_DOB"),
    ("telegram_user_id", "SCAM_REPORT_TGID"),
    ("phone",            "SCAM_REPORT_PHONE"),
    ("ccp",              "SCAM_REPORT_CCP"),
    ("card",             "SCAM_REPORT_CARD"),
    ("passport",         "SCAM_REPORT_PASSPORT"),
]

MD2 = ParseMode.MARKDOWN_V2

# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def _esc(text) -> str:
    return escape_markdown(str(text) if text else "—", version=2)


_LRM = "‎"


def _ltr(text) -> str:
    """Wraps a value in Unicode LRM marks so digits/IDs render left-to-right
    even when embedded in an RTL (Arabic) message."""
    s = _esc(text)
    return f"{_LRM}{s}{_LRM}" if s and s != "—" else s


async def _edit_or_reply(update: Update, text: str, keyboard=None, parse_mode=MD2) -> None:
    kwargs = dict(text=text, parse_mode=parse_mode, reply_markup=keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(**kwargs)
    else:
        await update.message.reply_text(**kwargs)


def _rm_filters(context) -> dict:
    return context.user_data.setdefault("rm_filters", {
        "city": None, "metro": None, "price": None
    })


# ── Conversation clean-up helpers ─────────────────────────────────────────────

async def _conv_edit(query, context, text: str, keyboard=None) -> None:
    """Callback step — edit the single conversation message in place."""
    await query.edit_message_text(text, parse_mode=MD2, reply_markup=keyboard)
    context.user_data["conv_msg_id"]  = query.message.message_id
    context.user_data["conv_chat_id"] = query.message.chat_id


async def _conv_reply(update: Update, context, text: str, keyboard=None) -> None:
    """Text step — delete user's message, then edit the conversation message.
    Keeps the chat perfectly clean: only ONE bot message visible at all times."""
    chat_id = update.effective_chat.id

    # Delete the user's typed / photo message
    try:
        await update.message.delete()
    except Exception:
        pass

    prev_id = context.user_data.get("conv_msg_id")
    if prev_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=prev_id,
                text=text, parse_mode=MD2, reply_markup=keyboard,
            )
            return
        except Exception:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=prev_id)
            except Exception:
                pass

    # Fallback: send a fresh message
    msg = await context.bot.send_message(
        chat_id=chat_id, text=text, parse_mode=MD2, reply_markup=keyboard,
    )
    context.user_data["conv_msg_id"] = msg.message_id


# ══════════════════════════════════════════════════════════════════════════════
# /START
# ══════════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    users = context.application.bot_data.setdefault("users", {})
    user  = update.effective_user
    if add_user(users, user.id, user.first_name, user.username):
        save_users(users)
    await _edit_or_reply(update, C.WELCOME, KB.main_menu_kb())


# ── Simple commands ───────────────────────────────────────────────────────────

async def help_cmd(update, context):
    await update.message.reply_text(C.HELP_TEXT, parse_mode=MD2)

async def about_cmd(update, context):
    await update.message.reply_text(C.ABOUT_TEXT, parse_mode=MD2)

async def contact_cmd(update, context):
    await update.message.reply_text(C.CONTACT_TEXT, parse_mode=MD2, reply_markup=KB.contact_kb())

async def website_cmd(update, context):
    await update.message.reply_text(C.WEBSITE_TEXT, parse_mode=MD2)


# ══════════════════════════════════════════════════════════════════════════════
# MARKETPLACE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _verified_badge(user_id: int) -> str:
    return " ✅ موثّق" if is_verified(load_users(), user_id) else ""


def _fmt_item(item: dict, num: int, total: int) -> str:
    cat_label  = MKT.CATEGORIES.get(item["category"], item["category"])
    photo_line = "📷 _يوجد صورة_\n" if item.get("photo_id") else ""
    badge      = _verified_badge(item["user_id"])
    return (
        f"🛒 *Avito Algeria* — {_esc(cat_label)}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 *{_esc(item['title'])}*{badge}\n\n"
        f"💰 *السعر:* {_esc(item['price'])}\n"
        f"📍 *المدينة:* {_esc(item['city'])}\n"
        f"💬 *الوصف:* {_esc(item['description'])}\n"
        f"{photo_line}"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 {num}/{total}"
    )


def _fmt_listing(lst: dict, num: int, total: int) -> str:
    rtype  = MKT.ROOMMATE_TYPES.get(lst["type"], lst["type"])
    rroom  = MKT.ROOM_TYPES.get(lst.get("room_type", ""), "")
    metro  = MKT.METRO_DISTANCES.get(lst.get("metro_distance", ""), "")
    badge  = _verified_badge(lst["user_id"])
    return (
        f"🏠 *إيجاد شريك سكن*{badge}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔖 *النوع:* {_esc(rtype)}\n"
        f"🛏️ *الوحدة:* {_esc(rroom)}\n"
        f"📍 *المدينة:* {_esc(lst['city'])}\n"
        f"💰 *السعر:* {_esc(lst['price'])}\n"
        f"🚇 *المترو:* {_esc(metro)}\n"
        f"💬 *التفاصيل:* {_esc(lst['description'])}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 {num}/{total}"
    )


async def _show_item(query, item: dict, index: int, items: list,
                     active_cat: str = "all") -> None:
    """Display marketplace item — handles photo/text switching cleanly."""
    caption = _fmt_item(item, index + 1, len(items))
    kb = KB.avito_browse_kb(active_cat, index, len(items),
                             item["id"], seller_user_id=item.get("user_id"))
    if item.get("photo_id"):
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=item["photo_id"],
                                      caption=caption, parse_mode=MD2),
                reply_markup=kb,
            )
        except Exception:
            try:
                await query.message.delete()
            except Exception:
                pass
            await query.message.reply_photo(
                photo=item["photo_id"], caption=caption,
                parse_mode=MD2, reply_markup=kb,
            )
    else:
        try:
            await query.edit_message_text(caption, parse_mode=MD2, reply_markup=kb)
        except Exception:
            try:
                await query.message.delete()
            except Exception:
                pass
            await query.message.reply_text(caption, parse_mode=MD2, reply_markup=kb)


async def _send_item_to_admin(context, item: dict) -> None:
    from admin import ADMINS
    fwd = INQUIRY_CHAT or (str(ADMINS[0]) if ADMINS else None)
    if not fwd:
        return
    seller    = f"@{_esc(item['username'])}" if item.get("username") else _esc(item.get("first_name"))
    cat_label = _esc(MKT.CATEGORIES.get(item["category"], item["category"]))
    msg = (
        "🛒 *إعلان جديد — Avito Algeria*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *البائع:* {_esc(item['first_name'])} \\({seller}\\)\n"
        f"🆔 *ID:* `{item['user_id']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 *الفئة:* {cat_label}\n"
        f"📝 *العنوان:* {_esc(item['title'])}\n"
        f"💰 *السعر:* {_esc(item['price'])}\n"
        f"📍 *المدينة:* {_esc(item['city'])}\n"
        f"💬 *الوصف:* {_esc(item['description'])}\n"
        f"🆔 *item\\_id:* `{item['id']}`"
    )
    kb = KB.admin_approve_mkt_kb(item["id"])
    try:
        if item.get("photo_id"):
            await context.bot.send_photo(
                chat_id=int(fwd), photo=item["photo_id"],
                caption=msg, parse_mode=MD2, reply_markup=kb,
            )
        else:
            await context.bot.send_message(
                chat_id=int(fwd), text=msg, parse_mode=MD2, reply_markup=kb,
            )
    except Exception as e:
        logger.error("Failed to send item to admin: %s", e)


async def _send_listing_to_admin(context, lst: dict) -> None:
    from admin import ADMINS
    fwd = INQUIRY_CHAT or (str(ADMINS[0]) if ADMINS else None)
    if not fwd:
        return
    poster = f"@{_esc(lst['username'])}" if lst.get("username") else _esc(lst.get("first_name"))
    rtype  = _esc(MKT.ROOMMATE_TYPES.get(lst["type"], lst["type"]))
    rroom  = _esc(MKT.ROOM_TYPES.get(lst.get("room_type", ""), ""))
    metro  = _esc(MKT.METRO_DISTANCES.get(lst.get("metro_distance", ""), ""))
    msg = (
        "🏠 *إعلان سكن جديد*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *المُعلن:* {_esc(lst['first_name'])} \\({poster}\\)\n"
        f"🆔 *ID:* `{lst['user_id']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔖 *النوع:* {rtype}\n"
        f"🛏️ *الوحدة:* {rroom}\n"
        f"📍 *المدينة:* {_esc(lst['city'])}\n"
        f"💰 *السعر:* {_esc(lst['price'])}\n"
        f"🚇 *المترو:* {metro}\n"
        f"💬 *التفاصيل:* {_esc(lst['description'])}\n"
        f"🆔 *listing\\_id:* `{lst['id']}`"
    )
    try:
        await context.bot.send_message(
            chat_id=int(fwd), text=msg, parse_mode=MD2,
            reply_markup=KB.admin_approve_rm_kb(lst["id"]),
        )
    except Exception as e:
        logger.error("Failed to send listing to admin: %s", e)


BOT_USERNAME = os.getenv("BOT_USERNAME", "DzHelpInRuss_Bot")


async def _post_to_groups(context, text: str, photo_id: str = None,
                          contact_user_id: int = None) -> None:
    """After admin approval — share the post into the configured Telegram groups."""
    rows = []
    if contact_user_id:
        rows.append([InlineKeyboardButton("💬 تواصل مع المعلن", url=f"tg://user?id={contact_user_id}")])
    rows.append([InlineKeyboardButton("🤖 الانتقال إلى البوت", url=f"https://t.me/{BOT_USERNAME}")])
    kb = InlineKeyboardMarkup(rows)
    for gid in GROUP_IDS:
        try:
            if photo_id:
                await context.bot.send_photo(chat_id=gid, photo=photo_id,
                                             caption=text, parse_mode=MD2, reply_markup=kb)
            else:
                await context.bot.send_message(chat_id=gid, text=text, parse_mode=MD2, reply_markup=kb)
        except Exception as e:
            logger.error("Failed to post to group %s: %s", gid, e)


async def _broadcast_teaser(context, teaser: str, view_callback: str) -> None:
    """Notify every bot user with a 'view details' button — sent in small batches
    so it never blocks other bot activity while it runs in the background."""
    users = context.application.bot_data.get("users", {})
    ids   = [uid for uid in get_user_ids(users) if not is_teaser_snoozed(users, uid)]
    kb    = InlineKeyboardMarkup([[
        InlineKeyboardButton("👁️ عرض التفاصيل", callback_data=view_callback),
        InlineKeyboardButton("🚫 غير مهتم", callback_data="tsr_skip"),
    ]])

    async def _send_one(uid):
        try:
            await context.bot.send_message(chat_id=uid, text=teaser, parse_mode=MD2, reply_markup=kb)
        except Exception:
            pass

    batch_size = 20
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i + batch_size]
        await asyncio.gather(*(_send_one(uid) for uid in batch))
        await asyncio.sleep(1.0)


def _broadcast_teaser_bg(context, teaser: str, view_callback: str) -> None:
    """Fire-and-forget — schedules the batched broadcast without blocking the caller."""
    asyncio.create_task(_broadcast_teaser(context, teaser, view_callback))


def _fmt_travel(post: dict) -> str:
    route = TRV.ROUTES.get(post["route"], post["route"])
    badge = _verified_badge(post["user_id"])
    return (
        f"🧳 *هبطلي ولا طلعلي معاك*{badge}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧭 *الاتجاه:* {_esc(route)}\n"
        f"📅 *التاريخ:* {_esc(post['date'])}\n"
        f"✈️ *الطيران:* {_esc(post.get('flight'))}\n"
        f"📍 *التفاصيل:* {_esc(post['city'])}\n"
        f"📞 *التواصل:* {_esc(post['contact'])}\n"
        f"💬 *ملاحظة:* {_esc(post.get('note'))}"
    )


_TRV_ROUTE_TOKENS = {"alg_to_msk": "alg_msk", "msk_to_alg": "msk_alg"}
_TRV_TOKEN_ROUTES  = {v: k for k, v in _TRV_ROUTE_TOKENS.items()}


async def _show_trv_browse(query, route: str, idx: int) -> None:
    posts = TRV.get_approved_posts_by_route(route)
    route_token = _TRV_ROUTE_TOKENS[route]
    if not posts:
        await query.edit_message_text(
            C.TRV_BROWSE_EMPTY, parse_mode=MD2,
            reply_markup=KB.trv_browse_empty_kb(route_token)
        )
        return
    idx  = max(0, min(idx, len(posts) - 1))
    post = posts[idx]
    text = _fmt_travel(post) + f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 {idx+1}/{len(posts)}"
    await query.edit_message_text(
        text, parse_mode=MD2,
        reply_markup=KB.trv_browse_kb(route_token, idx, len(posts), poster_user_id=post.get("user_id"))
    )


async def _send_travel_to_admin(context, post: dict) -> None:
    from admin import ADMINS
    fwd = INQUIRY_CHAT or (str(ADMINS[0]) if ADMINS else None)
    if not fwd:
        return
    poster = f"@{_esc(post['username'])}" if post.get("username") else _esc(post.get("first_name"))
    route  = _esc(TRV.ROUTES.get(post["route"], post["route"]))
    msg = (
        "🧳 *رحلة جديدة — هبطلي ولا طلعلي معاك*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *المُعلن:* {_esc(post['first_name'])} \\({poster}\\)\n"
        f"🆔 *ID:* `{post['user_id']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧭 *الاتجاه:* {route}\n"
        f"📅 *التاريخ:* {_esc(post['date'])}\n"
        f"✈️ *الطيران:* {_esc(post.get('flight'))}\n"
        f"📍 *التفاصيل:* {_esc(post['city'])}\n"
        f"📞 *التواصل:* {_esc(post['contact'])}\n"
        f"💬 *ملاحظة:* {_esc(post.get('note'))}\n"
        f"🆔 *post\\_id:* `{post['id']}`"
    )
    try:
        await context.bot.send_message(
            chat_id=int(fwd), text=msg, parse_mode=MD2,
            reply_markup=KB.admin_approve_trv_kb(post["id"]),
        )
    except Exception as e:
        logger.error("Failed to send travel post to admin: %s", e)


def _trv_cleanup(ctx) -> None:
    for k in ("trv_route", "trv_date", "trv_flight", "trv_city", "trv_contact"):
        ctx.user_data.pop(k, None)


def _mkt_cleanup(ctx) -> None:
    for k in ("mkt_cat", "mkt_title", "mkt_price", "mkt_city", "mkt_desc", "mkt_photo"):
        ctx.user_data.pop(k, None)


def _rm_cleanup(ctx) -> None:
    for k in ("rm_type", "rm_room_type", "rm_city", "rm_city_key",
              "rm_price", "rm_metro", "rm_desc"):
        ctx.user_data.pop(k, None)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CALLBACK ROUTER
# ══════════════════════════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    d = query.data

    # ── Navigation ────────────────────────────────────────────────────────────
    if   d == "Start":   await start(update, context)
    elif d == "noop":    pass
    elif d == "contact": await query.edit_message_text(C.CONTACT_TEXT, parse_mode=MD2,
                                                        reply_markup=KB.contact_kb())

    elif d == "tsr_skip":
        users = context.application.bot_data.get("users", {})
        snooze_teasers(users, update.effective_user.id, days=7)
        try:
            await query.message.delete()
        except Exception:
            await query.edit_message_reply_markup(reply_markup=None)
        await query.answer("🚫 لن تتلقى إشعارات مشابهة لمدة 7 أيام")

    # ── Services ──────────────────────────────────────────────────────────────
    elif d == "services_menu":
        await query.edit_message_text(C.SERVICES_MENU, parse_mode=MD2,
                                      reply_markup=KB.services_menu_kb())
    elif d == "registration_services":
        await query.edit_message_text(C.REGISTRATION_TEXT, parse_mode=MD2,
                                      reply_markup=KB.registration_kb())
    elif d == "translation_services":
        await query.edit_message_text(C.TRANSLATION_TEXT, parse_mode=MD2,
                                      reply_markup=KB.translation_kb())
    elif d == "money_transfer":
        await query.edit_message_text(C.MONEY_TRANSFER, parse_mode=MD2,
                                      reply_markup=KB.money_transfer_kb())
    elif d == "airport_pickup":
        await query.edit_message_text(C.AIRPORT_PICKUP, parse_mode=MD2,
                                      reply_markup=KB.airport_pickup_kb())
    elif d == "request_consultation":
        await query.edit_message_text(C.CONSULTATION_TEXT, parse_mode=MD2,
                                      reply_markup=KB.consultation_kb())

    # ── Consular Services ────────────────────────────────────────────────────
    elif d == "consular_menu":
        await query.edit_message_text(C.CONSULAR_MENU, parse_mode=MD2,
                                      reply_markup=KB.consular_menu_kb())
    elif d == "consular_registration":
        await query.edit_message_text(C.CONSULAR_REGISTRATION, parse_mode=MD2,
                                      reply_markup=KB.consular_back_kb())
    elif d == "consular_passport":
        await query.edit_message_text(C.CONSULAR_PASSPORT, parse_mode=MD2,
                                      reply_markup=KB.consular_back_kb())
    elif d == "consular_civil_status":
        await query.edit_message_text(C.CONSULAR_CIVIL_STATUS, parse_mode=MD2,
                                      reply_markup=KB.consular_back_kb())
    elif d == "consular_military":
        await query.edit_message_text(C.CONSULAR_MILITARY, parse_mode=MD2,
                                      reply_markup=KB.consular_back_kb())
    elif d == "consular_elections":
        await query.edit_message_text(C.CONSULAR_ELECTIONS, parse_mode=MD2,
                                      reply_markup=KB.consular_back_kb())
    elif d == "consular_other":
        await query.edit_message_text(C.CONSULAR_OTHER, parse_mode=MD2,
                                      reply_markup=KB.consular_back_kb())
    elif d == "consular_contact":
        await query.edit_message_text(C.CONSULAR_CONTACT, parse_mode=MD2,
                                      reply_markup=KB.consular_back_kb())

    # ── Guide ─────────────────────────────────────────────────────────────────
    elif d == "guide_menu":
        await query.edit_message_text(C.GUIDE_MENU, parse_mode=MD2,
                                      reply_markup=KB.guide_menu_kb())
    elif d == "before_arrival":
        await query.edit_message_text(C.BEFORE_ARRIVAL_MENU, parse_mode=MD2,
                                      reply_markup=KB.before_arrival_kb())
    elif d == "after_arrival":
        await query.edit_message_text(C.AFTER_ARRIVAL_MENU, parse_mode=MD2,
                                      reply_markup=KB.after_arrival_kb())
    elif d == "Visa_guide":
        await query.edit_message_text(C.VISA_GUIDE, parse_mode=MD2,
                                      reply_markup=KB.video_contact_kb("before_arrival"))
    elif d == "Visa_Forum":
        await query.edit_message_text(C.VISA_FORM, parse_mode=MD2,
                                      reply_markup=KB.video_contact_kb("before_arrival"))
    elif d == "visa_appointment":
        await query.edit_message_text(C.VISA_APPOINTMENT, parse_mode=MD2,
                                      reply_markup=KB.video_contact_kb("before_arrival"))
    elif d == "Authen_documents":
        await query.edit_message_text(C.AUTH_DOCUMENTS, parse_mode=MD2,
                                      reply_markup=KB.video_contact_kb("before_arrival"))
    elif d == "russian_consulate_contact":
        await query.edit_message_text(C.CONSULATE_CONTACT, parse_mode=MD2,
                                      reply_markup=KB.back_kb("before_arrival"))
    elif d == "algerian_embassy_russia":
        await query.edit_message_text(C.ALGERIAN_EMBASSY, parse_mode=MD2,
                                      reply_markup=KB.back_kb("before_arrival"))
    elif d == "airline_contact":
        await query.edit_message_text(C.AIRLINE_CONTACT, parse_mode=MD2,
                                      reply_markup=KB.back_kb("before_arrival"))
    elif d == "how_to_open_bank_account":
        await query.edit_message_text(C.BANK_ACCOUNT, parse_mode=MD2,
                                      reply_markup=KB.bank_kb())
    elif d == "how_to_get_sim":
        await query.edit_message_text(C.SIM_CARD, parse_mode=MD2,
                                      reply_markup=KB.consult_back_kb("after_arrival"))
    elif d == "how_to_get_tax_social":
        await query.edit_message_text(C.TAX_SOCIAL, parse_mode=MD2,
                                      reply_markup=KB.consult_back_kb("after_arrival"))

    # ══════════════════════════════════════════════════════════════════════════
    # شرلوك الجزائري — menu entry
    # ══════════════════════════════════════════════════════════════════════════

    elif d == "scam_menu":
        await query.edit_message_text(C.SCAM_MENU_TEXT, parse_mode=MD2,
                                      reply_markup=KB.scam_menu_kb(), disable_web_page_preview=True)

    # ══════════════════════════════════════════════════════════════════════════
    # AVITO ALGERIA
    # ══════════════════════════════════════════════════════════════════════════

    elif d == "avito_menu":
        await query.edit_message_text(C.AVITO_MAIN, parse_mode=MD2,
                                      reply_markup=KB.avito_main_kb())

    elif d == "avito_browse" or d == "avito_filter_all":
        items = MKT.get_approved_items()
        if not items:
            await query.edit_message_text(
                "😔 *لا توجد إعلانات بعد\\.*\n\nكن أول من ينشر إعلانًا ➕",
                parse_mode=MD2, reply_markup=KB.avito_empty_kb("all")
            )
        else:
            await _show_item(query, items[0], 0, items, active_cat="all")

    elif d.startswith("avito_filter_"):
        cat   = d.replace("avito_filter_", "")
        items = MKT.get_approved_items() if cat == "all" else MKT.get_items_by_category(cat)
        if not items:
            await query.edit_message_text(
                f"😔 *لا توجد إعلانات في هذه الفئة بعد\\.*\n\nاختر فئة أخرى أو انشر إعلانًا ➕",
                parse_mode=MD2, reply_markup=KB.avito_empty_kb(cat)
            )
        else:
            await _show_item(query, items[0], 0, items, active_cat=cat)

    elif d.startswith("avito_nav_"):
        # avito_nav_{active_cat}_{index}
        parts = d.split("_")
        idx   = int(parts[-1])
        cat   = "_".join(parts[2:-1])
        items = MKT.get_approved_items() if cat == "all" else MKT.get_items_by_category(cat)
        if not items:
            await query.edit_message_text(
                "😔 *لا توجد إعلانات\\.*",
                parse_mode=MD2, reply_markup=KB.avito_empty_kb(cat)
            )
        else:
            idx = max(0, min(idx, len(items) - 1))
            await _show_item(query, items[idx], idx, items, active_cat=cat)

    elif d.startswith("avito_goto_"):
        item_id = d[len("avito_goto_"):]
        item    = MKT.get_item_by_id(item_id)
        if not item or item["status"] != "approved":
            await query.answer("الإعلان غير متوفر", show_alert=True)
            return
        items = MKT.get_approved_items()
        idx   = next((i for i, it in enumerate(items) if it["id"] == item_id), 0)
        await _show_item(query, item, idx, items, active_cat="all")

    elif d == "avito_myitems":
        user  = update.effective_user
        items = MKT.get_user_items(user.id)
        if not items:
            await query.edit_message_text(C.AVITO_MY_EMPTY, parse_mode=MD2,
                                          reply_markup=KB.avito_main_kb())
        else:
            await query.edit_message_text(
                f"📋 *إعلاناتي* \\({len(items)}\\)\n⏳ قيد المراجعة  •  ✅ منشور",
                parse_mode=MD2, reply_markup=KB.avito_my_items_kb(items)
            )

    elif d.startswith("avito_view_"):
        item_id = d[len("avito_view_"):]
        item    = MKT.get_item_by_id(item_id)
        if not item:
            await query.answer("الإعلان غير موجود", show_alert=True)
            return
        status  = "✅ منشور" if item["status"] == "approved" else "⏳ قيد المراجعة"
        cat_lbl = MKT.CATEGORIES.get(item["category"], item["category"])
        text    = (
            f"📝 *{_esc(item['title'])}*\n"
            f"📂 {_esc(cat_lbl)}\n"
            f"💰 {_esc(item['price'])}  📍 {_esc(item['city'])}\n"
            f"💬 {_esc(item['description'])}\n"
            f"📊 الحالة: {status}"
        )
        await query.edit_message_text(text, parse_mode=MD2,
                                      reply_markup=KB.avito_item_owner_kb(item_id))

    elif d.startswith("avito_del_"):
        item_id = d[len("avito_del_"):]
        await query.edit_message_text(
            "⚠️ *هل أنت متأكد من حذف هذا الإعلان؟*",
            parse_mode=MD2, reply_markup=KB.avito_del_confirm_kb(item_id)
        )

    elif d.startswith("avito_delcfm_"):
        item_id = d[len("avito_delcfm_"):]
        MKT.delete_item(item_id)
        await query.edit_message_text(C.MKT_DELETED, parse_mode=MD2,
                                      reply_markup=KB.avito_main_kb())

    elif d == "avito_cancel_post":
        await query.edit_message_text(C.MKT_CANCELLED, parse_mode=MD2,
                                      reply_markup=KB.avito_main_kb())

    # ── Avito report ──────────────────────────────────────────────────────────
    elif d.startswith("avito_rpt_"):
        item_id = d[len("avito_rpt_"):]
        context.user_data["rpt_mkt_item"] = item_id
        await query.edit_message_text(C.MKT_REPORT_ASK, parse_mode=MD2,
                                      reply_markup=KB.avito_report_reason_kb(item_id))

    elif d.startswith("rpt_mkt_"):
        # rpt_mkt_{reason}_{item_id}
        parts   = d.split("_")
        reason  = parts[2]
        item_id = parts[3]
        item    = MKT.get_item_by_id(item_id)
        if item:
            count = MKT.report_item(item_id)
            user  = update.effective_user
            reasons = {"fake": "🤥 مزيف/احتيال", "spam": "🗑️ سبام", "inap": "🔞 غير لائق"}
            reason_lbl = reasons.get(reason, reason)
            reporter   = f"@{_esc(user.username)}" if user.username else _esc(user.first_name)
            from admin import ADMINS
            fwd = INQUIRY_CHAT or (str(ADMINS[0]) if ADMINS else None)
            if fwd:
                msg = (
                    "🚨 *بلاغ على إعلان — Avito Algeria*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📝 *الإعلان:* {_esc(item['title'])}\n"
                    f"🆔 *item\\_id:* `{item_id}`\n"
                    f"⚠️ *السبب:* {reason_lbl}\n"
                    f"📢 *المُبلِّغ:* {reporter} \\(`{user.id}`\\)\n"
                    f"📊 *إجمالي البلاغات:* {count}"
                )
                try:
                    await context.bot.send_message(
                        chat_id=int(fwd), text=msg, parse_mode=MD2,
                        reply_markup=KB.admin_report_kb("mkt", item_id)
                    )
                except Exception as e:
                    logger.error("Failed to send report: %s", e)
        await query.edit_message_text(C.MKT_REPORT_DONE, parse_mode=MD2,
                                      reply_markup=KB.avito_main_kb())

    # ── Admin: Avito approval & management ────────────────────────────────────
    elif d.startswith("mkt_app_"):
        item_id = d[len("mkt_app_"):]
        item    = MKT.get_item_by_id(item_id)
        if item:
            MKT.approve_item(item_id)
            await query.edit_message_reply_markup(reply_markup=KB.admin_active_mkt_kb(item_id))
            try:
                await context.bot.send_message(
                    chat_id=item["user_id"], text=C.MKT_APPROVED_NOTIFY,
                    parse_mode=MD2, reply_markup=KB.avito_main_kb()
                )
            except Exception:
                pass
            await _post_to_groups(context, _fmt_item(item, 1, 1), photo_id=item.get("photo_id"),
                                  contact_user_id=item["user_id"])
            _broadcast_teaser_bg(
                context,
                "🛒 *إعلان جديد في Avito Algeria\\!*\nهل تريد رؤية التفاصيل؟",
                f"avito_goto_{item_id}",
            )
        else:
            await query.answer("الإعلان غير موجود أو تم حذفه", show_alert=True)

    elif d.startswith("mkt_apo_"):
        item_id = d[len("mkt_apo_"):]
        item    = MKT.get_item_by_id(item_id)
        if item:
            MKT.approve_item(item_id)
            await query.edit_message_reply_markup(reply_markup=KB.admin_active_mkt_kb(item_id))
            try:
                await context.bot.send_message(
                    chat_id=item["user_id"], text=C.MKT_APPROVED_NOTIFY,
                    parse_mode=MD2, reply_markup=KB.avito_main_kb()
                )
            except Exception:
                pass
        else:
            await query.answer("الإعلان غير موجود أو تم حذفه", show_alert=True)

    elif d.startswith("mkt_rej_"):
        item_id = d[len("mkt_rej_"):]
        item    = MKT.get_item_by_id(item_id)
        if item:
            MKT.delete_item(item_id)
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=item["user_id"], text=C.MKT_REJECTED_NOTIFY, parse_mode=MD2
                )
            except Exception:
                pass
        else:
            await query.answer("الإعلان غير موجود", show_alert=True)

    elif d.startswith("mkt_admdel_"):
        item_id = d[len("mkt_admdel_"):]
        item    = MKT.get_item_by_id(item_id)
        if item:
            MKT.delete_item(item_id)
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                f"🗑️ تم حذف الإعلان `{item_id}` بنجاح\\.", parse_mode=MD2
            )
            try:
                await context.bot.send_message(
                    chat_id=item["user_id"],
                    text="🗑️ تم حذف إعلانك من *Avito Algeria* من قبل الإدارة\\.",
                    parse_mode=MD2
                )
            except Exception:
                pass
        else:
            await query.answer("الإعلان غير موجود", show_alert=True)

    elif d.startswith("adm_mkt_del_"):
        item_id = d[len("adm_mkt_del_"):]
        item    = MKT.get_item_by_id(item_id)
        if item:
            MKT.delete_item(item_id)
            # Refresh admin list
            items = MKT.get_all_items()
            if items:
                await query.edit_message_text(
                    f"🗑️ تم حذف `{item_id}`\\. إجمالي الإعلانات: {len(items)}",
                    parse_mode=MD2, reply_markup=KB.admin_mkt_list_kb(items)
                )
            else:
                await query.edit_message_text("📭 لا توجد إعلانات\\.", parse_mode=MD2,
                                              reply_markup=KB.admin_back_kb())
            try:
                await context.bot.send_message(
                    chat_id=item["user_id"],
                    text="🗑️ تم حذف إعلانك من *Avito Algeria* من قبل الإدارة\\.",
                    parse_mode=MD2
                )
            except Exception:
                pass
        else:
            await query.answer("الإعلان غير موجود", show_alert=True)

    elif d == "adm_mkt_list":
        items = MKT.get_all_items()
        if not items:
            await query.edit_message_text(
                "📭 *لا توجد إعلانات في السوق\\.*",
                parse_mode=MD2, reply_markup=KB.admin_back_kb()
            )
        else:
            await query.edit_message_text(
                f"🛒 *إعلانات Avito Algeria* \\({len(items)}\\)\n"
                "_اضغط على إعلان لحذفه_",
                parse_mode=MD2, reply_markup=KB.admin_mkt_list_kb(items)
            )

    elif d.startswith("rpt_ign_"):
        await query.edit_message_reply_markup(reply_markup=None)
        await query.answer("✅ تم تجاهل البلاغ")

    # ══════════════════════════════════════════════════════════════════════════
    # ROOMMATE
    # ══════════════════════════════════════════════════════════════════════════

    elif d == "rm_menu":
        await query.edit_message_text(C.RM_MAIN, parse_mode=MD2,
                                      reply_markup=KB.roommate_main_kb())

    elif d in ("rm_browse", "rm_back_browse"):
        f = _rm_filters(context)
        listings = MKT.filter_listings(f["city"], f["metro"], f["price"])
        if not listings:
            await query.edit_message_text(
                C.RM_EMPTY, parse_mode=MD2,
                reply_markup=KB.roommate_browse_kb(
                    0, 0, filter_city=f["city"],
                    filter_metro=f["metro"], filter_price=f["price"]
                ) if False else KB.roommate_main_kb()
            )
            # show main with filter hint
            await query.edit_message_text(
                C.RM_EMPTY, parse_mode=MD2, reply_markup=KB.roommate_main_kb()
            )
        else:
            idx = context.user_data.get("rm_browse_idx", 0)
            idx = max(0, min(idx, len(listings) - 1))
            lst = listings[idx]
            await query.edit_message_text(
                _fmt_listing(lst, idx + 1, len(listings)), parse_mode=MD2,
                reply_markup=KB.roommate_browse_kb(
                    idx, len(listings), poster_user_id=lst.get("user_id"),
                    filter_city=f["city"], filter_metro=f["metro"], filter_price=f["price"]
                )
            )

    elif d.startswith("rm_nav_"):
        idx = int(d[len("rm_nav_"):])
        f   = _rm_filters(context)
        context.user_data["rm_browse_idx"] = idx
        listings = MKT.filter_listings(f["city"], f["metro"], f["price"])
        if not listings:
            await query.edit_message_text(C.RM_EMPTY, parse_mode=MD2,
                                          reply_markup=KB.roommate_main_kb())
        else:
            idx = max(0, min(idx, len(listings) - 1))
            lst = listings[idx]
            await query.edit_message_text(
                _fmt_listing(lst, idx + 1, len(listings)), parse_mode=MD2,
                reply_markup=KB.roommate_browse_kb(
                    idx, len(listings), poster_user_id=lst.get("user_id"),
                    filter_city=f["city"], filter_metro=f["metro"], filter_price=f["price"]
                )
            )

    # ── Roommate filters ──────────────────────────────────────────────────────
    elif d == "rm_filt_city":
        f = _rm_filters(context)
        await query.edit_message_text(C.RM_FILTER_CITY, parse_mode=MD2,
                                      reply_markup=KB.rm_filter_city_kb(f["city"]))

    elif d == "rm_filt_metro":
        f = _rm_filters(context)
        await query.edit_message_text(C.RM_FILTER_METRO, parse_mode=MD2,
                                      reply_markup=KB.rm_filter_metro_kb(f["metro"]))

    elif d == "rm_filt_price":
        f = _rm_filters(context)
        await query.edit_message_text(C.RM_FILTER_PRICE, parse_mode=MD2,
                                      reply_markup=KB.rm_filter_price_kb(f["price"]))

    elif d.startswith("rm_fc_"):
        city_key = d[len("rm_fc_"):]
        f = _rm_filters(context)
        f["city"] = None if city_key == "all" else city_key
        context.user_data["rm_browse_idx"] = 0
        # Re-show listings
        listings = MKT.filter_listings(f["city"], f["metro"], f["price"])
        if not listings:
            await query.edit_message_text(C.RM_EMPTY, parse_mode=MD2,
                                          reply_markup=KB.roommate_main_kb())
        else:
            lst = listings[0]
            await query.edit_message_text(
                _fmt_listing(lst, 1, len(listings)), parse_mode=MD2,
                reply_markup=KB.roommate_browse_kb(
                    0, len(listings), poster_user_id=lst.get("user_id"),
                    filter_city=f["city"], filter_metro=f["metro"], filter_price=f["price"]
                )
            )

    elif d.startswith("rm_fm_"):
        metro = d[len("rm_fm_"):]
        f = _rm_filters(context)
        f["metro"] = None if metro == "all" else metro
        context.user_data["rm_browse_idx"] = 0
        listings = MKT.filter_listings(f["city"], f["metro"], f["price"])
        if not listings:
            await query.edit_message_text(C.RM_EMPTY, parse_mode=MD2,
                                          reply_markup=KB.roommate_main_kb())
        else:
            lst = listings[0]
            await query.edit_message_text(
                _fmt_listing(lst, 1, len(listings)), parse_mode=MD2,
                reply_markup=KB.roommate_browse_kb(
                    0, len(listings), poster_user_id=lst.get("user_id"),
                    filter_city=f["city"], filter_metro=f["metro"], filter_price=f["price"]
                )
            )

    elif d.startswith("rm_fp_"):
        sort = d[len("rm_fp_"):]
        f = _rm_filters(context)
        f["price"] = None if sort == "all" else sort
        context.user_data["rm_browse_idx"] = 0
        listings = MKT.filter_listings(f["city"], f["metro"], f["price"])
        if not listings:
            await query.edit_message_text(C.RM_EMPTY, parse_mode=MD2,
                                          reply_markup=KB.roommate_main_kb())
        else:
            lst = listings[0]
            await query.edit_message_text(
                _fmt_listing(lst, 1, len(listings)), parse_mode=MD2,
                reply_markup=KB.roommate_browse_kb(
                    0, len(listings), poster_user_id=lst.get("user_id"),
                    filter_city=f["city"], filter_metro=f["metro"], filter_price=f["price"]
                )
            )

    # ── Roommate report ───────────────────────────────────────────────────────
    elif d == "rm_rpt_btn":
        # Need current listing id from browse position
        f    = _rm_filters(context)
        idx  = context.user_data.get("rm_browse_idx", 0)
        listings = MKT.filter_listings(f["city"], f["metro"], f["price"])
        if not listings:
            await query.answer("الإعلان غير موجود", show_alert=True)
            return
        idx = max(0, min(idx, len(listings) - 1))
        listing_id = listings[idx]["id"]
        await query.edit_message_text(C.RM_REPORT_ASK, parse_mode=MD2,
                                      reply_markup=KB.rm_report_reason_kb(listing_id))

    elif d.startswith("rpt_rm_"):
        # rpt_rm_{reason}_{listing_id}
        parts      = d.split("_")
        reason     = parts[2]
        listing_id = parts[3]
        lst = MKT.get_listing_by_id(listing_id)
        if lst:
            count = MKT.report_listing(listing_id)
            user  = update.effective_user
            reasons = {"fake": "🤥 مزيف/احتيال", "spam": "🗑️ سبام", "inap": "🔞 غير لائق"}
            reason_lbl = reasons.get(reason, reason)
            reporter   = f"@{_esc(user.username)}" if user.username else _esc(user.first_name)
            from admin import ADMINS
            fwd = INQUIRY_CHAT or (str(ADMINS[0]) if ADMINS else None)
            if fwd:
                msg = (
                    "🚨 *بلاغ على إعلان سكن*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📍 *المدينة:* {_esc(lst['city'])}\n"
                    f"🆔 *listing\\_id:* `{listing_id}`\n"
                    f"⚠️ *السبب:* {reason_lbl}\n"
                    f"📢 *المُبلِّغ:* {reporter} \\(`{user.id}`\\)\n"
                    f"📊 *إجمالي البلاغات:* {count}"
                )
                try:
                    await context.bot.send_message(
                        chat_id=int(fwd), text=msg, parse_mode=MD2,
                        reply_markup=KB.admin_report_kb("rm", listing_id)
                    )
                except Exception as e:
                    logger.error("Failed to send rm report: %s", e)
        await query.edit_message_text(C.RM_REPORT_DONE, parse_mode=MD2,
                                      reply_markup=KB.roommate_main_kb())

    elif d.startswith("rm_goto_"):
        lid = d[len("rm_goto_"):]
        lst = MKT.get_listing_by_id(lid)
        if not lst or lst["status"] != "approved":
            await query.answer("الإعلان غير متوفر", show_alert=True)
            return
        listings = MKT.get_approved_listings()
        idx      = next((i for i, l in enumerate(listings) if l["id"] == lid), 0)
        await query.edit_message_text(
            _fmt_listing(lst, idx + 1, len(listings)), parse_mode=MD2,
            reply_markup=KB.roommate_browse_kb(idx, len(listings), poster_user_id=lst.get("user_id"))
        )

    # ── Roommate my listings ──────────────────────────────────────────────────
    elif d == "rm_mylist":
        user     = update.effective_user
        listings = MKT.get_user_listings(user.id)
        if not listings:
            await query.edit_message_text(C.RM_MY_EMPTY, parse_mode=MD2,
                                          reply_markup=KB.roommate_main_kb())
        else:
            await query.edit_message_text(
                f"📋 *إعلانات السكن* \\({len(listings)}\\)\n⏳ قيد المراجعة  •  ✅ منشور",
                parse_mode=MD2, reply_markup=KB.roommate_my_kb(listings)
            )

    elif d.startswith("rm_view_"):
        lid = d[len("rm_view_"):]
        lst = MKT.get_listing_by_id(lid)
        if not lst:
            await query.answer("الإعلان غير موجود", show_alert=True)
            return
        status = "✅ منشور" if lst["status"] == "approved" else "⏳ قيد المراجعة"
        rtype  = MKT.ROOMMATE_TYPES.get(lst["type"], lst["type"])
        rroom  = MKT.ROOM_TYPES.get(lst.get("room_type", ""), "")
        metro  = MKT.METRO_DISTANCES.get(lst.get("metro_distance", ""), "")
        text   = (
            f"🔖 *{_esc(rtype)}*\n"
            f"🛏️ {_esc(rroom)}\n"
            f"📍 {_esc(lst['city'])}  •  🚇 {_esc(metro)}\n"
            f"💰 {_esc(lst['price'])}\n"
            f"💬 {_esc(lst['description'])}\n"
            f"📊 الحالة: {status}"
        )
        await query.edit_message_text(text, parse_mode=MD2,
                                      reply_markup=KB.roommate_item_owner_kb(lid))

    elif d.startswith("rm_del_"):
        lid = d[len("rm_del_"):]
        await query.edit_message_text(
            "⚠️ *هل أنت متأكد من حذف هذا الإعلان؟*",
            parse_mode=MD2, reply_markup=KB.roommate_del_confirm_kb(lid)
        )

    elif d.startswith("rm_delcfm_"):
        lid = d[len("rm_delcfm_"):]
        MKT.delete_listing(lid)
        await query.edit_message_text(C.RM_DELETED, parse_mode=MD2,
                                      reply_markup=KB.roommate_main_kb())

    elif d == "rm_cancel_post":
        await query.edit_message_text(C.RM_CANCELLED, parse_mode=MD2,
                                      reply_markup=KB.roommate_main_kb())

    # ── Admin: Roommate approval & management ─────────────────────────────────
    elif d.startswith("rm_app_"):
        lid = d[len("rm_app_"):]
        lst = MKT.get_listing_by_id(lid)
        if lst:
            MKT.approve_listing(lid)
            await query.edit_message_reply_markup(reply_markup=KB.admin_active_rm_kb(lid))
            try:
                await context.bot.send_message(
                    chat_id=lst["user_id"], text=C.RM_APPROVED_NOTIFY,
                    parse_mode=MD2, reply_markup=KB.roommate_main_kb()
                )
            except Exception:
                pass
            await _post_to_groups(context, _fmt_listing(lst, 1, 1), contact_user_id=lst["user_id"])
            _broadcast_teaser_bg(
                context,
                "🏠 *إعلان سكن جديد\\!*\nهل تريد رؤية التفاصيل؟",
                f"rm_goto_{lid}",
            )
        else:
            await query.answer("الإعلان غير موجود أو تم حذفه", show_alert=True)

    elif d.startswith("rm_apo_"):
        lid = d[len("rm_apo_"):]
        lst = MKT.get_listing_by_id(lid)
        if lst:
            MKT.approve_listing(lid)
            await query.edit_message_reply_markup(reply_markup=KB.admin_active_rm_kb(lid))
            try:
                await context.bot.send_message(
                    chat_id=lst["user_id"], text=C.RM_APPROVED_NOTIFY,
                    parse_mode=MD2, reply_markup=KB.roommate_main_kb()
                )
            except Exception:
                pass
        else:
            await query.answer("الإعلان غير موجود أو تم حذفه", show_alert=True)

    elif d.startswith("rm_rej_"):
        lid = d[len("rm_rej_"):]
        lst = MKT.get_listing_by_id(lid)
        if lst:
            MKT.delete_listing(lid)
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=lst["user_id"], text=C.RM_REJECTED_NOTIFY, parse_mode=MD2
                )
            except Exception:
                pass
        else:
            await query.answer("الإعلان غير موجود", show_alert=True)

    elif d.startswith("rm_admdel_"):
        lid = d[len("rm_admdel_"):]
        lst = MKT.get_listing_by_id(lid)
        if lst:
            MKT.delete_listing(lid)
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                f"🗑️ تم حذف الإعلان `{lid}` بنجاح\\.", parse_mode=MD2
            )
            try:
                await context.bot.send_message(
                    chat_id=lst["user_id"],
                    text="🗑️ تم حذف إعلان السكن الخاص بك من قبل الإدارة\\.",
                    parse_mode=MD2
                )
            except Exception:
                pass
        else:
            await query.answer("الإعلان غير موجود", show_alert=True)

    elif d.startswith("adm_rm_del_"):
        lid = d[len("adm_rm_del_"):]
        lst = MKT.get_listing_by_id(lid)
        if lst:
            MKT.delete_listing(lid)
            listings = MKT.get_all_listings()
            if listings:
                await query.edit_message_text(
                    f"🗑️ تم حذف `{lid}`\\. إجمالي الإعلانات: {len(listings)}",
                    parse_mode=MD2, reply_markup=KB.admin_rm_list_kb(listings)
                )
            else:
                await query.edit_message_text("📭 لا توجد إعلانات\\.", parse_mode=MD2,
                                              reply_markup=KB.admin_back_kb())
            try:
                await context.bot.send_message(
                    chat_id=lst["user_id"],
                    text="🗑️ تم حذف إعلان السكن الخاص بك من قبل الإدارة\\.",
                    parse_mode=MD2
                )
            except Exception:
                pass
        else:
            await query.answer("الإعلان غير موجود", show_alert=True)

    elif d == "adm_rm_list":
        listings = MKT.get_all_listings()
        if not listings:
            await query.edit_message_text(
                "📭 *لا توجد إعلانات سكن\\.*",
                parse_mode=MD2, reply_markup=KB.admin_back_kb()
            )
        else:
            await query.edit_message_text(
                f"🏠 *إعلانات السكن* \\({len(listings)}\\)\n"
                "_اضغط على إعلان لحذفه_",
                parse_mode=MD2, reply_markup=KB.admin_rm_list_kb(listings)
            )

    elif d.startswith("rpt_ign_"):
        await query.edit_message_reply_markup(reply_markup=None)
        await query.answer("✅ تم تجاهل البلاغ")

    # ══════════════════════════════════════════════════════════════════════════
    # TRAVEL COMPANION — هبطلي ولا طلعلي معاك
    # ══════════════════════════════════════════════════════════════════════════

    elif d == "trv_menu":
        await query.edit_message_text(C.TRAVEL_MAIN, parse_mode=MD2,
                                      reply_markup=KB.travel_main_kb())

    elif d in ("trv_browse_alg_msk", "trv_browse_msk_alg"):
        route = "alg_to_msk" if d == "trv_browse_alg_msk" else "msk_to_alg"
        context.user_data["trv_browse_idx"] = 0
        await _show_trv_browse(query, route, 0)

    elif d.startswith("trv_bnav_"):
        rest = d[len("trv_bnav_"):]
        route_token, idx_str = rest.rsplit("_", 1)
        idx   = int(idx_str)
        route = _TRV_TOKEN_ROUTES.get(route_token, "alg_to_msk")
        context.user_data["trv_browse_idx"] = idx
        await _show_trv_browse(query, route, idx)

    elif d == "trv_mylist":
        user  = update.effective_user
        posts = TRV.get_user_posts(user.id)
        if not posts:
            await query.edit_message_text(C.TRV_MY_EMPTY, parse_mode=MD2,
                                          reply_markup=KB.travel_main_kb())
        else:
            await query.edit_message_text(
                f"📋 *رحلاتي* \\({len(posts)}\\)\n⏳ قيد المراجعة  •  ✅ منشور",
                parse_mode=MD2, reply_markup=KB.trv_my_kb(posts)
            )

    elif d.startswith("trv_view_"):
        post_id = d[len("trv_view_"):]
        post    = TRV.get_post_by_id(post_id)
        if not post:
            await query.answer("الرحلة غير موجودة", show_alert=True)
            return
        user        = update.effective_user
        is_owner    = post["user_id"] == user.id
        status_line = ("\n📊 الحالة: " + ("✅ منشور" if post["status"] == "approved" else "⏳ قيد المراجعة")) if is_owner else ""
        text        = _fmt_travel(post) + status_line
        kb          = KB.trv_item_owner_kb(post_id) if is_owner else KB.back_kb("trv_menu")
        await query.edit_message_text(text, parse_mode=MD2, reply_markup=kb)

    elif d.startswith("trv_del_"):
        post_id = d[len("trv_del_"):]
        await query.edit_message_text(
            "⚠️ *هل أنت متأكد من حذف هذه الرحلة؟*",
            parse_mode=MD2, reply_markup=KB.trv_del_confirm_kb(post_id)
        )

    elif d.startswith("trv_delcfm_"):
        post_id = d[len("trv_delcfm_"):]
        TRV.delete_post(post_id)
        await query.edit_message_text(C.TRV_DELETED, parse_mode=MD2,
                                      reply_markup=KB.travel_main_kb())

    elif d == "trv_cancel_post":
        await query.edit_message_text(C.TRV_CANCELLED, parse_mode=MD2,
                                      reply_markup=KB.travel_main_kb())

    # ── Admin: travel approval ───────────────────────────────────────────────
    elif d.startswith("trv_app_"):
        post_id = d[len("trv_app_"):]
        post    = TRV.get_post_by_id(post_id)
        if post:
            TRV.approve_post(post_id)
            await query.edit_message_reply_markup(reply_markup=KB.admin_active_trv_kb(post_id))
            try:
                await context.bot.send_message(
                    chat_id=post["user_id"], text=C.TRV_APPROVED_NOTIFY,
                    parse_mode=MD2, reply_markup=KB.travel_main_kb()
                )
            except Exception:
                pass
            await _post_to_groups(context, _fmt_travel(post), contact_user_id=post["user_id"])
            _broadcast_teaser_bg(
                context,
                "🧳 *إعلان سفر جديد\\!*\nشخص يحتاج هذا، تريد رؤية التفاصيل؟",
                f"trv_view_{post_id}",
            )
        else:
            await query.answer("الرحلة غير موجودة أو تم حذفها", show_alert=True)

    elif d.startswith("trv_apo_"):
        post_id = d[len("trv_apo_"):]
        post    = TRV.get_post_by_id(post_id)
        if post:
            TRV.approve_post(post_id)
            await query.edit_message_reply_markup(reply_markup=KB.admin_active_trv_kb(post_id))
            try:
                await context.bot.send_message(
                    chat_id=post["user_id"], text=C.TRV_APPROVED_NOTIFY,
                    parse_mode=MD2, reply_markup=KB.travel_main_kb()
                )
            except Exception:
                pass
        else:
            await query.answer("الرحلة غير موجودة أو تم حذفها", show_alert=True)

    elif d.startswith("trv_rej_"):
        post_id = d[len("trv_rej_"):]
        post    = TRV.get_post_by_id(post_id)
        if post:
            TRV.delete_post(post_id)
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=post["user_id"], text=C.TRV_REJECTED_NOTIFY, parse_mode=MD2
                )
            except Exception:
                pass
        else:
            await query.answer("الرحلة غير موجودة", show_alert=True)

    # ── Admin: community inquiry approval ────────────────────────────────────
    elif d.startswith("inq_app_"):
        inq_id = d[len("inq_app_"):]
        item   = INQS.get_by_id(inq_id)
        if item:
            INQS.approve_inquiry(inq_id)
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=item["user_id"], text=C.INQ_APPROVED_NOTIFY,
                    parse_mode=MD2, reply_markup=KB.back_to_main_kb()
                )
            except Exception:
                pass
            group_msg = (
                "👥 *استفسار من الجالية*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📛 *الاسم:* {_esc(item['name'])}\n"
                f"🎯 *الخدمة:* {_esc(item['service'])}\n"
                f"💬 *التفاصيل:* {_esc(item['notes'])}"
            )
            await _post_to_groups(context, group_msg, contact_user_id=item["user_id"])
        else:
            await query.answer("الاستفسار غير موجود أو تم حذفه", show_alert=True)

    elif d.startswith("inq_apo_"):
        inq_id = d[len("inq_apo_"):]
        item   = INQS.get_by_id(inq_id)
        if item:
            INQS.approve_inquiry(inq_id)
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=item["user_id"], text=C.INQ_APPROVED_NOTIFY,
                    parse_mode=MD2, reply_markup=KB.back_to_main_kb()
                )
            except Exception:
                pass
        else:
            await query.answer("الاستفسار غير موجود أو تم حذفه", show_alert=True)

    elif d.startswith("inq_rej_"):
        inq_id = d[len("inq_rej_"):]
        item   = INQS.get_by_id(inq_id)
        if item:
            INQS.delete_inquiry(inq_id)
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=item["user_id"], text=C.INQ_REJECTED_NOTIFY, parse_mode=MD2
                )
            except Exception:
                pass
        else:
            await query.answer("الاستفسار غير موجود", show_alert=True)

    # ── Admin: شرلوك الجزائري — report approval ────────────────────────────────
    elif d.startswith("scam_app_"):
        report_id = d[len("scam_app_"):]
        report = SCAM.get_report_by_id(report_id)
        if report:
            SCAM.approve_report(report_id)
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=report["reporter_user_id"], text=C.SCAM_APPROVED_NOTIFY, parse_mode=MD2,
                )
            except Exception:
                pass
        else:
            await query.answer("البلاغ غير موجود", show_alert=True)

    elif d.startswith("scam_rej_"):
        report_id = d[len("scam_rej_"):]
        report = SCAM.get_report_by_id(report_id)
        if report:
            SCAM.reject_report(report_id)
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=report["reporter_user_id"], text=C.SCAM_REJECTED_NOTIFY, parse_mode=MD2,
                )
            except Exception:
                pass
        else:
            await query.answer("البلاغ غير موجود", show_alert=True)

    # ── Admin: شرلوك الجزائري — full-detail access requests ────────────────────
    elif d.startswith("scam_acc_app_"):
        req_id = d[len("scam_acc_app_"):]
        req = SCAM.get_access_request_by_id(req_id)
        report = SCAM.get_report_by_id(req["report_id"]) if req else None
        if req and report:
            SCAM.approve_access(req_id)
            await query.edit_message_reply_markup(reply_markup=None)
            detail_msg = (
                "🔓 *تمت الموافقة على طلب الاطلاع الكامل*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📛 *الاسم:* {_esc(report['full_name'])} {_esc(report['surname'])}\n"
                f"🎂 *الميلاد:* {_esc(report['date_of_birth'])}\n"
                f"🆔 *Telegram ID:* {_esc(report['telegram_user_id'])}\n"
                f"📱 *الهاتف:* {_esc(report['phone'])}\n"
                f"🏦 *CCP:* {_esc(report['ccp'])}\n"
                f"💳 *البطاقة:* {_esc(report['card'])}\n"
                f"🛂 *جواز السفر:* {_esc(report['passport'])}\n"
                f"⚠️ *السبب:* {_esc(report['reason'])}"
            )
            try:
                await context.bot.send_message(
                    chat_id=req["requester_user_id"], text=detail_msg, parse_mode=MD2,
                )
            except Exception:
                pass
        else:
            await query.answer("الطلب غير موجود", show_alert=True)

    elif d.startswith("scam_acc_rej_"):
        req_id = d[len("scam_acc_rej_"):]
        req = SCAM.get_access_request_by_id(req_id)
        if req:
            SCAM.reject_access(req_id)
            await query.edit_message_reply_markup(reply_markup=None)
            try:
                await context.bot.send_message(
                    chat_id=req["requester_user_id"], text=C.SCAM_ACCESS_REJECTED_NOTIFY, parse_mode=MD2,
                )
            except Exception:
                pass
        else:
            await query.answer("الطلب غير موجود", show_alert=True)

    # ── Unknown ───────────────────────────────────────────────────────────────
    else:
        logger.warning("Unhandled callback: %s", d)
        await query.answer("هذا الزر غير معرّف", show_alert=True)


# ══════════════════════════════════════════════════════════════════════════════
# INQUIRY CONVERSATION
# ══════════════════════════════════════════════════════════════════════════════

async def inq_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _conv_edit(query, context, C.INQ_TARGET, KB.inq_target_kb())
    return _INQ_TARGET


async def inq_target_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["inq_target"] = "community" if query.data == "inq_target_community" else "admin"
    await _conv_edit(query, context, C.INQ_START, KB.inq_cancel_kb())
    return _INQ_PHONE


async def inq_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["inq_name"] = update.message.text
    await _conv_reply(update, context, C.INQ_PHONE, KB.inq_cancel_kb())
    return _INQ_SERVICE


async def inq_service_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["inq_phone"] = update.message.text
    await _conv_reply(update, context, C.INQ_SERVICE, KB.inquiry_service_kb())
    return _INQ_NOTES


async def inq_service_btn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    labels = {
        "inq_svc_registration": "🎓 تسجيل جامعي",
        "inq_svc_translation":  "📑 ترجمة وثائق",
        "inq_svc_consultation": "🗣️ استشارة عامة",
        "inq_svc_other":        "❓ أخرى",
    }
    context.user_data["inq_service"] = labels.get(query.data, query.data)
    await _conv_edit(query, context, C.INQ_NOTES, KB.inq_cancel_kb())
    return _INQ_NOTES


async def inq_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    notes = update.message.text
    if notes.strip() == ".":
        notes = "—"
    context.user_data["inq_notes"] = notes
    is_community = context.user_data.get("inq_target") == "community"
    await _forward_inquiry(update, context)
    done_text = C.INQ_DONE_COMMUNITY if is_community else C.INQ_DONE
    await _conv_reply(update, context, done_text, KB.back_to_main_kb())
    _inq_cleanup(context)
    return ConversationHandler.END


async def inq_cancel_btn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _conv_edit(query, context, C.INQ_CANCEL, KB.back_to_main_kb())
    _inq_cleanup(context)
    return ConversationHandler.END


async def inq_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _conv_reply(update, context, C.INQ_CANCEL, KB.back_to_main_kb())
    _inq_cleanup(context)
    return ConversationHandler.END


async def _forward_inquiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ud   = context.user_data
    username_part = f"@{_esc(user.username)}" if user.username else "—"

    if ud.get("inq_target") == "community":
        item = INQS.add_inquiry(
            user_id=user.id, username=user.username, first_name=user.first_name,
            name=ud.get("inq_name", ""), phone=ud.get("inq_phone", ""),
            service=ud.get("inq_service", ""), notes=ud.get("inq_notes", ""),
        )
        msg = (
            "👥 *استفسار جديد — موجّه للجالية*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *المرسل:* {_esc(user.first_name)} \\({username_part}\\)\n"
            f"🆔 *ID:* `{user.id}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 *الاسم:* {_esc(item['name'])}\n"
            f"📱 *الهاتف:* {_esc(item['phone'])}\n"
            f"🎯 *الخدمة:* {_esc(item['service'])}\n"
            f"💬 *ملاحظات:* {_esc(item['notes'])}\n"
            f"🆔 *inq\\_id:* `{item['id']}`"
        )
        kb = KB.admin_approve_inq_kb(item["id"])
    else:
        msg = (
            "📥 *استفسار جديد — موجّه للإدارة*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *المرسل:* {_esc(user.first_name)} \\({username_part}\\)\n"
            f"🆔 *ID:* `{user.id}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 *الاسم:* {_esc(ud.get('inq_name'))}\n"
            f"📱 *الهاتف:* {_esc(ud.get('inq_phone'))}\n"
            f"🎯 *الخدمة:* {_esc(ud.get('inq_service'))}\n"
            f"💬 *ملاحظات:* {_esc(ud.get('inq_notes'))}"
        )
        kb = None

    from admin import ADMINS
    fwd = INQUIRY_CHAT or (str(ADMINS[0]) if ADMINS else None)
    if fwd:
        try:
            await context.bot.send_message(chat_id=int(fwd), text=msg, parse_mode=MD2, reply_markup=kb)
        except Exception as e:
            logger.error("Failed to forward inquiry: %s", e)


def _inq_cleanup(context) -> None:
    for k in ("inq_target", "inq_name", "inq_phone", "inq_service", "inq_notes"):
        context.user_data.pop(k, None)


# ══════════════════════════════════════════════════════════════════════════════
# MARKETPLACE CONVERSATION — post a new item
# ══════════════════════════════════════════════════════════════════════════════

async def mkt_post_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _conv_edit(query, context, C.MKT_POST_CAT, KB.avito_post_cat_kb())
    return _MKT_CAT


async def mkt_choose_cat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["mkt_cat"] = query.data.replace("avito_pcat_", "")
    await _conv_edit(query, context, C.MKT_POST_TITLE, KB.avito_cancel_kb())
    return _MKT_TITLE


async def mkt_get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["mkt_title"] = update.message.text.strip()
    await _conv_reply(update, context, C.MKT_POST_PRICE, KB.avito_cancel_kb())
    return _MKT_PRICE


async def mkt_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["mkt_price"] = update.message.text.strip()
    await _conv_reply(update, context, C.MKT_POST_CITY, KB.avito_cancel_kb())
    return _MKT_CITY


async def mkt_get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["mkt_city"] = update.message.text.strip()
    await _conv_reply(update, context, C.MKT_POST_DESC, KB.avito_cancel_kb())
    return _MKT_DESC


async def mkt_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["mkt_desc"] = update.message.text.strip()
    await _conv_reply(update, context, C.MKT_POST_PHOTO, KB.avito_cancel_kb())
    return _MKT_PHOTO


async def mkt_get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        try:
            await update.message.delete()
        except Exception:
            pass
        await _conv_reply(update, context, C.MKT_POST_PHOTO_RETRY, KB.avito_cancel_kb())
        return _MKT_PHOTO
    context.user_data["mkt_photo"] = update.message.photo[-1].file_id
    try:
        await update.message.delete()
    except Exception:
        pass
    await _mkt_submit(update, context, via_callback=False)
    return ConversationHandler.END


async def _mkt_submit(update: Update, context: ContextTypes.DEFAULT_TYPE,
                      via_callback: bool = False) -> None:
    user = update.effective_user
    ud   = context.user_data
    item = MKT.add_item(
        user_id=user.id, username=user.username, first_name=user.first_name,
        category=ud.get("mkt_cat", "other"), title=ud.get("mkt_title", ""),
        price=ud.get("mkt_price", ""), city=ud.get("mkt_city", ""),
        description=ud.get("mkt_desc", ""), photo_id=ud.get("mkt_photo"),
    )
    if via_callback:
        await _conv_edit(update.callback_query, context,
                         C.MKT_POST_PENDING, KB.back_to_main_kb())
    else:
        chat_id  = update.effective_chat.id
        prev_id  = context.user_data.get("conv_msg_id")
        if prev_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=prev_id,
                    text=C.MKT_POST_PENDING, parse_mode=MD2,
                    reply_markup=KB.back_to_main_kb(),
                )
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id, text=C.MKT_POST_PENDING,
                    parse_mode=MD2, reply_markup=KB.back_to_main_kb(),
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id, text=C.MKT_POST_PENDING,
                parse_mode=MD2, reply_markup=KB.back_to_main_kb(),
            )
    await _send_item_to_admin(context, item)
    _mkt_cleanup(context)


async def mkt_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await _conv_edit(update.callback_query, context,
                         C.MKT_CANCELLED, KB.avito_main_kb())
    else:
        await _conv_reply(update, context, C.MKT_CANCELLED, KB.avito_main_kb())
    _mkt_cleanup(context)
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# ROOMMATE CONVERSATION — post a new listing
# ══════════════════════════════════════════════════════════════════════════════

async def rm_post_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _conv_edit(query, context, C.RM_POST_TYPE, KB.roommate_type_kb())
    return _RM_TYPE


async def rm_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["rm_type"] = "need" if query.data == "rm_type_need" else "have"
    await _conv_edit(query, context, C.RM_POST_ROOM_TYPE, KB.roommate_room_type_kb())
    return _RM_ROOM_TYPE


async def rm_room_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["rm_room_type"] = query.data.replace("rm_rtype_", "")
    await _conv_edit(query, context, C.RM_POST_CITY, KB.roommate_city_kb())
    return _RM_CITY_CHOICE


async def rm_city_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    city_key = query.data.replace("rm_city_", "")
    if city_key == "other":
        await _conv_edit(query, context, C.RM_POST_CITY_TEXT, KB.roommate_cancel_kb())
        return _RM_CITY_TEXT
    else:
        context.user_data["rm_city"]     = MKT.RUSSIAN_CITIES.get(city_key, city_key)
        context.user_data["rm_city_key"] = city_key
        await _conv_edit(query, context, C.RM_POST_PRICE, KB.roommate_cancel_kb())
        return _RM_PRICE


async def rm_city_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["rm_city"]     = update.message.text.strip()
    context.user_data["rm_city_key"] = "other"
    await _conv_reply(update, context, C.RM_POST_PRICE, KB.roommate_cancel_kb())
    return _RM_PRICE


async def rm_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["rm_price"] = update.message.text.strip()
    await _conv_reply(update, context, C.RM_POST_METRO, KB.roommate_metro_kb())
    return _RM_METRO


async def rm_metro_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["rm_metro"] = query.data.replace("rm_metro_", "")
    await _conv_edit(query, context, C.RM_POST_DESC, KB.roommate_cancel_kb())
    return _RM_DESC


async def rm_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    ud   = context.user_data
    lst  = MKT.add_listing(
        user_id=user.id, username=user.username, first_name=user.first_name,
        listing_type=ud.get("rm_type", "need"),
        room_type=ud.get("rm_room_type", "room1"),
        city=ud.get("rm_city", ""),
        city_key=ud.get("rm_city_key", "other"),
        price=ud.get("rm_price", ""),
        metro_distance=ud.get("rm_metro", "far"),
        description=update.message.text.strip(),
    )
    await _conv_reply(update, context, C.RM_POST_PENDING, KB.back_to_main_kb())
    await _send_listing_to_admin(context, lst)
    _rm_cleanup(context)
    return ConversationHandler.END


async def rm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await _conv_edit(update.callback_query, context,
                         C.RM_CANCELLED, KB.roommate_main_kb())
    else:
        await _conv_reply(update, context, C.RM_CANCELLED, KB.roommate_main_kb())
    _rm_cleanup(context)
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# TRAVEL CONVERSATION — post a new travel companion request
# ══════════════════════════════════════════════════════════════════════════════

async def trv_post_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "trv_post_choose":
        await _conv_edit(query, context, C.TRV_POST_ROUTE, KB.trv_direction_kb())
        return _TRV_ROUTE
    context.user_data["trv_route"] = "alg_to_msk" if data == "trv_post_alg_msk" else "msk_to_alg"
    await _conv_edit(query, context, C.TRV_POST_DATE, KB.trv_cancel_kb())
    return _TRV_DATE


async def trv_route_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["trv_route"] = "alg_to_msk" if query.data == "trv_dir_alg_msk" else "msk_to_alg"
    await _conv_edit(query, context, C.TRV_POST_DATE, KB.trv_cancel_kb())
    return _TRV_DATE


async def trv_get_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_str = update.message.text.strip()
    if not TRV.parse_date(date_str):
        await _conv_reply(update, context, C.TRV_POST_DATE_RETRY, KB.trv_cancel_kb())
        return _TRV_DATE
    context.user_data["trv_date"] = date_str
    await _conv_reply(update, context, C.TRV_POST_FLIGHT, KB.trv_skip_flight_kb())
    return _TRV_FLIGHT


async def trv_get_flight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["trv_flight"] = update.message.text.strip()
    await _conv_reply(update, context, C.TRV_POST_CITY, KB.trv_cancel_kb())
    return _TRV_CITY


async def trv_skip_flight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["trv_flight"] = "—"
    await _conv_edit(query, context, C.TRV_POST_CITY, KB.trv_cancel_kb())
    return _TRV_CITY


async def trv_get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["trv_city"] = update.message.text.strip()
    await _conv_reply(update, context, C.TRV_POST_CONTACT, KB.trv_cancel_kb())
    return _TRV_CONTACT


async def trv_get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["trv_contact"] = update.message.text.strip()
    await _conv_reply(update, context, C.TRV_POST_NOTE, KB.trv_cancel_kb())
    return _TRV_NOTE


async def trv_get_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    note = update.message.text.strip()
    if note == "-":
        note = "—"
    user = update.effective_user
    ud   = context.user_data
    post = TRV.add_post(
        user_id=user.id, username=user.username, first_name=user.first_name,
        route=ud.get("trv_route", "alg_to_msk"), date=ud.get("trv_date", ""),
        flight=ud.get("trv_flight", "—"), city=ud.get("trv_city", ""),
        contact=ud.get("trv_contact", ""), note=note,
    )
    await _conv_reply(update, context, C.TRV_POST_PENDING, KB.back_to_main_kb())
    await _send_travel_to_admin(context, post)
    _trv_cleanup(context)
    return ConversationHandler.END


async def trv_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await _conv_edit(update.callback_query, context, C.TRV_CANCELLED, KB.travel_main_kb())
    else:
        await _conv_reply(update, context, C.TRV_CANCELLED, KB.travel_main_kb())
    _trv_cleanup(context)
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# شرلوك الجزائري — CHECK conversation
# ══════════════════════════════════════════════════════════════════════════════

def _fmt_scam_result(r: dict) -> str:
    return (
        f"⚠️ *{_esc(r['full_name'])} {_esc(r['surname'])}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎂 *الميلاد:* {_esc(r.get('date_of_birth') or '—')}\n"
        f"🆔 *Telegram ID:* {_ltr(r.get('telegram_user_id') or '—')}\n"
        f"📱 *الهاتف:* {_ltr(r.get('phone') or '—')}\n"
        f"🏦 *CCP:* {_ltr(r.get('ccp') or '—')}\n"
        f"🔑 *المفتاح/RIP:* {_ltr(r.get('cle_rip') or '—')}\n"
        f"💳 *البطاقة:* {_ltr(r.get('card') or '—')}\n"
        f"🛂 *الجواز:* {_ltr(r.get('passport') or '—')}\n"
        f"⚠️ *السبب:* {_esc(r['reason'])}\n\n"
        "_للاطلاع على التفاصيل الكاملة \\(غير مموّهة\\)، استخدم التطبيق المصغر وزر «طلب رؤية التفاصيل الكاملة»\\._"
    )


def _md2_link(text: str, url: str) -> str:
    esc_url = url.replace("\\", "\\\\").replace(")", "\\)")
    return f"[{_esc(text)}]({esc_url})"


def _fmt_guarantor_result(g: dict) -> str:
    contact_line = f"💬 *التواصل:* {_md2_link(g.get('contact_label') or g['contact'], g['contact'])}" if g.get("contact") else ""
    return (
        f"✅ *هذا شخص ضامن موثوق*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 *الاسم:* {_esc(g['name'])}\n"
        f"👪 *اللقب:* {_esc(g['surname'])}\n"
        f"🇷🇺 *بالروسية:* {_esc(g.get('full_name_ru') or '—')}\n"
        f"📱 *الهاتف:* {_ltr(g['phone'])}\n"
        f"{contact_line}"
    )


async def scam_check_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _conv_edit(query, context, C.SCAM_CHECK_PROMPT, KB.scam_cancel_kb())
    return _SCAM_CHECK_QUERY


async def scam_check_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from admin import is_admin
    user = update.effective_user
    text = update.message.text.strip()
    if not is_admin(user.id) and not SCAM.check_and_bump_quota(user.id):
        await _conv_reply(update, context, C.SCAM_CHECK_QUOTA, KB.scam_menu_kb())
        return ConversationHandler.END
    res = SCAM.smart_search(text)
    if res["mode"] == "none":
        await _conv_reply(update, context, C.SCAM_CHECK_NONE, KB.scam_menu_kb())
        return ConversationHandler.END
    if res["mode"] == "guarantor":
        await _conv_reply(update, context, _fmt_guarantor_result(res["results"][0]), KB.scam_menu_kb())
        return ConversationHandler.END
    if res["mode"] == "candidates":
        context.user_data["scam_candidates"] = res["results"]
        lines = "\n".join(
            f"{i + 1}\\. {_esc(c['full_name'])} {_esc(c['surname'])}" for i, c in enumerate(res["results"])
        )
        await _conv_reply(update, context, f"{C.SCAM_CHECK_PICK_PROMPT}\n\n{lines}", KB.scam_cancel_kb())
        return _SCAM_CHECK_PICK
    await _conv_reply(update, context, _fmt_scam_result(res["results"][0]), KB.scam_menu_kb())
    return ConversationHandler.END


async def scam_check_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    candidates = context.user_data.get("scam_candidates", [])
    if not text.isdigit() or not (1 <= int(text) <= len(candidates)):
        await _conv_reply(update, context, C.SCAM_CHECK_PICK_RETRY, KB.scam_cancel_kb())
        return _SCAM_CHECK_PICK
    chosen = candidates[int(text) - 1]
    detail = SCAM.get_report_detail(chosen["id"])
    msg = _fmt_scam_result(detail) if detail else C.SCAM_CHECK_NONE
    context.user_data.pop("scam_candidates", None)
    await _conv_reply(update, context, msg, KB.scam_menu_kb())
    return ConversationHandler.END


async def scam_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await _conv_edit(update.callback_query, context, C.SCAM_CANCELLED, KB.scam_menu_kb())
    else:
        await _conv_reply(update, context, C.SCAM_CANCELLED, KB.scam_menu_kb())
    for key in ("scam_step", "scam_candidates", "scam_full_name", "scam_reason", "scam_photo",
                *(f"scam_{k}" for k, _ in SCAM_OPTIONAL_STEPS)):
        context.user_data.pop(key, None)
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# شرلوك الجزائري — REPORT conversation
# ══════════════════════════════════════════════════════════════════════════════

async def scam_report_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _conv_edit(query, context, C.SCAM_REPORT_NAME, KB.scam_cancel_kb())
    return _SCAM_NAME


async def _scam_prompt_optional(update, context, via_callback: bool) -> None:
    idx = context.user_data["scam_step"]
    _, content_key = SCAM_OPTIONAL_STEPS[idx]
    text = getattr(C, content_key)
    if via_callback:
        await _conv_edit(update.callback_query, context, text, KB.scam_skip_kb())
    else:
        await _conv_reply(update, context, text, KB.scam_skip_kb())


async def scam_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["scam_full_name"] = update.message.text.strip()
    context.user_data["scam_step"] = 0
    await _scam_prompt_optional(update, context, via_callback=False)
    return _SCAM_OPTIONAL


async def _scam_advance_optional(update: Update, context: ContextTypes.DEFAULT_TYPE, via_callback: bool) -> int:
    context.user_data["scam_step"] += 1
    if context.user_data["scam_step"] >= len(SCAM_OPTIONAL_STEPS):
        if via_callback:
            await _conv_edit(update.callback_query, context, C.SCAM_REPORT_REASON, KB.scam_cancel_kb())
        else:
            await _conv_reply(update, context, C.SCAM_REPORT_REASON, KB.scam_cancel_kb())
        return _SCAM_REASON
    await _scam_prompt_optional(update, context, via_callback=via_callback)
    return _SCAM_OPTIONAL


async def scam_get_optional(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    idx = context.user_data["scam_step"]
    key, _ = SCAM_OPTIONAL_STEPS[idx]
    context.user_data[f"scam_{key}"] = update.message.text.strip()
    return await _scam_advance_optional(update, context, via_callback=False)


async def scam_skip_optional(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    idx = context.user_data["scam_step"]
    key, _ = SCAM_OPTIONAL_STEPS[idx]
    context.user_data[f"scam_{key}"] = ""
    return await _scam_advance_optional(update, context, via_callback=True)


async def scam_get_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["scam_reason"] = update.message.text.strip()
    await _conv_reply(update, context, C.SCAM_REPORT_PHOTO, KB.scam_skip_photo_kb())
    return _SCAM_PHOTO


async def scam_get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["scam_photo"] = update.message.photo[-1].file_id if update.message.photo else None
    try:
        await update.message.delete()
    except Exception:
        pass
    await _scam_submit(update, context, via_callback=False)
    return ConversationHandler.END


async def scam_skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["scam_photo"] = None
    await _scam_submit(update, context, via_callback=True)
    return ConversationHandler.END


async def _scam_submit(update: Update, context: ContextTypes.DEFAULT_TYPE, via_callback: bool) -> None:
    user = update.effective_user
    ud = context.user_data
    report = SCAM.add_report(
        reporter_user_id=user.id, reporter_username=user.username, reporter_first_name=user.first_name,
        full_name=ud.get("scam_full_name", ""), surname=ud.get("scam_surname", ""),
        full_name_ru=ud.get("scam_full_name_ru", ""),
        date_of_birth=ud.get("scam_date_of_birth", ""), telegram_user_id=ud.get("scam_telegram_user_id", ""),
        phone=ud.get("scam_phone", ""), ccp=ud.get("scam_ccp", ""), cle_rip=ud.get("scam_cle_rip", ""),
        card=ud.get("scam_card", ""),
        passport=ud.get("scam_passport", ""), reason=ud.get("scam_reason", ""),
        photos=[ud["scam_photo"]] if ud.get("scam_photo") else [],
    )
    if via_callback:
        await _conv_edit(update.callback_query, context, C.SCAM_REPORT_PENDING, KB.back_to_main_kb())
    else:
        chat_id = update.effective_chat.id
        prev_id = context.user_data.get("conv_msg_id")
        if prev_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=prev_id,
                    text=C.SCAM_REPORT_PENDING, parse_mode=MD2, reply_markup=KB.back_to_main_kb(),
                )
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id, text=C.SCAM_REPORT_PENDING, parse_mode=MD2, reply_markup=KB.back_to_main_kb(),
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id, text=C.SCAM_REPORT_PENDING, parse_mode=MD2, reply_markup=KB.back_to_main_kb(),
            )
    await _send_scam_report_to_admin(context, report)
    for key in ("scam_step", "scam_full_name", "scam_reason", "scam_photo",
                *(f"scam_{k}" for k, _ in SCAM_OPTIONAL_STEPS)):
        context.user_data.pop(key, None)


async def _send_scam_report_to_admin(context, report: dict) -> None:
    from admin import ADMINS
    fwd = INQUIRY_CHAT or (str(ADMINS[0]) if ADMINS else None)
    if not fwd:
        return
    reporter = f"@{_esc(report['reporter_username'])}" if report.get("reporter_username") else _esc(report.get("reporter_first_name"))
    msg = (
        "🕵️ *بلاغ جديد — شرلوك الجزائري*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *المُبلِّغ:* {_esc(report['reporter_first_name'])} \\({reporter}\\)\n"
        f"🆔 *ID:* `{report['reporter_user_id']}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 *الاسم الكامل:* {_esc(report['full_name'])}\n"
        f"👪 *اللقب:* {_esc(report['surname'] or '—')}\n"
        f"🇷🇺 *الاسم بالروسية:* {_esc(report.get('full_name_ru') or '—')}\n"
        f"🎂 *تاريخ الميلاد:* {_esc(report['date_of_birth'] or '—')}\n"
        f"🆔 *Telegram ID:* {_ltr(report['telegram_user_id'] or '—')}\n"
        f"📱 *الهاتف:* {_ltr(report['phone'] or '—')}\n"
        f"🏦 *CCP:* {_ltr(report['ccp'] or '—')}\n"
        f"🔑 *المفتاح/RIP:* {_ltr(report.get('cle_rip') or '—')}\n"
        f"💳 *البطاقة:* {_ltr(report['card'] or '—')}\n"
        f"🛂 *جواز السفر:* {_ltr(report['passport'] or '—')}\n"
        f"⚠️ *السبب:* {_esc(report['reason'])}\n"
        f"🆔 *report\\_id:* `{report['id']}`"
    )
    kb = KB.admin_approve_scam_kb(report["id"])
    try:
        if report.get("photos"):
            await context.bot.send_photo(chat_id=int(fwd), photo=report["photos"][0],
                                         caption=msg, parse_mode=MD2, reply_markup=kb)
        else:
            await context.bot.send_message(chat_id=int(fwd), text=msg, parse_mode=MD2, reply_markup=kb)
    except Exception as e:
        logger.error("Failed to send scam report to admin: %s", e)


# ══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLER
# ══════════════════════════════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Update %s caused error: %s", update, context.error, exc_info=context.error)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

async def _travel_maintenance_loop() -> None:
    """Runs once a day in the background — archives expired travel posts and
    permanently deletes ones past the 6-month retention window."""
    while True:
        try:
            TRV.run_maintenance()
        except Exception as e:
            logger.error("Travel maintenance failed: %s", e)
        await asyncio.sleep(86400)


async def _post_init(app) -> None:
    TRV.run_maintenance()
    asyncio.create_task(_travel_maintenance_loop())


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set.")

    from telegram.request import HTTPXRequest
    proxy   = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or None
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=60, write_timeout=60, connect_timeout=30,
        proxy=proxy,
    )
    app = ApplicationBuilder().token(BOT_TOKEN).request(request).post_init(_post_init).build()
    app.bot_data["users"] = load_users()

    # ── Inquiry ConversationHandler ───────────────────────────────────────────
    _inq_cxl = CallbackQueryHandler(inq_cancel_btn, pattern="^inq_cancel$")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        inquiry_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(inq_start, pattern="^inquiry_start$")],
            states={
                _INQ_TARGET:  [_inq_cxl, CallbackQueryHandler(inq_target_chosen, pattern="^inq_target_")],
                _INQ_PHONE:   [_inq_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, inq_phone)],
                _INQ_SERVICE: [_inq_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, inq_service_text)],
                _INQ_NOTES:   [_inq_cxl, CallbackQueryHandler(inq_service_btn, pattern="^inq_svc_"),
                               MessageHandler(filters.TEXT & ~filters.COMMAND, inq_notes)],
            },
            fallbacks=[CommandHandler("cancel", inq_cancel)],
            per_user=True, per_chat=True,
        )

    # ── Marketplace ConversationHandler ───────────────────────────────────────
    _mkt_cxl = CallbackQueryHandler(mkt_cancel, pattern="^avito_cancel_post$")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        marketplace_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(mkt_post_start, pattern="^avito_post$")],
            states={
                _MKT_CAT:   [_mkt_cxl, CallbackQueryHandler(mkt_choose_cat, pattern="^avito_pcat_")],
                _MKT_TITLE: [_mkt_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, mkt_get_title)],
                _MKT_PRICE: [_mkt_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, mkt_get_price)],
                _MKT_CITY:  [_mkt_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, mkt_get_city)],
                _MKT_DESC:  [_mkt_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, mkt_get_desc)],
                _MKT_PHOTO: [_mkt_cxl,
                             MessageHandler(filters.PHOTO, mkt_get_photo),
                             MessageHandler(filters.TEXT & ~filters.COMMAND, mkt_get_photo)],
            },
            fallbacks=[CommandHandler("cancel", mkt_cancel)],
            per_user=True, per_chat=True,
        )

    # ── Roommate ConversationHandler ──────────────────────────────────────────
    _rm_cxl = CallbackQueryHandler(rm_cancel, pattern="^rm_cancel_post$")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        roommate_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(rm_post_start, pattern="^rm_post$")],
            states={
                _RM_TYPE:       [_rm_cxl, CallbackQueryHandler(rm_type_chosen,      pattern="^rm_type_")],
                _RM_ROOM_TYPE:  [_rm_cxl, CallbackQueryHandler(rm_room_type_chosen, pattern="^rm_rtype_")],
                _RM_CITY_CHOICE:[_rm_cxl, CallbackQueryHandler(rm_city_chosen,      pattern="^rm_city_")],
                _RM_CITY_TEXT:  [_rm_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, rm_city_text)],
                _RM_PRICE:      [_rm_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, rm_get_price)],
                _RM_METRO:      [_rm_cxl, CallbackQueryHandler(rm_metro_chosen,     pattern="^rm_metro_")],
                _RM_DESC:       [_rm_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, rm_get_desc)],
            },
            fallbacks=[CommandHandler("cancel", rm_cancel)],
            per_user=True, per_chat=True,
        )

    # ── Travel ConversationHandler ─────────────────────────────────────────────
    _trv_cxl = CallbackQueryHandler(trv_cancel, pattern="^trv_cancel_post$")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        travel_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(trv_post_start, pattern="^trv_post_(choose|msk_alg|alg_msk)$")],
            states={
                _TRV_ROUTE:   [_trv_cxl, CallbackQueryHandler(trv_route_chosen, pattern="^trv_dir_")],
                _TRV_DATE:    [_trv_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, trv_get_date)],
                _TRV_FLIGHT:  [_trv_cxl, CallbackQueryHandler(trv_skip_flight, pattern="^trv_skip_flight$"),
                               MessageHandler(filters.TEXT & ~filters.COMMAND, trv_get_flight)],
                _TRV_CITY:    [_trv_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, trv_get_city)],
                _TRV_CONTACT: [_trv_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, trv_get_contact)],
                _TRV_NOTE:    [_trv_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, trv_get_note)],
            },
            fallbacks=[CommandHandler("cancel", trv_cancel)],
            per_user=True, per_chat=True,
        )

    # ── شرلوك الجزائري: check ConversationHandler ─────────────────────────────
    _scam_cxl = CallbackQueryHandler(scam_cancel, pattern="^scam_cancel_post$")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        scam_check_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(scam_check_start, pattern="^scam_check_start$")],
            states={
                _SCAM_CHECK_QUERY: [_scam_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, scam_check_query)],
                _SCAM_CHECK_PICK:  [_scam_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, scam_check_pick)],
            },
            fallbacks=[CommandHandler("cancel", scam_cancel)],
            per_user=True, per_chat=True,
        )

    # ── شرلوك الجزائري: report ConversationHandler ────────────────────────────
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        scam_report_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(scam_report_start, pattern="^scam_report_start$")],
            states={
                _SCAM_NAME:     [_scam_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, scam_get_name)],
                _SCAM_OPTIONAL: [_scam_cxl, CallbackQueryHandler(scam_skip_optional, pattern="^scam_skip_field$"),
                                 MessageHandler(filters.TEXT & ~filters.COMMAND, scam_get_optional)],
                _SCAM_REASON:   [_scam_cxl, MessageHandler(filters.TEXT & ~filters.COMMAND, scam_get_reason)],
                _SCAM_PHOTO:    [_scam_cxl, CallbackQueryHandler(scam_skip_photo, pattern="^scam_skip_photo$"),
                                 MessageHandler(filters.PHOTO, scam_get_photo)],
            },
            fallbacks=[CommandHandler("cancel", scam_cancel)],
            per_user=True, per_chat=True,
        )

    # ── Register handlers (order matters!) ────────────────────────────────────
    for h in get_admin_handlers():
        app.add_handler(h)

    app.add_handler(marketplace_conv)
    app.add_handler(roommate_conv)
    app.add_handler(travel_conv)
    app.add_handler(inquiry_conv)
    app.add_handler(scam_check_conv)
    app.add_handler(scam_report_conv)

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("help",    help_cmd))
    app.add_handler(CommandHandler("about",   about_cmd))
    app.add_handler(CommandHandler("contact", contact_cmd))
    app.add_handler(CommandHandler("website", website_cmd))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)

    logger.info("KADER DZ Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    import asyncio
    import sys

    PID_FILE = os.path.join(os.path.dirname(__file__), "bot.pid")
    pid = os.getpid()

    def _stale_pid(p: str) -> bool:
        try:
            old = int(open(p).read().strip())
            if old == pid:
                return True
            import signal
            os.kill(old, 0)
            return False
        except (OSError, ValueError):
            return True

    if os.path.exists(PID_FILE) and not _stale_pid(PID_FILE):
        logger.error("Another bot instance is already running. Exiting.")
        sys.exit(1)

    with open(PID_FILE, "w") as f:
        f.write(str(pid))

    try:
        asyncio.set_event_loop(asyncio.new_event_loop())
        main()
    finally:
        try:
            os.remove(PID_FILE)
        except OSError:
            pass
