from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN ="7628097563:AAHWSwaT5XV46Np_BlaNzH2OVZOgSCUjXs0"

async def delete_bot_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    messages = context.user_data.get("bot_messages", [])
    for msg_id in messages:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    context.user_data["bot_messages"] = []



def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 قناة التلغرام", url="https://t.me/Kaader_Dz")],
        [InlineKeyboardButton("📺 YouTube", url="https://www.youtube.com/@Yousfi-Abdelkader")],
        [InlineKeyboardButton("💬 شات المجموعة", url="https://t.me/Kadet_Dz_Chat")],
        [InlineKeyboardButton("₽ بيع وشراء الروبل", callback_data="rub_exchange")],
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
    "📗 جواز السفر: 1200  روبل\n"
    "📋 شهادة بكالوريا: 1200 روبل\n"
    "📄 كشف نقاط البكالوريا:  1300 روبل\n"
    "🗒️ التحاليل: 700 روبل\n"
    "📋 ديبلوم ليسونس أو ماستر: 1200  روبل\n"
    "📄 كشف نقاط ليسونس أو ماستر: 1400 روبل\n\n"
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

    elif query.data == "rub_exchange":
        text = (
            "💰 نحن نقبل وسائل الدفع التالية:\n"
            "💶 اليورو\n"
            "💵 الدولار\n"
            "💴 الروبل\n"
            "💷 الدينار\n"
            "💵 ليرة\n"
            "🪙 العملات الرقمية (التشفير) – مثلBitcoin, USDT, وغيرها ✅\n\n"
            "📌  نقدم لعملائنا أسعار صرف العملات المتغيرة في كل ثانية، من خلال نظام محدث باستمرار يوميًا، "
            "يعتمد على مصادر موثوقة من مؤسسات مصرفية رسمية وأسعار السوق الموازي في الجزائر، "
            "مما يتيح لهم مراقبة دقيقة لأسعار الصرف وتسهيل عمليات التحويل."
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 تواصل معنا", url="https://t.me/Yousfi_Abdelkader")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="Start")]
        ])

        await query.edit_message_text(text, reply_markup=keyboard)


    # خدمات التسجيل و الترجمة قائمة
    elif query.data == "services_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 خدمات التسجيل", callback_data="registration_services")],
            [InlineKeyboardButton("📝 الترجمة", callback_data="translation_services")],
            [InlineKeyboardButton("🗣️ اطلب الاستشارة", callback_data="request_consultation")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="Start")],
        ])
        await query.edit_message_text("📑 خدمات التسجيل و الترجمة – اختر أحد الخيارات:", reply_markup=keyboard)

    elif query.data == "registration_services":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 تواصل الآن", url="https://t.me/Yousfi_Abdelkader")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="services_menu")]
        ])

        await query.edit_message_text(
            "🎓 لقد حصلت على شهادة البكالوريا؟\n"
            "📚 تدرس في الجامعة؟\n"
            "🌍 أو قررت تغيير مسارك الدراسي والدراسة في الخارج؟\n"
            "حتى إن كان مستواك ثانوياً وترغب في الدراسة في معهد خارج بلدك، فكل هذه الحالات ✅ تؤهلك للسفر إلى **روسيا** 🇷🇺 بهدف الدراسة والحصول على شهادة قوية 💪 ومعترف بها دوليًا 🌐.\n\n"
            "لكن 🤔 قد لا تعرف طريقة التسجيل، وتبحث عن وسيط موثوق 🤝 يساعدك ويوجهك من **التسجيل الأولي** 📝 إلى **الوصول لروسيا** ✈️، **الاستقرار في السكن الجامعي** 🏠، وبدء دراستك 📖 في الجامعة.\n\n"
            "🎯 إذاً، أنت في المكان الصحيح!\n"
            "ما عليك سوى اتباع خطوات التسجيل ✅\n"
            "ونحن سنتكفل بكل شيء 👨‍🏫 من المرافقة إلى غاية وصولك الآمن وبداية مسارك الدراسي بثقة 💼 واطمئنان 🛡️.\n\n"
            "هل ترغب في البدء؟ اضغط على الزر بالأسفل ⬇️ وسنكون معك خطوة بخطوة! 🛤️",
            reply_markup=keyboard
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
            [InlineKeyboardButton("📌 ملف الفيزا", callback_data="Visa_guide")],
            [InlineKeyboardButton("📄استمارة الفيزا", callback_data="Visa_Forum")],
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
    elif query.data == "Visa_guide":
        text = "📌 الوثائق المطلوبة للتسجيل:\n\nيمكنك مشاهدة شرح كامل بالفيديو عبر الرابط التالي:"
        await query.edit_message_text(text, reply_markup=back_button("before_arrival"))

        # إرسال رسالة جديدة مع رابط الفيديو ليظهر معاينة يوتيوب
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🔗 https://youtu.be/tOCG-K8QQv8"
        )

        # رسالة أزرار تواصل ورجوع
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 تواصل معنا", url="https://t.me/Yousfi_Abdelkader")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="before_arrival")]
        ])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="هل لديك أي سؤال؟ تواصل معنا عبر الزر أدناه.",
            reply_markup=keyboard
        )



    elif query.data == "Visa_Forum":
        text = "📢 منتدى التأشيرات:\n\nيمكنك مشاهدة شرح مفصل عبر الفيديو التالي:"
        await query.edit_message_text(text, reply_markup=back_button("before_arrival"))
        # إرسال رابط الفيديو ليظهر معاينة يوتيوب
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🔗 https://youtu.be/KYqtG5DihC8"

        )
        # رسالة أزرار تواصل ورجوع
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 تواصل معنا", url="https://t.me/Yousfi_Abdelkader")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="before_arrival")]
        ])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="هل لديك أي سؤال؟ تواصل معنا عبر الزر أدناه.",
            reply_markup=keyboard
        )


    elif query.data == "visa_application":
        await query.edit_message_text("🛂 هنا شرح طلب التأشيرة ...", reply_markup=back_button("before_arrival"))

    elif query.data == "visa_appointment":
        await query.edit_message_text("📅 معلومات موعد التأشيرة ...", reply_markup=back_button("before_arrival"))

    elif query.data == "russian_consulate_contact":
        await query.edit_message_text("📞 معلومات الاتصال بالقنصلية الروسية في الجزائر ...", reply_markup=back_button("before_arrival"))

    elif query.data == "airline_contact":
        await query.edit_message_text("✈️ معلومات الاتصال بشركة الخطوط الجوية الجزائرية ...", reply_markup=back_button("before_arrival"))

    elif query.data == "how_to_open_bank_account":
        await query.edit_message_text(
        "💳 أهم حاجة يحتاجها المغترب هي الحساب البنكي.\n\n"
        "ننصحكم تفتحوا حساب في زوج بنوك مهمين:\n"
        "Сбербанк (سبيربنك) و Тинькофф (Тбанк).\n\n"
        "📌 *طريقة فتح حساب في Сбербанк:\n\n"
        "1. دور على أقرب فرع Сбербанк.\n"
        "2. خذ معاك الوثائق التالية:\n"
        "   • جواز السفر\n"
        "   • الترجمة الرسمية للجواز\n"
        "   • بطاقة الهجرة (ميغراتيون كارد)\n"
        "   • ورقة الريجيستراتسيا\n"
        "   • رقم هاتف روسي يكون شغال\n"
        "3. لما تدخل للفرع، قول لهم:\n"
        "   \"Я хочу оформить карту\" (بمعنى: أريد فتح بطاقة).\n"
        "4. هم يتكفلوا بالباقي، يفتحولك الحساب ويعطوك البطاقة مباشرة، وكامل المعلومات يرسلوها لتطبيق الهاتف.\n\n"
        "⚠️ غالبًا الموظف يحاول يبيعلك عرض اسمه Сберпрайм بـ 299₽ شهريًا أو 2999₽ في السنة.\n"
        "قول له بكل بساطة: \"Нет\". العرض غير إجباري.\n\n"
        "📌 فتح حساب في Тинькофф (Тбанк):\n\n"
        "هذا البنك تفتح فيه الحساب من الهاتف فقط، ويجيك المندوب حتى لدارك يسلمك البطاقة.\n\n"
        "1. حضّر نفس الوثائق السابقة.\n"
        "2. ادخل على هذا الرابط وعمّر المعلومات:\n"
        "👉 https://www.tbank.ru/baf/ucdgm7eo8q\n"
        "3. تختار اليوم اللي يناسبك لتوصيل البطاقة، وتوصلك مجانا، حتى حامل البطاقات يعطيهولك مجاني.\n\n"
        "⏱️ ملاحظة سريعة:\n\n"
        "* بطاقة Сбербанк تاخذها في نفس اليوم.\n"
        "* بطاقة Тинькофф توصلك في اليوم التالي تقريبًا.\n\n"
        "🔁 خدمة خاصة لسكان بيتر (سانت بطرسبورغ):\n\n"
        "* إذا حاولت تفتح حساب وقالولك لازم تدفع 2999₽ غصب، أو وقعت في فخ، تواصل معايا ونقدر نرجعلك فلوسك "
        "إذا ما فاتتش 15 يوم من الدفع.\n"
        "* وإذا مزال ما فتحتش حساب وعايش في بيتر، تواصل معايا نعاونك ونفتحلك الحساب لوجه الله.\n\n"
        "📢 أيها القارئ، شارك المعلومة باش تعم الفائدة.\n"
        "واشترك في القناة:\n"
        "https://t.me/+DNclQXMhFExlNGRk",
        reply_markup=back_button("after_arrival")
    )

    elif query.data == "how_to_get_sim":

        await query.edit_message_text(

            "اليوم سنتحدث عن موضوع مهم وكثير من الناس يعانوا منه، وهو **موضوع السيم كارد\n"
            "(Sim card).\n\n"
            " المراحل بترتيب:\n\n"
            " 1. للناس اللي عندها سيم كارد من قبل:\n\n"
            "الأمر أسهل بالنسبة لكم.\n\n"
            "* أولاً، إذا عندك Госуслуги (بوابة الخدمات الحكومية)، و عندك **СНИЛС** (رقم التأمين الاجتماعي)، وفعّلت البيومتري، وحسابك موثق (учётная запись)،\n"
            " تدخل للتطبيق Госуслуги وتكتب بمساعدة ماكس:\n"
            "  Подтверждение личности для заключения договора связи\n"
            "* بعدها تدخل رقمك والشركة اللي اشتريت منها السيم كارد، وتكمل الخطوات، وتفعلها خلال خمس دقائق.\n\n"
            " 2. للناس اللي ما عندهاش أي شيء:\n\n"
            " أولاً، خذ معاك:\n\n"
            " جواز السفر\n"
            " ترجمة جواز السفر\n"
            "  ورقة التسجيل (регистрация)\n"
            " وروح لأقرب МФЦ (مركز الخدمات المتكاملة) وقل لهم:\n"
            "  \"أحتاج أخرج СНИЛС.\"\n"
            " هم يعملوه لك، وتنتظر حتى يصلك الإيميل أنه جاهز، بعدها ترفعه في الموقع.\n"
            " بعد رفعه، اصبر حوالي خمس أيام عمل ليظهر في قاعدة البيانات، بعدها تعاود تروح МФЦ.\n"
            " تقول لهم: \"بغيت أفتح Госуслуги.\"\n"
            " هم يفتحوه لك ويفعلوه، ويسجلوا لك البيومتري.\n"
            " أو تقدر تروح لأقرب بنك، وهم يفعلوه لك باستخدام СНИЛС وجواز السفر وترجمته.\n\n"
            "⭕️ الأفضل تعمل كل شيء في МФЦ، لأنه لو صار أي مشكلة هم المسؤولين ويقدروا يساعدوك بسهولة أكثر من البنك.\n\n"
            " 3. بعد ما تفتح حساب Госуслуги وتفعّله، وتعمل البيومتري:\n\n"
            " إذا عندك سيم كارد، فعلها كما شرحت في المرحلة الأولى.\n"
            " إذا ما عندكش، تروح تشتري سيم كارد من أي مكان تحب، وتفعلها هناك بمساعدة موظف.\n\n"
            "⚠️مهم جداً: اللي عنده سيم كارد قديمة لازم يفعلها قبل يونيو، لأن بعدها سيتم إيقاف الشريحة.\n\n"
            "أي سؤال أو إذا ما فهمتش حاجة، حط سؤالك في التعليقات.\n\n"
            "رابط القناة:\n"
            "[https://t.me/+aMlKWNOdHEAzMzY0](https://t.me/+aMlKWNOdHEAzMzY0)\n\n"
            "هل تريدني أساعدك بصيغة رسمية أكثر أو مختصرة؟",
            reply_markup=back_button("after_arrival")
        )


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

