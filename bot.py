from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = "7628097563:AAEqjdqraYRV4HmbyJ0cWrfIg1DR25uNw78"  # Replace with your real token

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 قناة التلغرام", url="https://t.me/Kaader_Dz")],
        [InlineKeyboardButton("📺 YouTube", url="https://www.youtube.com/@Yousfi-Abdelkader")],
        [InlineKeyboardButton("💬 شات المجموعة", url="https://t.me/Kadet_Dz_Chat")],
        [InlineKeyboardButton("📑 خدمات التسجيل والترجمة, الاستشارة", callback_data="services_menu")],
        [InlineKeyboardButton("📘 دليلك الشامل", callback_data="guide_menu")],
    ])

def back_button(back_to="Start"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data=back_to)]
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

    # خدمات التسجيل و الترجمة قائمة
    elif query.data == "services_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 خدمات التسجيل", callback_data="registration_services")],
            [InlineKeyboardButton("📝 الترجمة", callback_data="translation_services")],
            [InlineKeyboardButton("🗣️ اطلب الاستشارة", callback_data="request_consultation")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="Start")],
        ])
        await query.edit_message_text("📑 خدمات التسجيل و الترجمة – اختر أحد الخيارات:", reply_markup=keyboard)

    # خدمات التسجيل (يمكنك تعديل الرسالة حسب الحاجة)
    elif query.data == "registration_services":
        await query.edit_message_text(
            "📚 خدمات التسجيل:\n\n"
            "هنا يمكنك إضافة تفاصيل خدمات التسجيل التي تقدمها.\n"
            "يمكنك تعديل هذه الرسالة لاحقًا حسب متطلباتك.",
            reply_markup=back_button("services_menu")
        )

    # الترجمة
    elif query.data == "translation_services":
        await query.edit_message_text(TRANSLATION_MESSAGE, reply_markup=back_button("services_menu"))

    # اطلب الاستشارة
    elif query.data == "request_consultation":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Yousfi Abdelkader / Kader", url="https://t.me/Yousfi_Abdelkader")],
            [InlineKeyboardButton("💬 Ramzi Peter", url="https://t.me/the_random_men")],
            [InlineKeyboardButton("💬 وليد", url="https://t.me/Oualid_bel")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="services_menu")]
        ])
        await query.edit_message_text("🗣️ اختر المستشار الذي تريد التواصل معه:", reply_markup=keyboard)

    # دليلك الشامل قائمة رئيسية
    elif query.data == "guide_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 الدليل قبل مجيئه إلى روسيا", callback_data="before_arrival")],
            [InlineKeyboardButton("📑 الدليل بعد وصوله إلى روسيا", callback_data="after_arrival")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="Start")],
        ])
        await query.edit_message_text("📘 دليلك الشامل – اختر القسم:", reply_markup=keyboard)

    # الدليل قبل مجيئه إلى روسيا (6 أزرار)
    elif query.data == "before_arrival":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📌 دليل القبول في روسيا", callback_data="acceptance_guide")],
            [InlineKeyboardButton("📄 الوثائق المطلوبة", callback_data="required_documents")],
            [InlineKeyboardButton("🛂 طلب التأشيرة", callback_data="visa_application")],
            [InlineKeyboardButton("📅 موعد التأشيرة", callback_data="visa_appointment")],
            [InlineKeyboardButton("📞 معلومات الاتصال بالقنصلية الروسية في الجزائر", callback_data="russian_consulate_contact")],
            [InlineKeyboardButton("✈️ معلومات الاتصال بشركة الخطوط الجوية الجزائرية", callback_data="airline_contact")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="guide_menu")],
        ])
        await query.edit_message_text("📄 الدليل قبل مجيئه إلى روسيا – اختر موضوعًا:", reply_markup=keyboard)

    # الدليل بعد وصوله إلى روسيا (4 أزرار)
    elif query.data == "after_arrival":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏦 كيفية فتح حساب بنكي في روسيا", callback_data="how_to_open_bank_account")],
            [InlineKeyboardButton("📱 كيفية الحصول على شريحة هاتف (SIM Card)", callback_data="how_to_get_sim")],
            [InlineKeyboardButton("🟩 كيفية الحصول على البطاقة الخضراء", callback_data="how_to_get_green_card")],
            [InlineKeyboardButton("🆔 كيفية استخراج رقم التعريف الضريبي (ИНН) ورقم التأمين الاجتماعي (СНИЛС)", callback_data="how_to_get_tax_social")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="guide_menu")],
        ])
        await query.edit_message_text("📑 الدليل بعد وصوله إلى روسيا – اختر موضوعًا:", reply_markup=keyboard)

    # ردود أزرار فرعية - يمكن تعديلها لاحقًا
    elif query.data == "acceptance_guide":
        await query.edit_message_text("📌 هنا شرح دليل القبول في روسيا ...", reply_markup=back_button("before_arrival"))

    elif query.data == "required_documents":
        await query.edit_message_text("📄 الوثائق المطلوبة هي ...", reply_markup=back_button("before_arrival"))

    elif query.data == "visa_application":
        await query.edit_message_text("🛂 هنا شرح طلب التأشيرة ...", reply_markup=back_button("before_arrival"))

    elif query.data == "visa_appointment":
        await query.edit_message_text("📅 معلومات موعد التأشيرة ...", reply_markup=back_button("before_arrival"))

    elif query.data == "russian_consulate_contact":
        await query.edit_message_text("📞 معلومات الاتصال بالقنصلية الروسية في الجزائر ...", reply_markup=back_button("before_arrival"))

    elif query.data == "airline_contact":
        await query.edit_message_text("✈️ معلومات الاتصال بشركة الخطوط الجوية الجزائرية ...", reply_markup=back_button("before_arrival"))

    elif query.data == "how_to_open_bank_account":
        await query.edit_message_text("🏦 كيفية فتح حساب بنكي في روسيا ...", reply_markup=back_button("after_arrival"))

    elif query.data == "how_to_get_sim":
        await query.edit_message_text("📱 كيفية الحصول على شريحة هاتف (SIM Card) ...", reply_markup=back_button("after_arrival"))

    elif query.data == "how_to_get_green_card":
        await query.edit_message_text("🟩 كيفية الحصول على البطاقة الخضراء ...", reply_markup=back_button("after_arrival"))

    elif query.data == "how_to_get_tax_social":
        await query.edit_message_text("🆔 كيفية استخراج رقم التعريف الضريبي (ИНН) ورقم التأمين الاجتماعي (СНИЛС) ...", reply_markup=back_button("after_arrival"))

    else:
        await query.answer("هذا الزر غير معرف", show_alert=True)


if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app.run_polling()
