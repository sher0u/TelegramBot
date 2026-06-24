# -*- coding: utf-8 -*-
"""All inline keyboard builders — KADER DZ Bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import marketplace_storage as MKT


# ══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════════════════════════════════════════════

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 دليلك الشامل",       callback_data="guide_menu")],
        [InlineKeyboardButton("🏛️ الخدمات القنصلية",   callback_data="consular_menu")],
        [InlineKeyboardButton("⚙️ الخدمات",             callback_data="services_menu")],
        [InlineKeyboardButton("🛒 Avito Algeria",       callback_data="avito_menu"),
         InlineKeyboardButton("🏠 شريك سكن",           callback_data="rm_menu")],
        [InlineKeyboardButton("🧳 هبطلي ولا طلعلي معاك", callback_data="trv_menu")],
        [InlineKeyboardButton("📝 تقديم استفسار",       callback_data="inquiry_start")],
        [InlineKeyboardButton("📢 القناة",  url="https://t.me/Kaader_Dz"),
         InlineKeyboardButton("📺 يوتيوب", url="https://www.youtube.com/@Yousfi-Abdelkader"),
         InlineKeyboardButton("💬 الشات",  url="https://t.me/RussianTent")],
        [InlineKeyboardButton("🌐 الموقع الرسمي",       url="https://kaderdz.ru/")],
    ])


def back_kb(to: str = "Start") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=to)]])


def back_to_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="Start")]])


def persistent_menu_kb() -> ReplyKeyboardMarkup:
    """Always-visible bottom keyboard so the user never needs to type /start."""
    return ReplyKeyboardMarkup(
        [["العودة الى القائمة الرئيسية"]],
        resize_keyboard=True,
        is_persistent=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SERVICES
# ══════════════════════════════════════════════════════════════════════════════

def services_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 التسجيل الجامعي",          callback_data="registration_services")],
        [InlineKeyboardButton("💸 تحويل الأموال",            callback_data="money_transfer")],
        [InlineKeyboardButton("📑 ترجمة الوثائق",            callback_data="translation_services")],
        [InlineKeyboardButton("✈️ استقبال في المطار",         callback_data="airport_pickup")],
        [InlineKeyboardButton("🗣️ استشارة",                  callback_data="request_consultation")],
        [InlineKeyboardButton("🔙 رجوع",                     callback_data="Start")],
    ])


def registration_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 تواصل الآن", url="https://t.me/Yousfi_Abdelkader")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="services_menu")],
    ])


def translation_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 اطلب الترجمة الآن", url="https://t.me/Yousfi_Abdelkader")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="services_menu")],
    ])


def money_transfer_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 تواصل للتحويل", url="https://t.me/Yousfi_Abdelkader")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="services_menu")],
    ])


def airport_pickup_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 اطلب الاستقبال", url="https://t.me/Yousfi_Abdelkader")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="services_menu")],
    ])


def consultation_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Yousfi Abdelkader", url="https://t.me/Yousfi_Abdelkader")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="services_menu")],
    ])


# ══════════════════════════════════════════════════════════════════════════════
# CONSULAR SERVICES
# ══════════════════════════════════════════════════════════════════════════════

def consular_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 التسجيل القنصلي",        callback_data="consular_registration")],
        [InlineKeyboardButton("🛂 جواز السفر البيومتري",   callback_data="consular_passport")],
        [InlineKeyboardButton("🪪 الحالة المدنية",          callback_data="consular_civil_status")],
        [InlineKeyboardButton("🪖 الخدمة الوطنية",          callback_data="consular_military")],
        [InlineKeyboardButton("🗳️ الانتخابات",              callback_data="consular_elections")],
        [InlineKeyboardButton("📑 وثائق أخرى",              callback_data="consular_other")],
        [InlineKeyboardButton("📞 التواصل",                 callback_data="consular_contact")],
        [InlineKeyboardButton("🔙 رجوع",                    callback_data="Start")],
    ])


def consular_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="consular_menu")],
    ])


# ══════════════════════════════════════════════════════════════════════════════
# GUIDE
# ══════════════════════════════════════════════════════════════════════════════

def guide_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✈️ قبل الوصول إلى روسيا", callback_data="before_arrival")],
        [InlineKeyboardButton("🏠 بعد الوصول إلى روسيا", callback_data="after_arrival")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="Start")],
    ])


def before_arrival_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 ملف الفيزا",              callback_data="Visa_guide"),
         InlineKeyboardButton("📄 استمارة الفيزا",          callback_data="Visa_Forum")],
        [InlineKeyboardButton("📅 حجز موعد التأشيرة",       callback_data="visa_appointment")],
        [InlineKeyboardButton("📌 عملية التوثيق",           callback_data="Authen_documents")],
        [InlineKeyboardButton("📞 القنصلية الروسية",        callback_data="russian_consulate_contact")],
        [InlineKeyboardButton("🏛️ سفارة الجزائر في روسيا", callback_data="algerian_embassy_russia")],
        [InlineKeyboardButton("✈️ الخطوط الجوية الجزائرية", callback_data="airline_contact")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="guide_menu")],
    ])


def after_arrival_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏦 فتح حساب بنكي",          callback_data="how_to_open_bank_account")],
        [InlineKeyboardButton("📱 الحصول على شريحة SIM",    callback_data="how_to_get_sim")],
        [InlineKeyboardButton("🆔 استخراج ИНН و СНИЛС",    callback_data="how_to_get_tax_social")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="guide_menu")],
    ])


def video_contact_kb(back_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 تواصل معنا", url="https://t.me/Yousfi_Abdelkader")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=back_to)],
    ])


def consult_back_kb(back_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗣️ اطلب استشارة", callback_data="request_consultation")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=back_to)],
    ])


def bank_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏦 فتح حساب Тинькофф", url="https://www.tbank.ru/baf/ucdgm7eo8q")],
        [InlineKeyboardButton("🗣️ اطلب استشارة",      callback_data="request_consultation")],
        [InlineKeyboardButton("🔙 رجوع",               callback_data="after_arrival")],
    ])


def contact_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 تيليغرام",    url="https://t.me/Yousfi_Abdelkader")],
        [InlineKeyboardButton("🌐 الموقع الرسمي", url="https://kaderdz.ru")],
        [InlineKeyboardButton("🔙 رجوع",          callback_data="Start")],
    ])


# ══════════════════════════════════════════════════════════════════════════════
# INQUIRY FORM
# ══════════════════════════════════════════════════════════════════════════════

def inq_target_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👨‍💼 الإدارة",  callback_data="inq_target_admin")],
        [InlineKeyboardButton("👥 الجالية",    callback_data="inq_target_community")],
        [InlineKeyboardButton("❌ إلغاء",       callback_data="inq_cancel")],
    ])


def admin_approve_inq_kb(inq_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ موافقة", callback_data=f"inq_app_{inq_id}"),
        InlineKeyboardButton("❌ رفض",    callback_data=f"inq_rej_{inq_id}"),
    ]])


def inq_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء النموذج", callback_data="inq_cancel")]])


def inquiry_service_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 تسجيل جامعي",    callback_data="inq_svc_registration"),
         InlineKeyboardButton("📑 ترجمة وثائق",    callback_data="inq_svc_translation")],
        [InlineKeyboardButton("🗣️ استشارة عامة",   callback_data="inq_svc_consultation"),
         InlineKeyboardButton("❓ أخرى",            callback_data="inq_svc_other")],
        [InlineKeyboardButton("❌ إلغاء النموذج",   callback_data="inq_cancel")],
    ])


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════════════

def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إحصائيات",           callback_data="adm_stats"),
         InlineKeyboardButton("📤 بث رسالة",           callback_data="adm_broadcast")],
        [InlineKeyboardButton("📋 تصدير المستخدمين",   callback_data="adm_export"),
         InlineKeyboardButton("🔄 تحديث",              callback_data="adm_refresh")],
        [InlineKeyboardButton("🛒 إعلانات السوق",      callback_data="adm_mkt_list"),
         InlineKeyboardButton("🏠 إعلانات السكن",      callback_data="adm_rm_list")],
    ])


def broadcast_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 نص عادي",  callback_data="bc_plain"),
         InlineKeyboardButton("📣 Markdown", callback_data="bc_markdown")],
        [InlineKeyboardButton("❌ إلغاء",    callback_data="bc_cancel")],
    ])


def broadcast_groups_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ نعم، أرسل للمجموعات أيضًا", callback_data="bc_grp_yes")],
        [InlineKeyboardButton("➡️ لا، للمستخدمين فقط",        callback_data="bc_grp_no")],
        [InlineKeyboardButton("❌ إلغاء",                      callback_data="bc_cancel")],
    ])


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ إرسال للجميع", callback_data="bc_confirm"),
         InlineKeyboardButton("❌ إلغاء",        callback_data="bc_cancel")],
    ])


def admin_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع للوحة", callback_data="adm_panel")]])


def admin_approve_mkt_kb(item_id: str) -> InlineKeyboardMarkup:
    """Sent to admin when a new marketplace item arrives — approve or reject."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ موافقة",    callback_data=f"mkt_app_{item_id}"),
        InlineKeyboardButton("❌ رفض",       callback_data=f"mkt_rej_{item_id}"),
    ]])


