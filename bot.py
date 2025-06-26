from admin import get_admin_handlers
from user_storage import load_users, save_users
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")



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
        #[InlineKeyboardButton("₽ بيع وشراء الروبل", callback_data="rub_exchange")],
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
    users = context.application.bot_data.setdefault("users", set())
    user_id = update.effective_user.id
    if user_id not in users:
        users.add(user_id)
        save_users(users)  # Save immediately after adding

    greeting = "مرحبًا! 👋\n\nمرحبًا بك في بوت الدعم للطلاب في روسيا 🇷🇺.\n\nاستخدم الأزرار أدناه لاكتشاف الخدمات والمعلومات المفيدة.\n\nإذا كنت بحاجة لأي مساعدة، لا تتردد في التواصل معنا."

    # Respond to either /start message or callback "Start"
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
            "حتى إن كان مستواك ثانوياً وترغب في الدراسة في معهد خارج بلدك، فكل هذه الحالات ✅ تؤهلك للسفر إلى روسيا 🇷🇺 بهدف الدراسة والحصول على شهادة قوية 💪 ومعترف بها دوليًا 🌐.\n\n"
            "لكن 🤔 قد لا تعرف طريقة التسجيل، وتبحث عن وسيط موثوق 🤝 يساعدك ويوجهك من التسجيل الأولي 📝 إلى الوصول لروسيا ✈️، الاستقرار في السكن الجامعي 🏠، وبدء دراستك 📖 في الجامعة.\n\n"
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
            [InlineKeyboardButton("📄 االدليل قبل الوصول إلى روسيا", callback_data="before_arrival")],
            [InlineKeyboardButton("📑 الدليل بعد الوصول إلى روسيا", callback_data="after_arrival")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="Start")],
        ])
        await query.edit_message_text("📘 دليلك الشامل – اختر القسم:", reply_markup=keyboard)

    # الدليل قبل مجيئه إلى روسيا (6 أزرار)
    elif query.data == "before_arrival":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📌 ملف الفيزا", callback_data="Visa_guide")],
            [InlineKeyboardButton("📄استمارة الفيزا", callback_data="Visa_Forum")],
            #[InlineKeyboardButton("🛂 طلب التأشيرة", callback_data="visa_application")],
            [InlineKeyboardButton("📅 موعد التأشيرة", callback_data="visa_appointment")],
            # [InlineKeyboardButton("🛂 طلب التأشيرة", callback_data="visa_application")],
            [InlineKeyboardButton("📌 عملية التوثيق", callback_data="Authen_documents")],
            [InlineKeyboardButton("📞 معلومات الاتصال بالقنصلية الروسية في الجزائر", callback_data="russian_consulate_contact")],
            [InlineKeyboardButton("🏛️ سفارة الجزائر في روسيا", callback_data="algerian_embassy_russia")],
            [InlineKeyboardButton("✈️ معلومات الاتصال بشركة الخطوط الجوية الجزائرية", callback_data="airline_contact")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="guide_menu")],
        ])
        await query.edit_message_text("📄 الدليل قبل مجيئه إلى روسيا – اختر موضوعًا:", reply_markup=keyboard)

    # الدليل بعد وصوله إلى روسيا (4 أزرار)
    elif query.data == "after_arrival":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏦 كيفية فتح حساب بنكي في روسيا", callback_data="how_to_open_bank_account")],
            [InlineKeyboardButton("📱 كيفية الحصول على شريحة هاتف (SIM Card)", callback_data="how_to_get_sim")],
            #[InlineKeyboardButton("🟩 كيفية الحصول على البطاقة الخضراء", callback_data="how_to_get_green_card")],
            [InlineKeyboardButton("🆔 كيفية استخراج رقم التعريف الضريبي (ИНН) ورقم التأمين الاجتماعي (СНИЛС)", callback_data="how_to_get_tax_social")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="guide_menu")],
        ])
        await query.edit_message_text("📑 الدليل بعد وصوله إلى روسيا – اختر موضوعًا:", reply_markup=keyboard)

    # ردود أزرار فرعية - يمكن تعديلها لاحقًا
    elif query.data == "Authen_documents":
        text = (
            "🎥 شرح عملية التوثيق خطوة بخطوة:\n\n"
            "شاهد الفيديو هنا:\n"
            "https://youtu.be/x0mB1bAexGA?si=8oyBDQ6bi8vp55bT"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="before_arrival")]
        ])
        await query.edit_message_text(text, reply_markup=keyboard, disable_web_page_preview=True)



    elif query.data == "Visa_guide":
        text = (
            "🔗 فيديو شرح ملف الفيزا:\n"
            "https://youtu.be/tOCG-K8QQv8\n\n"
            "هل لديك أي سؤال؟ تواصل معنا عبر الزر أدناه."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 تواصل معنا", url="https://t.me/Yousfi_Abdelkader")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="before_arrival")]
        ])
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    elif query.data == "Visa_Forum":
        text = (
            "📢 منتدى التأشيرات:\n\n"
            "يمكنك مشاهدة شرح مفصل عبر الفيديو التالي:\n"
            "🔗 https://youtu.be/KYqtG5DihC8\n\n"
            "هل لديك أي سؤال؟ تواصل معنا عبر الزر أدناه."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 تواصل معنا", url="https://t.me/Yousfi_Abdelkader")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="before_arrival")]
        ])
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)



    #elif query.data == "visa_application":
        #await query.edit_message_text("🛂 هنا شرح طلب التأشيرة ...", reply_markup=back_button("before_arrival"))

    elif query.data == "visa_appointment":
        text = (
            "📅 معلومات موعد التأشيرة:\n\n"
            "يمكنك مشاهدة شرح مفصل عبر الفيديو التالي:\n"
            "🔗 https://youtu.be/dX-djNN-qRE\n\n"
            "هل لديك أي سؤال؟ تواصل معنا عبر الزر أدناه."
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 تواصل معنا", url="https://t.me/Yousfi_Abdelkader")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="before_arrival")]
        ])

        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)



    elif query.data == "russian_consulate_contact":
        text = (
            "📞 معلومات الاتصال بالقنصلية الروسية في الجزائر:\n\n"
            "🏢 العنوان:\n"
            "14, Impasse Bougandoura, El Biar, Alger\n\n"
            "📧 البريد الإلكتروني:\n"
            "rus.consulat@yandex.ru\n\n"
            "📞 الهاتف:\n"
            "+213 (0)20-28-09-28\n\n"
            "📠 الفاكس:\n"
            "+213 (0)23-37-68-67\n"
        )
        await query.edit_message_text(text, reply_markup=back_button("before_arrival"))

    elif query.data == "algerian_embassy_russia":
        text = (
            "🏛️ سفارة الجزائر في روسيا:\n\n"
            "📞 الهاتف: \u200E+7 (495) 937 46 00\n"
            "📍 العنوان: Крапивенский пер., 1А, Москва, 127051\n\n"
            "إذا لديك أي استفسار، لا تتردد في التواصل."
        )
        await query.edit_message_text(text, reply_markup=back_button("before_arrival"))


    elif query.data == "airline_contact":
        text = (
            "✈️ معلومات الاتصال بشركة الخطوط الجوية الجزائرية:\n\n"
            "📞 الهاتف:\n"
            "• <a href='tel:+74959092459'>+7 (495) 909 24 59</a>\n"
            "• <a href='tel:+79260115800'>+7 (926) 011 58 00</a>\n\n"
            "📍 العنوان:\n"
            "127550, Москва, Дмитровское ш., 27/1916-18\n\n"
            "📧 البريد الإلكتروني:\n"
            "airalgeriemoscow@mail.ru\n"
        )
        await query.edit_message_text(text, reply_markup=back_button("before_arrival"), parse_mode="HTML")





    elif query.data == "how_to_open_bank_account":

        text = (

            "💳 أهم حاجة يحتاجها المغترب هي الحساب البنكي.\n\n"

            "ننصحكم تفتحوا حساب في زوج بنوك مهمين:\n"

            "Сбербанк (سبيرбنك) و Тинькофф (Тбанк).\n\n"

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
            "📢 إذا واجهت أي مشكلة، لا تتردد في طلب استشارة عبر الزر أدناه 👇"

        )

        keyboard = InlineKeyboardMarkup([

            [InlineKeyboardButton("🗣️ اطلب الاستشارة", callback_data="request_consultation")],

            [InlineKeyboardButton("🔙 رجوع", callback_data="after_arrival")]

        ])

        await query.edit_message_text(text, reply_markup=keyboard)




    elif query.data == "how_to_get_sim":
        text = (
            "اليوم سنتحدث عن موضوع مهم وكثير من الناس يعانوا منه، وهو موضوع السيم كارد (Sim card).\n\n"
            "📋 المراحل بترتيب:\n\n"
            "1️⃣ للناس اللي عندها سيم كارد من قبل:\n\n"
            "الأمر أسهل بالنسبة لكم.\n\n"
            "✅ إذا عندك Госуслуги (بوابة الخدمات الحكومية)، و عندك СНИЛС (رقم التأمين الاجتماعي)، وفعّلت البيومتري، وحسابك موثق (учётная запись):\n"
            "▪️ تدخل للتطبيق Госуслуги وتكتب بمساعدة ماكس:\n"
            "  Подтверждение личности для заключения договора связи\n"
            "▪️ بعدها تدخل رقمك والشركة اللي اشتريت منها السيم كارد، وتكمل الخطوات، وتفعلها خلال خمس دقائق.\n\n"
            "2️⃣ للناس اللي ما عندهاش أي شيء:\n\n"
            "📌 الوثائق المطلوبة:\n"
            "• جواز السفر\n"
            "• ترجمة جواز السفر\n"
            "• ورقة التسجيل (регистрация)\n\n"
            "🔹 توجه إلى أقرب МФЦ (مركز الخدمات المتكاملة) وقل لهم:\n"
            "  \"أحتاج أخرج СНИЛС.\"\n"
            "📨 ينتج لك СНИЛС، وتنتظر الإيميل، وبعدها ترفعه على الموقع.\n"
            "⌛ انتظر حوالي 5 أيام عمل ليظهر في قاعدة البيانات، ثم عُد لـ МФЦ لفتح Госуслуги وتفعيل البيومتري.\n"
            "✳️ أو يمكنك تفعيله في أقرب بنك (لكن الأفضل МФЦ).\n\n"
            "3️⃣ بعد تفعيل Госуслуги والبيومتري:\n"
            "• إذا عندك سيم كارد، فعلها كما في المرحلة 1.\n"
            "• إذا ما عندكش، اشتري سيم كارد جديدة وفعلها بمساعدة موظف.\n\n"
            "⚠️ مهم جداً: الشريحة القديمة لازم تتفعل قبل يونيو، وإلا سيتم توقيفها.\n\n"
            "📢 إذا واجهت أي مشكلة، لا تتردد في طلب استشارة عبر الزر أدناه 👇"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗣️ اطلب الاستشارة", callback_data="request_consultation")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="after_arrival")]
        ])

        await query.edit_message_text(text, reply_markup=keyboard)



    #elif query.data == "how_to_get_green_card":
        #await query.edit_message_text("🟩 كيفية الحصول على البطاقة الخضراء ...", reply_markup=back_button("after_arrival"))

    elif query.data == "how_to_get_tax_social":

        text = (
            "🆔 كيفية استخراج رقم التعريف الضريبي (ИНН) ورقم التأمين الاجتماعي (СНИЛС):\n\n"
            "📍 يجب التوجه إلى أقرب مركز خدمات حكومية МФЦ (Многофункциональный центр)، وهو المكان الرسمي لاستخراج هذه الوثائق.\n\n"
            "📄 الوثائق المطلوبة:\n"
            "✅ جواز السفر (паспорт)\n"
            "✅ ترجمة جواز السفر إلى الروسية\n"
            "✅ بطاقة الهجرة (миграционная карта)\n"
            "✅ ورقة التسجيل (регистрация) – تثبت مكان سكنك الحالي\n\n"
            "🖊️ عند الوصول:\n"
            "1️⃣ اطلب استخراج СНИЛС (رقم التأمين الاجتماعي)\n"
            "2️⃣ بعد الحصول عليه، يمكنك أيضًا طلب استخراج ИНН (رقم التعريف الضريبي)\n\n"
            "🕐 المدة:\n"
            "غالبًا ما يتم إصدار СНИЛС خلال 1 إلى 3 أيام عمل.\n"
            "ИНН قد تحصل عليه مباشرة أو خلال أيام، حسب المدينة.\n\n"
            "💡 ملاحظات:\n"
            "• تأكد من أن بياناتك في الترجمة تطابق تمامًا ما في جواز السفر.\n"
            "📢 في حال واجهت أي صعوبة، يمكنك التوجه معنا عبر قسم الاستشارات للحصول على توجيه مباشر.\n"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗣️ اطلب الاستشارة", callback_data="request_consultation")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="after_arrival")],
        ])
        await query.edit_message_text(text, reply_markup=keyboard)
    else:
        await query.answer("هذا الزر غير معرف", show_alert=True)




if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()  # ✅ Build the app first
    app.bot_data["users"] = load_users()

    # ✅ Now you can add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # ✅ Add admin handlers
    for handler in get_admin_handlers():
        app.add_handler(handler)

    print("Bot is running...")
    app.run_polling()
