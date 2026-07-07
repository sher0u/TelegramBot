# -*- coding: utf-8 -*-
"""Storage layer — Travel companion posts (هبطلي ولا طلعلي معاك)."""
import json, os, uuid
from datetime import datetime, timedelta

_DIR        = os.path.dirname(__file__)
TRAVEL_FILE = os.path.join(_DIR, "travel.json")

ROUTES = {
    "alg_to_msk": "🇩🇿 ➡️ 🇷🇺   من الجزائر إلى روسيا",
    "msk_to_alg": "🇷🇺 ➡️ 🇩🇿   من روسيا إلى الجزائر",
}

ARCHIVE_AFTER_DAYS = 180  # keep an expired post for 6 months before permanent deletion


def parse_date(date_str: str) -> datetime | None:
    """Parse a travel date entered as DD/MM/YYYY, DD.MM.YYYY, or ISO YYYY-MM-DD."""
    date_str = (date_str or "").strip()
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load() -> list:
    if os.path.exists(TRAVEL_FILE):
        with open(TRAVEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def _save(data: list) -> None:
    with open(TRAVEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _new_id() -> str:
    return str(uuid.uuid4())[:8]

def _expires() -> str:
    return (datetime.now() + timedelta(days=30)).isoformat()

# ── Travel posts ──────────────────────────────────────────────────────────────

def get_all_posts() -> list:
    return _load()

def save_all_posts(posts: list) -> None:
    _save(posts)

def get_approved_posts() -> list:
    return [p for p in get_all_posts() if p["status"] == "approved"]

def get_approved_posts_by_route(route: str) -> list:
    return [p for p in get_approved_posts() if p["route"] == route]

def get_post_by_id(post_id: str) -> dict | None:
    return next((p for p in get_all_posts() if p["id"] == post_id), None)

def get_user_posts(user_id: int) -> list:
    return [p for p in get_all_posts() if p["user_id"] == user_id]

def add_post(user_id: int, username: str, first_name: str,
             route: str, date: str, flight: str, city: str,
             contact: str, note: str) -> dict:
    posts = get_all_posts()
    post = {
        "id":          _new_id(),
        "user_id":     user_id,
        "username":    username or "",
        "first_name":  first_name or "",
        "route":       route,
        "date":        date,
        "flight":      flight or "—",
        "city":        city,
        "contact":     contact,
        "note":        note,
        "status":      "pending",
        "created_at":  datetime.now().isoformat(),
        "expires_at":  _expires(),
    }
    posts.append(post)
    save_all_posts(posts)
    return post

def approve_post(post_id: str) -> None:
    posts = get_all_posts()
    for p in posts:
        if p["id"] == post_id:
            p["status"] = "approved"
            break
    save_all_posts(posts)

def delete_post(post_id: str) -> None:
    save_all_posts([p for p in get_all_posts() if p["id"] != post_id])


def run_maintenance() -> None:
    """Archive approved posts whose travel date has passed, and permanently
    delete posts that have been archived for longer than ARCHIVE_AFTER_DAYS."""
    posts = get_all_posts()
    now = datetime.now()
    kept = []
    changed = False

    for p in posts:
        if p["status"] == "approved":
            d = parse_date(p.get("date", ""))
            if d and d.date() < now.date():
                p["status"] = "archived"
                p["archived_at"] = now.isoformat()
                changed = True

        if p["status"] == "archived":
            archived_at = p.get("archived_at")
            if archived_at:
                try:
                    if datetime.fromisoformat(archived_at) + timedelta(days=ARCHIVE_AFTER_DAYS) < now:
                        changed = True
                        continue  # drop — past retention window
                except ValueError:
                    pass

        kept.append(p)

    if changed:
        save_all_posts(kept)
