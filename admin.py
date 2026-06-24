# -*- coding: utf-8 -*-
"""
Admin panel — interactive inline keyboard dashboard + broadcast ConversationHandler.
Restricted to ADMINS list (env ADMIN_IDS or hardcoded fallback).
"""
import asyncio
import logging
import os
import tempfile
import warnings
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from keyboards import (
    admin_panel_kb, admin_back_kb, broadcast_type_kb,
    broadcast_groups_kb, broadcast_confirm_kb,
)
from user_storage import get_stats, get_user_ids

logger = logging.getLogger(__name__)

# ── Admin IDs ─────────────────────────────────────────────────────────────────

_env = os.getenv("ADMIN_IDS", "").strip()
ADMINS: list[int] = (
    [int(x.strip()) for x in _env.split(",") if x.strip()]
    if _env
    else [872846255, 6698671368]
)

GROUP_IDS: list[int] = [int(x.strip()) for x in os.getenv("GROUP_IDS", "").split(",") if x.strip()]
BOT_USERNAME = os.getenv("BOT_USERNAME", "DzHelpInRuss_Bot")
_GROUP_BOT_LINK_KB = InlineKeyboardMarkup([[
    InlineKeyboardButton("🤖 الانتقال إلى البوت", url=f"https://t.me/{BOT_USERNAME}")
]])

# ── Conversation states ───────────────────────────────────────────────────────

_ADMIN_PASS = 0                                       # admin auth
_BC_TYPE, _BC_MSG, _BC_GROUPS, _BC_CONFIRM = range(1, 5)  # broadcast


# ── Helpers ───────────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


def _panel_text(users: dict) -> str:
    s = get_stats(users)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        "👨‍💼 *لوحة تحكم المشرف*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 *المستخدمون:* `{s['total']}`\n"
        f"🆕 *جدد اليوم:* `+{s['new_today']}`\n"
        f"📅 *جدد هذا الأسبوع:* `+{s['new_week']}`\n"
        f"🕐 *التحديث:* `{now}`"
    )


# ── Admin auth ConversationHandler ────────────────────────────────────────────

