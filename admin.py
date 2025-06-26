from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

ADMINS = [872846255,6698671368]  # Your Telegram user ID here

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("❌ You are not authorized to access the admin panel.")
        return

    users = context.application.bot_data.get("users", set())
    text = (
        "👨‍💼 Admin Panel\n\n"
        f"👥 Total Users: {len(users)}\n"
        "📢 Send a broadcast:\n"
        "`/broadcast Your message here`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if not context.args:
        await update.message.reply_text("ℹ️ Usage: `/broadcast Your message here`", parse_mode="Markdown")
        return

    message = " ".join(context.args)
    users = context.application.bot_data.get("users", set())

    success = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            success += 1
        except Exception:
            continue

    await update.message.reply_text(f"✅ Sent to {success}/{len(users)} users.")

def get_admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CommandHandler("broadcast", broadcast)
    ]
