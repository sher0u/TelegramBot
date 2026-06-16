# -*- coding: utf-8 -*-
"""Storage layer — Avito Algeria marketplace & Roommate listings."""
import json, os, uuid
from datetime import datetime, timedelta

_DIR             = os.path.dirname(__file__)
MARKETPLACE_FILE = os.path.join(_DIR, "marketplace.json")
ROOMMATE_FILE    = os.path.join(_DIR, "roommate.json")

# ── Lookup tables ─────────────────────────────────────────────────────────────

CATEGORIES = {
    "electronics": "📱 إلكترونيات",
    "furniture":   "🪑 أثاث",
    "clothes":     "🧥 ملابس شتوية",
    "algerian":    "🇩🇿 منتجات جزائرية",
    "other":       "📦 أخرى",
}

ROOMMATE_TYPES = {
    "need": "🔍 أبحث عن شريك سكن",
    "have": "🏠 عندي غرفة / وحدة",
}

ROOM_TYPES = {
    "room1":  "🛏️ غرفة في شقة",
    "studio": "🏠 استوديو",
}

METRO_DISTANCES = {
    "near": "🚇 قريب من المترو",
    "far":  "🚌 بعيد عن المترو",
}

RUSSIAN_CITIES = {
    "moscow":        "🏙️ موسكو",
    "spb":           "🌊 سانت بطرسبورغ",
    "kazan":         "🕌 كازان",
    "yekaterinburg": "⛰️ يكاترينبورغ",
    "novosibirsk":   "🌲 نوفوسيبيرسك",
    "voronezh":      "🌻 فورونيج",
    "rostov":        "🌞 روستوف",
    "other":         "📍 مدينة أخرى",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load(path: str) -> list:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def _save(path: str, data: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _new_id() -> str:
    return str(uuid.uuid4())[:8]

def _expires() -> str:
    return (datetime.now() + timedelta(days=30)).isoformat()

def _price_key(price_str: str) -> float:
    """Extract first number from price string for sorting."""
    import re
    nums = re.findall(r"[\d]+", str(price_str).replace(" ", ""))
    return float(nums[0]) if nums else 0.0

# ── Marketplace ───────────────────────────────────────────────────────────────

def get_all_items() -> list:
    return _load(MARKETPLACE_FILE)

def save_all_items(items: list) -> None:
    _save(MARKETPLACE_FILE, items)

def get_approved_items() -> list:
    return [i for i in get_all_items() if i["status"] == "approved"]

def get_items_by_category(category: str) -> list:
    return [i for i in get_all_items()
            if i["category"] == category and i["status"] == "approved"]

def get_item_by_id(item_id: str) -> dict | None:
    return next((i for i in get_all_items() if i["id"] == item_id), None)

def get_user_items(user_id: int) -> list:
    return [i for i in get_all_items() if i["user_id"] == user_id]

def add_item(user_id: int, username: str, first_name: str,
             category: str, title: str, price: str,
             city: str, description: str, photo_id: str = None) -> dict:
    items = get_all_items()
    item = {
        "id":          _new_id(),
        "user_id":     user_id,
        "username":    username or "",
        "first_name":  first_name or "",
        "category":    category,
        "title":       title,
        "price":       price,
        "city":        city,
        "description": description,
        "photo_id":    photo_id,
        "status":      "pending",
        "reports":     0,
        "created_at":  datetime.now().isoformat(),
        "expires_at":  _expires(),
    }
    items.append(item)
    save_all_items(items)
    return item

def approve_item(item_id: str) -> None:
    items = get_all_items()
    for i in items:
        if i["id"] == item_id:
            i["status"] = "approved"
            break
    save_all_items(items)

def delete_item(item_id: str) -> None:
    save_all_items([i for i in get_all_items() if i["id"] != item_id])

def report_item(item_id: str) -> int:
    """Increment report count. Returns new count."""
    items = get_all_items()
    count = 0
    for i in items:
        if i["id"] == item_id:
            i["reports"] = i.get("reports", 0) + 1
            count = i["reports"]
            break
    save_all_items(items)
    return count

# ── Roommate ──────────────────────────────────────────────────────────────────

def get_all_listings() -> list:
    return _load(ROOMMATE_FILE)

def save_all_listings(listings: list) -> None:
    _save(ROOMMATE_FILE, listings)

def get_approved_listings() -> list:
    return [l for l in get_all_listings() if l["status"] == "approved"]

def get_listing_by_id(listing_id: str) -> dict | None:
    return next((l for l in get_all_listings() if l["id"] == listing_id), None)

def get_user_listings(user_id: int) -> list:
    return [l for l in get_all_listings() if l["user_id"] == user_id]

def add_listing(user_id: int, username: str, first_name: str,
                listing_type: str, room_type: str, city: str, city_key: str,
                price: str, metro_distance: str, description: str) -> dict:
    listings = get_all_listings()
    listing = {
        "id":             _new_id(),
        "user_id":        user_id,
        "username":       username or "",
        "first_name":     first_name or "",
        "type":           listing_type,
        "room_type":      room_type,
        "city":           city,
        "city_key":       city_key,
        "price":          price,
        "metro_distance": metro_distance,
        "description":    description,
        "status":         "pending",
        "reports":        0,
        "created_at":     datetime.now().isoformat(),
        "expires_at":     _expires(),
    }
    listings.append(listing)
    save_all_listings(listings)
    return listing

def approve_listing(listing_id: str) -> None:
    listings = get_all_listings()
    for l in listings:
        if l["id"] == listing_id:
            l["status"] = "approved"
            break
    save_all_listings(listings)

def delete_listing(listing_id: str) -> None:
    save_all_listings([l for l in get_all_listings() if l["id"] != listing_id])

def report_listing(listing_id: str) -> int:
    listings = get_all_listings()
    count = 0
    for l in listings:
        if l["id"] == listing_id:
            l["reports"] = l.get("reports", 0) + 1
            count = l["reports"]
            break
    save_all_listings(listings)
    return count

def filter_listings(city_key: str = None, metro: str = None,
                    sort_price: str = None) -> list:
    """Return approved listings with optional filters applied."""
    result = get_approved_listings()
    if city_key and city_key != "all":
        result = [l for l in result if l.get("city_key") == city_key]
    if metro and metro != "all":
        result = [l for l in result if l.get("metro_distance") == metro]
    if sort_price == "asc":
        result = sorted(result, key=lambda l: _price_key(l["price"]))
    elif sort_price == "desc":
        result = sorted(result, key=lambda l: _price_key(l["price"]), reverse=True)
    return result