async def admin_panel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية الوصول\\.", parse_mode=ParseMode.MARKDOWN_V2)
        return ConversationHandler.END
    await update.message.reply_text(
        "🔐 *أدخل كلمة المرور:*",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    return _ADMIN_PASS


async def admin_check_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    entered = update.message.text.strip()
    # Delete the password message immediately for security
    try:
        await update.message.delete()
    except Exception:
        pass

    admin_password = os.getenv("ADMIN_PASSWORD", "Kader2508")
    if entered != admin_password:
        await update.message.reply_text(
            "❌ *كلمة المرور خاطئة\\.*\nحاول مرة أخرى بـ /admin",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return ConversationHandler.END

    users = context.application.bot_data.get("users", {})
    await update.message.reply_text(
        _panel_text(users),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=admin_panel_kb(),
    )
    return ConversationHandler.END


async def admin_auth_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ تم الإلغاء\\.", parse_mode=ParseMode.MARKDOWN_V2)
    return ConversationHandler.END


# ── Panel callback handler ────────────────────────────────────────────────────

async def panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("❌ غير مصرّح", show_alert=True)
        return

    users = context.application.bot_data.get("users", {})
    data = query.data

    if data in ("adm_refresh", "adm_panel"):
        await query.edit_message_text(
            _panel_text(users),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=admin_panel_kb(),
        )

    elif data == "adm_stats":
        s = get_stats(users)
        bot_info = await context.bot.get_me()
        username = escape_markdown(bot_info.username, version=2)
        text = (
            "📊 *إحصائيات مفصلة*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *البوت:* @{username}\n"
            f"👥 *الإجمالي:* `{s['total']}`\n"
            f"🆕 *جدد اليوم:* `{s['new_today']}`\n"
            f"📅 *جدد هذا الأسبوع:* `{s['new_week']}`\n"
            f"🕐 *آخر تحديث:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=admin_back_kb(),
        )

    elif data == "adm_export":
        ids = get_user_ids(users)
        if not ids:
            await query.answer("📭 لا يوجد مستخدمون مسجلون", show_alert=True)
            return
        content = "\n".join(str(uid) for uid in sorted(ids))
        filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            with open(tmp, "rb") as f:
                await query.message.reply_document(
                    document=f,
                    filename=filename,
                    caption=f"📋 إجمالي المستخدمين: `{len(ids)}`",
                    parse_mode=ParseMode.MARKDOWN_V2,
                )
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass


# ── Broadcast ConversationHandler ─────────────────────────────────────────────

async def bc_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return ConversationHandler.END
    await query.message.reply_text(
        "📤 *اختر نوع الرسالة:*",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=broadcast_type_kb(),
    )
    return _BC_TYPE


async def bc_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "bc_cancel":
        await query.edit_message_text("❌ تم إلغاء البث\\.", parse_mode=ParseMode.MARKDOWN_V2)
        return ConversationHandler.END
    context.user_data["bc_mode"] = "plain" if query.data == "bc_plain" else "markdown"
    await query.edit_message_text(
        "✏️ *أرسل نص الرسالة الآن:*\n\n_\\(أو /cancel للإلغاء\\)_",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    return _BC_MSG


async def bc_msg_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data["bc_message"] = update.message.text
    if GROUP_IDS:
        await update.message.reply_text(
            f"📢 *هل تريد إرسال هذه الرسالة إلى المجموعات أيضًا؟* \\(`{len(GROUP_IDS)}` مجموعة\\)",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=broadcast_groups_kb(),
        )
        return _BC_GROUPS
    context.user_data["bc_send_groups"] = False
    return await _show_bc_preview(update.message, context)


async def bc_groups_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "bc_cancel":
        await query.edit_message_text("❌ تم إلغاء البث\\.", parse_mode=ParseMode.MARKDOWN_V2)
        _bc_cleanup(context)
        return ConversationHandler.END
    context.user_data["bc_send_groups"] = (query.data == "bc_grp_yes")
    return await _show_bc_preview(query.message, context, edit=query)


async def _show_bc_preview(message, context: ContextTypes.DEFAULT_TYPE, edit=None) -> int:
    msg = context.user_data.get("bc_message", "")
    mode = context.user_data.get("bc_mode", "plain")
    label = "📣 Markdown" if mode == "markdown" else "📝 نص عادي"
    users = context.application.bot_data.get("users", {})
    total = len(users)
    send_groups = context.user_data.get("bc_send_groups", False)
    groups_line = f"📣 المجموعات: `{len(GROUP_IDS)}`\n" if send_groups else ""
    # msg goes into a code block — no MarkdownV2 escaping needed inside ```...```
    preview = (
        f"👀 *معاينة الرسالة*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"النوع: {label}\n"
        f"المستلمون: `{total}` مستخدم\n"
        f"{groups_line}\n"
        f"📨 *الرسالة:*\n"
        f"```\n{msg}\n```\n\n"
        f"هل تريد الإرسال؟"
    )
    if edit:
        await edit.edit_message_text(preview, parse_mode=ParseMode.MARKDOWN_V2,
                                      reply_markup=broadcast_confirm_kb())
    else:
        await message.reply_text(preview, parse_mode=ParseMode.MARKDOWN_V2,
                                  reply_markup=broadcast_confirm_kb())
    return _BC_CONFIRM


async def bc_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "bc_cancel":
        await query.edit_message_text("❌ تم إلغاء البث\\.", parse_mode=ParseMode.MARKDOWN_V2)
        _bc_cleanup(context)
        return ConversationHandler.END

    msg          = context.user_data.get("bc_message", "")
    mode         = context.user_data.get("bc_mode", "plain")
    send_groups  = context.user_data.get("bc_send_groups", False)
    parse_mode   = ParseMode.MARKDOWN if mode == "markdown" else None

    users = context.application.bot_data.get("users", {})
    ids = get_user_ids(users)
    total = len(ids)

    status = await query.edit_message_text(
        f"📤 جاري الإرسال إلى `{total}` مستخدم\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    success = blocked = failed = 0
    for uid in ids:
        try:
            kwargs: dict = {"chat_id": uid, "text": msg}
            if parse_mode:
                kwargs["parse_mode"] = parse_mode
                kwargs["disable_web_page_preview"] = True
            await context.bot.send_message(**kwargs)
            success += 1
            await asyncio.sleep(0.04)
        except Exception as e:
            err = str(e).lower()
            if any(x in err for x in ("bot was blocked", "user is deactivated", "forbidden", "chat not found")):
                blocked += 1
            else:
                failed += 1
                logger.warning("Broadcast failed for %d: %s", uid, e)

    groups_ok = groups_fail = 0
    if send_groups:
        for gid in GROUP_IDS:
            try:
                kwargs: dict = {"chat_id": gid, "text": msg, "reply_markup": _GROUP_BOT_LINK_KB}
                if parse_mode:
                    kwargs["parse_mode"] = parse_mode
                    kwargs["disable_web_page_preview"] = True
                await context.bot.send_message(**kwargs)
                groups_ok += 1
            except Exception as e:
                groups_fail += 1
                logger.warning("Group broadcast failed for %d: %s", gid, e)

    groups_line = f"📣 *المجموعات:* `{groups_ok}` ناجح، `{groups_fail}` فشل\n" if send_groups else ""
    await status.edit_text(
        "✅ *اكتمل البث\\!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📨 *ناجح:* `{success}`\n"
        f"🚫 *محظور/غير نشط:* `{blocked}`\n"
        f"⚠️ *فشل:* `{failed}`\n"
        f"📊 *الإجمالي:* `{total}`\n"
        f"{groups_line}",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    _bc_cleanup(context)
    return ConversationHandler.END


async def bc_cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ تم إلغاء البث\\.", parse_mode=ParseMode.MARKDOWN_V2)
    _bc_cleanup(context)
    return ConversationHandler.END


def _bc_cleanup(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("bc_message", None)
    context.user_data.pop("bc_mode", None)
    context.user_data.pop("bc_send_groups", None)


# ── Legacy text shortcuts (/stats, /broadcast, /users) ───────────────────────

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    users = context.application.bot_data.get("users", {})
    s = get_stats(users)
    bot_info = await context.bot.get_me()
    username = bot_info.username.replace("_", "\\_")
    await update.message.reply_text(
        "📊 *إحصائيات البوت*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 @{username}\n"
        f"👥 *الإجمالي:* `{s['total']}`\n"
        f"🆕 *جدد اليوم:* `{s['new_today']}`\n"
        f"📅 *جدد هذا الأسبوع:* `{s['new_week']}`\n"
        f"🕐 `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(
            "ℹ️ الاستخدام: `/broadcast نص الرسالة`\n"
            "أو استخدم لوحة `/admin` للبث التفاعلي\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return
    msg = " ".join(context.args)
    users = context.application.bot_data.get("users", {})
    ids = get_user_ids(users)
    status = await update.message.reply_text(
        f"📤 جاري الإرسال إلى `{len(ids)}` مستخدم\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    success = blocked = failed = 0
    for uid in ids:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            success += 1
            await asyncio.sleep(0.04)
        except Exception as e:
            err = str(e).lower()
            if any(x in err for x in ("bot was blocked", "user is deactivated", "forbidden", "chat not found")):
                blocked += 1
            else:
                failed += 1
    await status.edit_text(
        f"✅ ناجح: `{success}` \\| 🚫 محظور: `{blocked}` \\| ⚠️ فشل: `{failed}`",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def users_export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    users = context.application.bot_data.get("users", {})
    ids = get_user_ids(users)
    if not ids:
        await update.message.reply_text("📭 لا يوجد مستخدمون مسجلون\\.", parse_mode=ParseMode.MARKDOWN_V2)
        return
    content = "\n".join(str(uid) for uid in sorted(ids))
    filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp = f.name
    try:
        with open(tmp, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=filename,
                caption=f"📋 إجمالي: `{len(ids)}` مستخدم",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


# ── Handler registration ──────────────────────────────────────────────────────

def get_admin_handlers() -> list:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        admin_auth_conv = ConversationHandler(
            entry_points=[CommandHandler("admin", admin_panel_cmd)],
            states={
                _ADMIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_check_password)],
            },
            fallbacks=[CommandHandler("cancel", admin_auth_cancel)],
            per_user=True,
            per_chat=True,
        )

        broadcast_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(bc_start, pattern="^adm_broadcast$")],
            states={
                _BC_TYPE:   [CallbackQueryHandler(bc_type_chosen, pattern="^bc_(plain|markdown|cancel)$")],
                _BC_MSG:    [MessageHandler(filters.TEXT & ~filters.COMMAND, bc_msg_received)],
                _BC_GROUPS: [CallbackQueryHandler(bc_groups_chosen, pattern="^bc_(grp_yes|grp_no|cancel)$")],
                _BC_CONFIRM:[CallbackQueryHandler(bc_confirmed, pattern="^bc_(confirm|cancel)$")],
            },
            fallbacks=[CommandHandler("cancel", bc_cancel_cmd)],
            per_user=True,
            per_chat=True,
        )

    return [
        admin_auth_conv,
        broadcast_conv,
        CallbackQueryHandler(panel_callback, pattern="^adm_(stats|refresh|panel|export)$"),
        CommandHandler("stats", stats_cmd),
        CommandHandler("broadcast", broadcast_cmd),
        CommandHandler("announce", broadcast_cmd),
        CommandHandler("users", users_export_cmd),
    ]