def admin_active_mkt_kb(item_id: str) -> InlineKeyboardMarkup:
    """Shown after approval — admin can still delete."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗑️ حذف الإعلان المنشور", callback_data=f"mkt_admdel_{item_id}"),
    ]])


def admin_approve_rm_kb(listing_id: str) -> InlineKeyboardMarkup:
    """Sent to admin when a new roommate listing arrives."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ موافقة",    callback_data=f"rm_app_{listing_id}"),
        InlineKeyboardButton("❌ رفض",       callback_data=f"rm_rej_{listing_id}"),
    ]])


def admin_active_rm_kb(listing_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗑️ حذف الإعلان المنشور", callback_data=f"rm_admdel_{listing_id}"),
    ]])


def admin_mkt_list_kb(items: list) -> InlineKeyboardMarkup:
    """Admin view: list all active marketplace items with delete buttons."""
    rows = []
    for item in items[:12]:
        status = "✅" if item["status"] == "approved" else "⏳"
        rows.append([InlineKeyboardButton(
            f"{status} {item['title'][:26]}",
            callback_data=f"adm_mkt_del_{item['id']}",
        )])
    rows.append([InlineKeyboardButton("🔙 لوحة التحكم", callback_data="adm_panel")])
    return InlineKeyboardMarkup(rows)


