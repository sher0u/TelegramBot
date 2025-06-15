from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import os

BOT_TOKEN = os.environ.get("7628097563:AAEB0ipX_KQmAq3A4lM1dqxIB1glT45RDVE")  # safer for deployment

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    greeting = (
        "البوت في مرحلة تحديث ⚙️\n\n"
        "يرجى حذف المحادثة وإعادة تشغيل البوت بالضغط على الزر 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🔄 Start", callback_data="Start")],
        [InlineKeyboardButton("📢 قناة التلغرام", url="https://t.me/Kaader_Dz")],
        [InlineKeyboardButton("📺 YouTube", url="https://www.youtube.com/@Yousfi-Abdelkader")],
        [InlineKeyboardButton("💬 شات المجموعة", url="https://t.me/Kadet_Dz_Chat")],
        [InlineKeyboardButton("📝 خدمات التسجيل و الترجمة", callback_data="translation")],
        [InlineKeyboardButton("📘 دليلك الشامل", callback_data="guide")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(greeting, reply_markup=reply_markup)

# Button callback
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "Start":
        await start(update, context)

    elif query.data == "translation":
        await query.edit_message_text(
            text=(
                "ترجمة أوراق رسمية 📑 إلى اللغة الروسية 🇷🇺:\n\n"
                "📗 جواز السفر: 2,560 دج أو 800 روبل\n"
                "📋 شهادة بكالوريا: 3,520 دج أو 1100 روبل\n"
                "📄 كشف نقاط البكالوريا: 4,200 دج أو 1300 روبل\n"
                "🗒️ التحاليل: 1800 دج للورقة أو 600 روبل\n"
                "📋 ديبلوم ليسونس/ماستر: 3,500 دج أو 1100 روبل\n"
                "📄 كشف نقاط ليسونس/ماستر: 4,500 دج أو 1400 روبل\n\n"
                "📌 الأسعار لا تتغير لو كانت الأوراق موثقة\n"
                "📨 تواصل على الخاص: @Yousfi_Abdelkader | +7 915 884 6143"
            )
        )

    elif query.data == "guide":
        keyboard = [
            [InlineKeyboardButton("📌 خطوة 1", callback_data="step1")],
            [InlineKeyboardButton("📌 خطوة 2", callback_data="step2")],
            [InlineKeyboardButton("↩️ رجوع", callback_data="Start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📘 دليلك الشامل - اختر خطوة:", reply_markup=reply_markup)

    else:
        await query.edit_message_text("تم الضغط على: " + query.data)

# Main
if __name__ == "__main__":
    import asyncio

    async def main():
        app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_handler))

        print("🤖 Bot running")
        await app.run_polling()

    asyncio.run(main())
