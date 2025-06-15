from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from flask import Flask
import threading
import os
import asyncio

BOT_TOKEN = "7628097563:AAEEgVCCtSucect6WJ8oCx_IaLGUcsG0F0Q"  # Replace with your real token

# Your existing functions

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 قناة التلغرام", url="https://t.me/Kaader_Dz")],
        [InlineKeyboardButton("📺 YouTube", url="https://www.youtube.com/@Yousfi-Abdelkader")],
        [InlineKeyboardButton("💬 شات المجموعة", url="https://t.me/Kadet_Dz_Chat")],
        [InlineKeyboardButton("📑 خدمات التسجيل و الترجمة", callback_data="translation_services")],
        [InlineKeyboardButton("📘 دليلك الشامل", callback_data="guide_menu")],
    ])

def back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="Start")]
    ])

TRANSLATION_MESSAGE = (
    "ترجمة أوراق رسمية 📑 إلى اللغة الروسية 🇷🇺:\n\n"
    "نوفر لكم خدمات ترجمة الأوراق الرسمية📑 إلى اللغة الروسية 🇷🇺 بأسعار تنافسية💰\n\n"
    "📗 جواز السفر: 2,560 دج أو 800 روبل\n"
    "📋 شهادة بكالوريا: 3,520 دج أو 1100 روبل\n"
    "📄 كشف نقاط البكالوريا: 4,200 دج أو 1300 روبل\n"
    "🗒️ التحاليل: 1800 دج للورقة أو 600 روبل\n"
    "📋 ديبلوم ليسونس أو ماستر: 3,500 دج أو 1100 روبل\n"
    "📄 كشف نقاط ليسونس أو ماستر: 4,500 دج أو 1400 روبل\n\n"
    "ملاحظة:\n"
    "🔖 الأسعار لا تتغير لو كانت الأوراق موثقة في الوزارات.\n"
    "📨 كيفية الحصول على النسخ الأصلية يكون بالاتفاق مع الطالب سواء في الجزائر أو روسيا، وسعر التوصيل بالبريد على عاتق الطالب.\n\n"
    "للتواصل:\n"
    "@Yousfi_Abdelkader\n"
    "+7 915 884 6143\n"
    "أرسل اسمك، لقبك، رقمك، والوثائق التي تريد ترجمتها."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    greeting = (
        "البوت في مرحلة تحديث ⚙️\n\n"
        "يرجى حذف المحادثة وإعادة تشغيل البوت بالضغط على الزر 👇"
    )
    if update.message:
        sent_msg = await update.message.reply_text(greeting, reply_markup=main_menu_keyboard())
        context.user_data["last_message_id"] = sent_msg.message_id
    elif update.callback_query:
        await update.callback_query.edit_message_text(greeting, reply_markup=main_menu_keyboard())
        context.user_data["last_message_id"] = update.callback_query.message.message_id

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    last_msg_id = context.user_data.get("last_message_id")
    chat_id = query.message.chat_id
    if last_msg_id and last_msg_id != query.message.message_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_msg_id)
        except Exception:
            pass  # Ignore if can't delete

    context.user_data["last_message_id"] = query.message.message_id

    if query.data == "Start":
        await start(update, context)

    elif query.data == "translation_services":
        await query.edit_message_text(TRANSLATION_MESSAGE, reply_markup=back_button())

    elif query.data == "guide_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗺️ دليل التسجيل الجامعي", callback_data="uni_guide")],
            [InlineKeyboardButton("📚 دليل السكن", callback_data="housing_guide")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="Start")],
        ])
        await query.edit_message_text("📘 دليلك الشامل – اختر أحد الأقسام:", reply_markup=keyboard)

    elif query.data == "uni_guide":
        await query.edit_message_text("📘 هذا هو دليل التسجيل الجامعي 📚.", reply_markup=back_button())

    elif query.data == "housing_guide":
        await query.edit_message_text("🏠 هذا هو دليل السكن والخدمات 🏠.", reply_markup=back_button())

    else:
        await query.edit_message_text("تم الضغط على: " + query.data, reply_markup=back_button())

# --- Flask app part ---

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "🤖 Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    # Run Flask without debug, on all interfaces:
    flask_app.run(host='0.0.0.0', port=port)

async def main():
    # Start Flask app in a thread
    threading.Thread(target=run_flask).start()

    # Start Telegram bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot is running with all buttons and رجوع!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