def admin_rm_list_kb(listings: list) -> InlineKeyboardMarkup:
    """Admin view: list all active roommate listings with delete buttons."""
    rows = []
    for lst in listings[:12]:
        status = "✅" if lst["status"] == "approved" else "⏳"
        rtype  = "🔍" if lst["type"] == "need" else "🏠"
        rows.append([InlineKeyboardButton(
            f"{status} {rtype} {lst['city'][:24]}",
            callback_data=f"adm_rm_del_{lst['id']}",
        )])
    rows.append([InlineKeyboardButton("🔙 لوحة التحكم", callback_data="adm_panel")])
    return InlineKeyboardMarkup(rows)


def admin_report_kb(item_type: str, item_id: str) -> InlineKeyboardMarkup:
    """Admin receives a report — delete or ignore."""
    del_cb = f"mkt_admdel_{item_id}" if item_type == "mkt" else f"rm_admdel_{item_id}"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗑️ حذف الإعلان", callback_data=del_cb),
        InlineKeyboardButton("👁️ تجاهل",        callback_data=f"rpt_ign_{item_id}"),
    ]])


# ══════════════════════════════════════════════════════════════════════════════
# AVITO ALGERIA
# ══════════════════════════════════════════════════════════════════════════════

def avito_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 تصفح الإعلانات",     callback_data="avito_browse")],
        [InlineKeyboardButton("➕ نشر إعلان مجانًا",   callback_data="avito_post")],
        [InlineKeyboardButton("📋 إعلاناتي",            callback_data="avito_myitems")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية",   callback_data="Start")],
    ])


