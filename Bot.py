from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import os
BOT_TOKEN = os.environ["7628097563:AAFvePAB1EkfCMDWywZ6NM-il7oFlIiJpZc"]


# Main keyboard
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Start", callback_data="Start")],
        [InlineKeyboardButton("📢 قناة التلغرام", url="https://t.me/Kaader_Dz")],
        [InlineKeyboardButton("📺 YouTube", url="https://www.youtube.com/@Yousfi-Abdelkader")],
        [InlineKeyboardButton("💬 شات المجموعة", url="https://t.me/Kadet_Dz_Chat")],
        [InlineKeyboardButton("📑 خدمات التسجيل و الترجمة", callback_data="translation_services")],
        [InlineKeyboardButton("📘 دليلك الشامل", callback_data="guide_menu")],
    ])

# Add a "Back" button to any section
def back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="Start")]
    ])

# Translation services message
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

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    greeting = (
        "البوت في مرحلة تحديث ⚙️\n\n"
        "يرجى حذف المحادثة وإعادة تشغيل البوت بالضغط على الزر 👇"
    )
    if update.message:
        await update.message.reply_text(greeting, reply_markup=main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.edit_message_text(greeting, reply_markup=main_menu_keyboard())

# Callback handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

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

# Main bot setup
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🤖 Bot is running with all buttons and رجوع!")
    app.run_polling()
