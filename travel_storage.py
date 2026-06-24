# -*- coding: utf-8 -*-
"""Storage layer — Travel companion posts (هبطلي ولا طلعلي معاك)."""
import json, os, uuid
from datetime import datetime, timedelta

_DIR        = os.path.dirname(__file__)
TRAVEL_FILE = os.path.join(_DIR, "travel.json")

ROUTES = {
    "alg_to_msk": "🇩🇿➡️🇷🇺 من الجزائر إلى موسكو",
    "msk_to_alg": "🇷🇺➡️🇩🇿 من موسكو إلى الجزائر",
}

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