def avito_browse_kb(active_cat: str, index: int, total: int,
                    item_id: str, seller_user_id: int = None) -> InlineKeyboardMarkup:
    """Item card keyboard — nav + category filter chips at the bottom."""

    # ── Navigation row ────────────────────────────────────────────────────────
    nav = []
    if index > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"avito_nav_{active_cat}_{index-1}"))
    nav.append(InlineKeyboardButton(f"📍 {index+1} / {total}", callback_data="noop"))
    if index < total - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"avito_nav_{active_cat}_{index+1}"))

    # ── Category filter chips ─────────────────────────────────────────────────
    def _chip(key: str, label: str) -> InlineKeyboardButton:
        mark = "✓ " if active_cat == key else ""
        return InlineKeyboardButton(f"{mark}{label}", callback_data=f"avito_filter_{key}")

    row_cats1 = [_chip("electronics", "📱"), _chip("furniture", "🪑"), _chip("clothes", "🧥")]
    row_cats2 = [_chip("algerian", "🇩🇿"),  _chip("other", "📦"),      _chip("all", "🔄 الكل")]

    rows = [nav, row_cats1, row_cats2]

    if seller_user_id:
        rows.append([InlineKeyboardButton("💬 تواصل مع البائع",
                                          url=f"tg://user?id={seller_user_id}")])
    rows.append([
        InlineKeyboardButton("🚩 إبلاغ",  callback_data=f"avito_rpt_{item_id}"),
        InlineKeyboardButton("🔙 رجوع",   callback_data="avito_menu"),
    ])
    return InlineKeyboardMarkup(rows)


def avito_empty_kb(active_cat: str) -> InlineKeyboardMarkup:
    """Shown when a filter returns 0 results."""
    def _chip(key, label):
        mark = "✓ " if active_cat == key else ""
        return InlineKeyboardButton(f"{mark}{label}", callback_data=f"avito_filter_{key}")
    return InlineKeyboardMarkup([
        [_chip("electronics", "📱"), _chip("furniture", "🪑"), _chip("clothes", "🧥")],
        [_chip("algerian", "🇩🇿"),  _chip("other", "📦"),      _chip("all", "🔄 الكل")],
        [InlineKeyboardButton("➕ انشر أول إعلان", callback_data="avito_post"),
         InlineKeyboardButton("🔙 رجوع",           callback_data="avito_menu")],
    ])


def avito_report_reason_kb(item_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤥 إعلان مزيف / احتيال", callback_data=f"rpt_mkt_fake_{item_id}")],
        [InlineKeyboardButton("🗑️ سبام / مكرر",          callback_data=f"rpt_mkt_spam_{item_id}")],
        [InlineKeyboardButton("🔞 محتوى غير لائق",       callback_data=f"rpt_mkt_inap_{item_id}")],
        [InlineKeyboardButton("❌ إلغاء",                 callback_data=f"avito_nav_all_0")],
    ])


# ── Posting flow ──────────────────────────────────────────────────────────────

def avito_post_cat_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 إلكترونيات",       callback_data="avito_pcat_electronics")],
        [InlineKeyboardButton("🪑 أثاث",              callback_data="avito_pcat_furniture")],
        [InlineKeyboardButton("🧥 ملابس شتوية",      callback_data="avito_pcat_clothes")],
        [InlineKeyboardButton("🇩🇿 منتجات جزائرية", callback_data="avito_pcat_algerian")],
        [InlineKeyboardButton("📦 أخرى",              callback_data="avito_pcat_other")],
        [InlineKeyboardButton("❌ إلغاء",             callback_data="avito_cancel_post")],
    ])


