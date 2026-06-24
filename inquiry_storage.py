# -*- coding: utf-8 -*-
"""Storage layer — community-routed inquiries (نموذج استفسار → الجالية)."""
import json, os, uuid
from datetime import datetime

_DIR        = os.path.dirname(__file__)
INQUIRY_FILE = os.path.join(_DIR, "community_inquiries.json")


def _load() -> list:
    if os.path.exists(INQUIRY_FILE):
        with open(INQUIRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def _save(data: list) -> None:
    with open(INQUIRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _new_id() -> str:
    return str(uuid.uuid4())[:8]


def get_all() -> list:
    return _load()

def get_by_id(inq_id: str) -> dict | None:
    return next((i for i in get_all() if i["id"] == inq_id), None)

def add_inquiry(user_id: int, username: str, first_name: str,
                name: str, phone: str, service: str, notes: str) -> dict:
    items = get_all()
    item = {
        "id":         _new_id(),
        "user_id":    user_id,
        "username":   username or "",
        "first_name": first_name or "",
        "name":       name,
        "phone":      phone,
        "service":    service,
        "notes":      notes,
        "status":     "pending",
        "created_at": datetime.now().isoformat(),
    }
    items.append(item)
    _save(items)
    return item

def approve_inquiry(inq_id: str) -> None:
    items = get_all()
    for i in items:
        if i["id"] == inq_id:
            i["status"] = "approved"
            break
    _save(items)

def delete_inquiry(inq_id: str) -> None:
    _save([i for i in get_all() if i["id"] != inq_id])
