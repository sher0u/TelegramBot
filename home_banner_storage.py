# -*- coding: utf-8 -*-
"""Storage — temporary home-screen banner override for the mini app (set via broadcast)."""
import json, os
from datetime import datetime, timedelta

_DIR = os.path.dirname(__file__)
BANNER_FILE = os.path.join(_DIR, "home_banner.json")


def set_banner(text: str, hours: int = 24) -> None:
    data = {
        "text": text,
        "expires_at": (datetime.now() + timedelta(hours=hours)).isoformat(),
    }
    with open(BANNER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_active_banner() -> str | None:
    if not os.path.exists(BANNER_FILE):
        return None
    try:
        with open(BANNER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if datetime.fromisoformat(data["expires_at"]) > datetime.now():
            return data["text"]
    except Exception:
        pass
    return None