def avito_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="avito_cancel_post")]])


def avito_skip_photo_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ بدون صورة — تخطي", callback_data="avito_skip_photo")],
        [InlineKeyboardButton("❌ إلغاء",              callback_data="avito_cancel_post")],
    ])


# ── My items ──────────────────────────────────────────────────────────────────

def avito_my_items_kb(items: list) -> InlineKeyboardMarkup:
    rows = []
    for item in items[:10]:
        status = "✅" if item["status"] == "approved" else "⏳"
        rows.append([InlineKeyboardButton(
            f"{status} {item['title'][:28]}",
            callback_data=f"avito_view_{item['id']}",
        )])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="avito_menu")])
    return InlineKeyboardMarkup(rows)


def avito_item_owner_kb(item_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ حذف الإعلان",  callback_data=f"avito_del_{item_id}")],
        [InlineKeyboardButton("🔙 إعلاناتي",      callback_data="avito_myitems")],
    ])


def avito_del_confirm_kb(item_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ نعم، احذف",  callback_data=f"avito_delcfm_{item_id}"),
        InlineKeyboardButton("❌ لا",          callback_data="avito_myitems"),
    ]])


# ══════════════════════════════════════════════════════════════════════════════
# ROOMMATE
# ══════════════════════════════════════════════════════════════════════════════

def roommate_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 تصفح الإعلانات",      callback_data="rm_browse")],
        [InlineKeyboardButton("➕ نشر إعلان سكن",        callback_data="rm_post")],
        [InlineKeyboardButton("📋 إعلاناتي",              callback_data="rm_mylist")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية",     callback_data="Start")],
    ])


def roommate_browse_kb(index: int, total: int, poster_user_id: int = None,
                       filter_city: str = None, filter_metro: str = None,
                       filter_price: str = None) -> InlineKeyboardMarkup:
    """Listing card keyboard — nav + filter chips + contact + report."""

    # ── Navigation ────────────────────────────────────────────────────────────
    nav = []
    if index > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"rm_nav_{index-1}"))
    nav.append(InlineKeyboardButton(f"📍 {index+1} / {total}", callback_data="noop"))
    if index < total - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"rm_nav_{index+1}"))

    # ── Filter chips ──────────────────────────────────────────────────────────
    city_lbl  = MKT.RUSSIAN_CITIES.get(filter_city, "🏙️ المدينة") if filter_city and filter_city != "all" else "🏙️ المدينة"
    metro_lbl = ("🚇 قريب ✓" if filter_metro == "near"
                 else "🚌 بعيد ✓" if filter_metro == "far"
                 else "🚇 المترو")
    price_lbl = ("💰 ↑ سعر" if filter_price == "asc"
                 else "💰 ↓ سعر" if filter_price == "desc"
                 else "💰 السعر")

    rows = [
        nav,
        [InlineKeyboardButton(city_lbl,  callback_data="rm_filt_city"),
         InlineKeyboardButton(metro_lbl, callback_data="rm_filt_metro"),
         InlineKeyboardButton(price_lbl, callback_data="rm_filt_price")],
    ]

    if poster_user_id:
        rows.append([InlineKeyboardButton("💬 تواصل مع صاحب الإعلان",
                                          url=f"tg://user?id={poster_user_id}")])

    # Always show report + back
    rows.append([
        InlineKeyboardButton("🚩 إبلاغ", callback_data=f"rm_rpt_btn"),
        InlineKeyboardButton("🔙 رجوع",  callback_data="rm_menu"),
    ])
    return InlineKeyboardMarkup(rows)


