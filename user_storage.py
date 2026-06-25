# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime, timedelta

USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")


def load_users() -> dict:
    """Return {str(user_id): {joined, name, username}} — migrates old list format."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {str(uid): {"joined": None, "name": None, "username": None} for uid in data}
        return data
    except Exception:
        return {}


def save_users(users: dict) -> None:
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[storage] error saving users: {e}")


def add_user(users: dict, user_id: int, first_name: str = None, username: str = None) -> bool:
    """Add user if new. Returns True if this is a new user."""
    key = str(user_id)
    if key in users:
        return False
    users[key] = {
        "joined": datetime.now().isoformat(),
        "name": first_name,
        "username": username,
    }
    return True


def get_user_ids(users: dict) -> list[int]:
    return [int(k) for k in users]


def snooze_teasers(users: dict, user_id: int, days: int = 7) -> None:
    """Suppress 'new listing' teaser broadcasts to this user for N days."""
    key = str(user_id)
    if key in users:
        users[key]["teasers_snoozed_until"] = (datetime.now() + timedelta(days=days)).isoformat()
        save_users(users)


def is_teaser_snoozed(users: dict, user_id: int) -> bool:
    data = users.get(str(user_id))
    if not data:
        return False
    until = data.get("teasers_snoozed_until")
    if not until:
        return False
    try:
        return datetime.fromisoformat(until) > datetime.now()
    except ValueError:
        return False


def set_verified(users: dict, user_id: int, verified: bool) -> None:
    key = str(user_id)
    if key in users:
        users[key]["verified"] = verified
        save_users(users)


def is_verified(users: dict, user_id: int) -> bool:
    data = users.get(str(user_id))
    return bool(data and data.get("verified"))


def search_users(users: dict, query: str) -> list[dict]:
    """Search by user ID, username, or name (case-insensitive substring match)."""
    q = (query or "").strip().lower().lstrip("@")
    if not q:
        return []
    results = []
    for uid, data in users.items():
        name     = (data.get("name") or "").lower()
        username = (data.get("username") or "").lower()
        if q in uid or q in name or q in username:
            results.append({
                "user_id":  int(uid),
                "name":     data.get("name"),
                "username": data.get("username"),
                "joined":   data.get("joined"),
                "verified": bool(data.get("verified")),
            })
    return results[:30]


def get_stats(users: dict) -> dict:
    now = datetime.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    new_today = new_week = 0
    for data in users.values():
        joined_str = data.get("joined")
        if not joined_str:
            continue
        try:
            joined = datetime.fromisoformat(joined_str)
            if joined.date() == today:
                new_today += 1
            if joined >= week_ago:
                new_week += 1
        except ValueError:
            pass
    return {"total": len(users), "new_today": new_today, "new_week": new_week}