def rm_filter_city_kb(active: str = None) -> InlineKeyboardMarkup:
    def _c(key, label):
        mark = "✓ " if active == key else ""
        return InlineKeyboardButton(f"{mark}{label}", callback_data=f"rm_fc_{key}")
    return InlineKeyboardMarkup([
        [_c("moscow",        "🏙️ موسكو"),        _c("spb",   "🌊 سانت بطرسبورغ")],
        [_c("kazan",         "🕌 كازان"),         _c("yekaterinburg", "⛰️ يكاترينبورغ")],
        [_c("novosibirsk",   "🌲 نوفوسيبيرسك"), _c("voronezh",       "🌻 فورونيج")],
        [_c("rostov",        "🌞 روستوف"),        _c("other",          "📍 أخرى")],
        [InlineKeyboardButton("🔄 الكل — بدون فلتر", callback_data="rm_fc_all")],
        [InlineKeyboardButton("🔙 رجوع",               callback_data="rm_back_browse")],
    ])


def rm_filter_metro_kb(active: str = None) -> InlineKeyboardMarkup:
    def _m(key, label):
        mark = "✓ " if active == key else ""
        return InlineKeyboardButton(f"{mark}{label}", callback_data=f"rm_fm_{key}")
    return InlineKeyboardMarkup([
        [_m("near", "🚇 قريب من المترو"), _m("far", "🚌 بعيد عن المترو")],
        [InlineKeyboardButton("🔄 الكل", callback_data="rm_fm_all")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="rm_back_browse")],
    ])


def rm_filter_price_kb(active: str = None) -> InlineKeyboardMarkup:
    def _p(key, label):
        mark = "✓ " if active == key else ""
        return InlineKeyboardButton(f"{mark}{label}", callback_data=f"rm_fp_{key}")
    return InlineKeyboardMarkup([
        [_p("asc",  "💰 من الأرخص ↑"), _p("desc", "💰 من الأغلى ↓")],
        [InlineKeyboardButton("🔄 بدون ترتيب", callback_data="rm_fp_all")],
        [InlineKeyboardButton("🔙 رجوع",        callback_data="rm_back_browse")],
    ])


def rm_report_reason_kb(listing_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤥 إعلان مزيف / احتيال", callback_data=f"rpt_rm_fake_{listing_id}")],
        [InlineKeyboardButton("🗑️ سبام / مكرر",          callback_data=f"rpt_rm_spam_{listing_id}")],
        [InlineKeyboardButton("🔞 محتوى غير لائق",       callback_data=f"rpt_rm_inap_{listing_id}")],
        [InlineKeyboardButton("❌ إلغاء",                 callback_data="rm_back_browse")],
    ])


# ── Posting flow ──────────────────────────────────────────────────────────────

def roommate_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 أبحث عن شريك سكن",   callback_data="rm_type_need")],
        [InlineKeyboardButton("🏠 عندي غرفة / وحدة",   callback_data="rm_type_have")],
        [InlineKeyboardButton("❌ إلغاء",                callback_data="rm_cancel_post")],
    ])


def roommate_room_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛏️ غرفة في شقة",  callback_data="rm_rtype_room1")],
        [InlineKeyboardButton("🏠 استوديو",       callback_data="rm_rtype_studio")],
        [InlineKeyboardButton("❌ إلغاء",          callback_data="rm_cancel_post")],
    ])


def roommate_city_kb() -> InlineKeyboardMarkup:
    """City selection during roommate posting flow."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏙️ موسكو",              callback_data="rm_city_moscow"),
         InlineKeyboardButton("🌊 سانت بطرسبورغ",       callback_data="rm_city_spb")],
        [InlineKeyboardButton("🕌 كازان",               callback_data="rm_city_kazan"),
         InlineKeyboardButton("⛰️ يكاترينبورغ",        callback_data="rm_city_yekaterinburg")],
        [InlineKeyboardButton("🌲 نوفوسيبيرسك",        callback_data="rm_city_novosibirsk"),
         InlineKeyboardButton("🌻 فورونيج",             callback_data="rm_city_voronezh")],
        [InlineKeyboardButton("🌞 روستوف",              callback_data="rm_city_rostov"),
         InlineKeyboardButton("📍 مدينة أخرى",          callback_data="rm_city_other")],
        [InlineKeyboardButton("❌ إلغاء",               callback_data="rm_cancel_post")],
    ])


def roommate_metro_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚇 قريب من المترو",  callback_data="rm_metro_near")],
        [InlineKeyboardButton("🚌 بعيد عن المترو",  callback_data="rm_metro_far")],
        [InlineKeyboardButton("❌ إلغاء",            callback_data="rm_cancel_post")],
    ])


def roommate_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="rm_cancel_post")]])


# ── My listings ───────────────────────────────────────────────────────────────

def roommate_my_kb(listings: list) -> InlineKeyboardMarkup:
    rows = []
    for lst in listings[:10]:
        status = "✅" if lst["status"] == "approved" else "⏳"
        rtype  = "🔍 يبحث" if lst["type"] == "need" else "🏠 غرفة"
        rows.append([InlineKeyboardButton(
            f"{status} {rtype} — {lst['city'][:22]}",
            callback_data=f"rm_view_{lst['id']}",
        )])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="rm_menu")])
    return InlineKeyboardMarkup(rows)


def roommate_item_owner_kb(listing_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ حذف الإعلان",  callback_data=f"rm_del_{listing_id}")],
        [InlineKeyboardButton("🔙 إعلاناتي",      callback_data="rm_mylist")],
    ])


def roommate_del_confirm_kb(listing_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ نعم، احذف",  callback_data=f"rm_delcfm_{listing_id}"),
        InlineKeyboardButton("❌ لا",          callback_data="rm_mylist"),
    ]])


# ══════════════════════════════════════════════════════════════════════════════
# TRAVEL COMPANION — هبطلي ولا طلعلي معاك
# ══════════════════════════════════════════════════════════════════════════════

def travel_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ أضف رحلتك",                   callback_data="trv_post_choose")],
        [InlineKeyboardButton("🇷🇺➡️🇩🇿 من موسكو إلى الجزائر", callback_data="trv_post_msk_alg")],
        [InlineKeyboardButton("🇩🇿➡️🇷🇺 من الجزائر إلى موسكو", callback_data="trv_post_alg_msk")],
        [InlineKeyboardButton("📋 رحلاتي",                      callback_data="trv_mylist")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية",           callback_data="Start")],
    ])


def trv_direction_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇩🇿➡️🇷🇺 من الجزائر إلى موسكو", callback_data="trv_dir_alg_msk")],
        [InlineKeyboardButton("🇷🇺➡️🇩🇿 من موسكو إلى الجزائر", callback_data="trv_dir_msk_alg")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="trv_cancel_post")],
    ])


def trv_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="trv_cancel_post")]])


def trv_skip_flight_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ تخطي", callback_data="trv_skip_flight")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="trv_cancel_post")],
    ])


def trv_my_kb(posts: list) -> InlineKeyboardMarkup:
    rows = []
    for p in posts[:10]:
        status = "✅" if p["status"] == "approved" else "⏳"
        rows.append([InlineKeyboardButton(
            f"{status} {p['date']} — {p['city'][:18]}",
            callback_data=f"trv_view_{p['id']}",
        )])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="trv_menu")])
    return InlineKeyboardMarkup(rows)


def trv_item_owner_kb(post_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ حذف الرحلة",  callback_data=f"trv_del_{post_id}")],
        [InlineKeyboardButton("🔙 رحلاتي",       callback_data="trv_mylist")],
    ])


def trv_del_confirm_kb(post_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ نعم، احذف",  callback_data=f"trv_delcfm_{post_id}"),
        InlineKeyboardButton("❌ لا",          callback_data="trv_mylist"),
    ]])


def admin_approve_trv_kb(post_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ موافقة", callback_data=f"trv_app_{post_id}"),
        InlineKeyboardButton("❌ رفض",    callback_data=f"trv_rej_{post_id}"),
    ]])


def admin_active_trv_kb(post_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ تمت الموافقة", callback_data="noop")]])
