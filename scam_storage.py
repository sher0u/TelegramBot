# -*- coding: utf-8 -*-
"""Storage layer — شرلوك الجزائري (scam/thief check & report)."""
import json, os, re, uuid
from datetime import datetime

_DIR                 = os.path.dirname(__file__)
REPORTS_FILE         = os.path.join(_DIR, "scam_reports.json")
ACCESS_REQUESTS_FILE = os.path.join(_DIR, "scam_access_requests.json")
QUOTA_FILE           = os.path.join(_DIR, "scam_search_quota.json")

DAILY_SEARCH_LIMIT = 10

HARD_FIELDS = ["telegram_user_id", "phone", "ccp", "card", "passport", "cle_rip"]
NAME_FIELDS = ["full_name", "surname", "full_name_ru"]

# Known trusted guarantors — shown as a positive result instead of a scam match.
GUARANTORS = [
    {
        "name": "Yousfi", "surname": "Abdelkader", "full_name": "Yousfi Abdelkader",
        "full_name_ru": "Юсфи Абделькадер", "phone": "+79158846143",
        "contact": "https://t.me/Yousfi_Abdelkader", "contact_label": "تيليجرام",
    },
    {
        "name": "Derouiche", "surname": "Abdennour", "full_name": "Derouiche Abdennour",
        "full_name_ru": "Деруиш Абденнур", "phone": "+79967996510",
        "contact": "https://wa.me/79967996510", "contact_label": "واتساب",
    },
]


def normalize_phone(country: str, raw: str) -> str:
    """Forces a phone into +213... (Algeria) or +7... (Russia) format,
    accepting the common local shorthand (leading 0 for DZ, leading 8 for RU)."""
    digits = re.sub(r"\D", "", raw or "")
    if country == "dz":
        if digits.startswith("213"):
            digits = digits[3:]
        elif digits.startswith("0"):
            digits = digits[1:]
        return "+213" + digits
    if digits.startswith("8") and len(digits) == 11:
        digits = digits[1:]
    elif digits.startswith("7"):
        digits = digits[1:]
    return "+7" + digits


def normalize_phone_auto(raw: str) -> str:
    """Best-effort normalization when no explicit country is given (bot/admin
    text entry) — infers DZ vs RU from the digits, falls back to the trimmed
    input unchanged if it doesn't look like a recognizable phone shape."""
    raw = raw or ""
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return raw.strip()
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("213"):
        return "+213" + digits[3:]
    if digits.startswith("0") and len(digits) in (9, 10):
        return "+213" + digits[1:]
    if digits.startswith("7") and len(digits) == 11:
        return "+7" + digits[1:]
    if digits.startswith("8") and len(digits) == 11:
        return "+7" + digits[1:]
    if len(digits) == 10 and digits.startswith("9"):
        return "+7" + digits
    return raw.strip()


def _phone_key(value) -> str:
    """Canonical form for phone comparisons — the last 9 digits, so the same
    number matches regardless of +213/0 (DZ) or +7/8 (RU) prefix style."""
    digits = re.sub(r"\D", "", str(value or ""))
    return digits[-9:] if len(digits) >= 9 else digits


def _matches_field(stored: dict, field: str, value) -> bool:
    if field == "phone":
        qk = _phone_key(value)
        return bool(qk) and qk == _phone_key(stored.get("phone"))
    return _norm(value) == _norm(stored.get(field))


def check_guarantor(value: str) -> dict | None:
    v = _norm(value)
    vphone = _phone_key(value)
    if not v:
        return None
    for g in GUARANTORS:
        if v in (_norm(g["full_name"]), _norm(g["full_name_ru"]), _norm(g["name"]), _norm(g["surname"])):
            return g
        if vphone and vphone == _phone_key(g["phone"]):
            return g
    return None

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load(path: str, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def _save(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _new_id() -> str:
    return str(uuid.uuid4())[:8]

def _norm(s) -> str:
    return str(s or "").strip().lower().replace(" ", "")

# ── Reports ───────────────────────────────────────────────────────────────────

def get_all_reports() -> list:
    return _load(REPORTS_FILE, [])

def save_all_reports(reports: list) -> None:
    _save(REPORTS_FILE, reports)

def get_approved_reports() -> list:
    return [r for r in get_all_reports() if r["status"] == "approved"]

def get_report_by_id(report_id: str) -> dict | None:
    return next((r for r in get_all_reports() if r["id"] == report_id), None)

def get_reporter_reports(user_id: int) -> list:
    return [r for r in get_all_reports() if r["reporter_user_id"] == user_id]

def add_report(reporter_user_id: int, reporter_username: str, reporter_first_name: str,
               full_name: str, surname: str, full_name_ru: str, date_of_birth: str, telegram_user_id: str,
               phone: str, ccp: str, cle_rip: str, card: str, passport: str,
               reason: str, photos: list) -> dict:
    reports = get_all_reports()
    report = {
        "id":                  _new_id(),
        "reporter_user_id":    reporter_user_id,
        "reporter_username":   reporter_username or "",
        "reporter_first_name": reporter_first_name or "",
        "full_name":           full_name or "",
        "surname":             surname or "",
        "full_name_ru":        full_name_ru or "",
        "date_of_birth":       date_of_birth or "",
        "telegram_user_id":    telegram_user_id or "",
        "phone":               normalize_phone_auto(phone) if phone else "",
        "ccp":                 ccp or "",
        "cle_rip":             cle_rip or "",
        "card":                card or "",
        "passport":            passport or "",
        "reason":              reason or "",
        "photos":              photos or [],
        "status":              "pending",
        "created_at":          datetime.now().isoformat(),
    }
    reports.append(report)
    save_all_reports(reports)
    return report

def approve_report(report_id: str) -> None:
    reports = get_all_reports()
    for r in reports:
        if r["id"] == report_id:
            r["status"] = "approved"
            break
    save_all_reports(reports)

def reject_report(report_id: str) -> None:
    reports = get_all_reports()
    for r in reports:
        if r["id"] == report_id:
            r["status"] = "rejected"
            break
    save_all_reports(reports)

def delete_report(report_id: str) -> None:
    save_all_reports([r for r in get_all_reports() if r["id"] != report_id])

EDITABLE_FIELDS = ["full_name", "surname", "full_name_ru", "date_of_birth", "telegram_user_id",
                   "phone", "ccp", "cle_rip", "card", "passport", "reason"]

def update_report(report_id: str, fields: dict) -> dict | None:
    reports = get_all_reports()
    for r in reports:
        if r["id"] == report_id:
            for k in EDITABLE_FIELDS:
                if k in fields:
                    v = fields[k] or ""
                    r[k] = normalize_phone_auto(v) if (k == "phone" and v) else v
            save_all_reports(reports)
            return r
    return None

def get_pending_reports() -> list:
    return [r for r in get_all_reports() if r["status"] == "pending"]

# ── Search ────────────────────────────────────────────────────────────────────

def _mask(value: str) -> str:
    value = str(value or "")
    if len(value) <= 4:
        return "****"
    return "**** " + value[-4:]

def masked_report(r: dict) -> dict:
    return {
        "id": r["id"],
        "full_name": r["full_name"],
        "surname": r["surname"],
        "full_name_ru": r.get("full_name_ru", ""),
        "date_of_birth": r["date_of_birth"],
        "telegram_user_id": r["telegram_user_id"],
        "phone": r["phone"],
        "ccp": _mask(r["ccp"]),
        "cle_rip": _mask(r.get("cle_rip", "")),
        "card": _mask(r["card"]),
        "passport": _mask(r["passport"]),
        "reason": r["reason"],
        "photos": r["photos"],
        "created_at": r["created_at"],
    }

def _candidates(matches: list) -> list:
    return [{
        "id": r["id"],
        "full_name": r["full_name"],
        "surname": r["surname"],
        "full_name_ru": r.get("full_name_ru", ""),
        "date_of_birth": r["date_of_birth"],
    } for r in matches]


def search_reports(query: dict) -> dict:
    """Returns {"mode": "detail"|"candidates"|"none"|"guarantor", "results": [...]}.
    Hard identifiers (phone/ccp/card/...) are tried first, but a mismatch there
    doesn't hide a legitimate name match if a name was also given — it falls
    back to name-based candidates instead of returning "none" outright."""
    q = {k: v for k, v in query.items() if v}

    for v in q.values():
        g = check_guarantor(v)
        if g:
            return {"mode": "guarantor", "results": [g]}

    approved = get_approved_reports()
    hard = {k: v for k, v in q.items() if k in HARD_FIELDS}
    name_qs = {k: v for k, v in q.items() if k in NAME_FIELDS}

    if hard:
        matches = [r for r in approved if any(_matches_field(r, k, v) for k, v in hard.items())]
        if matches:
            return {"mode": "detail", "results": [masked_report(r) for r in matches]}

    if not name_qs:
        return {"mode": "none", "results": []}

    matches = [r for r in approved if any(_matches_field(r, k, v) for k, v in name_qs.items())]
    if not matches:
        return {"mode": "none", "results": []}
    return {"mode": "candidates", "results": _candidates(matches)}

def smart_search(value: str) -> dict:
    """Bot chat entry point — a single free-text value, unknown which field it is.
    Tries it against every hard identifier first, then falls back to a name match."""
    if not _norm(value):
        return {"mode": "none", "results": []}

    g = check_guarantor(value)
    if g:
        return {"mode": "guarantor", "results": [g]}

    approved = get_approved_reports()

    matches = [r for r in approved if any(_matches_field(r, f, value) for f in HARD_FIELDS)]
    if matches:
        return {"mode": "detail", "results": [masked_report(r) for r in matches]}

    matches = [r for r in approved if any(_matches_field(r, f, value) for f in NAME_FIELDS)]
    if not matches:
        return {"mode": "none", "results": []}
    return {"mode": "candidates", "results": _candidates(matches)}

def get_report_detail(report_id: str) -> dict | None:
    r = get_report_by_id(report_id)
    if not r or r["status"] != "approved":
        return None
    return masked_report(r)

# ── Access requests ───────────────────────────────────────────────────────────

def get_all_access_requests() -> list:
    return _load(ACCESS_REQUESTS_FILE, [])

def save_all_access_requests(reqs: list) -> None:
    _save(ACCESS_REQUESTS_FILE, reqs)

def get_access_request_by_id(req_id: str) -> dict | None:
    return next((a for a in get_all_access_requests() if a["id"] == req_id), None)

def add_access_request(report_id: str, requester_user_id: int, requester_username: str,
                        reason: str) -> dict:
    reqs = get_all_access_requests()
    req = {
        "id":                 _new_id(),
        "report_id":          report_id,
        "requester_user_id":  requester_user_id,
        "requester_username": requester_username or "",
        "reason":             reason or "",
        "status":             "pending",
        "created_at":         datetime.now().isoformat(),
    }
    reqs.append(req)
    save_all_access_requests(reqs)
    return req

def approve_access(req_id: str) -> None:
    reqs = get_all_access_requests()
    for a in reqs:
        if a["id"] == req_id:
            a["status"] = "approved"
            break
    save_all_access_requests(reqs)

def reject_access(req_id: str) -> None:
    reqs = get_all_access_requests()
    for a in reqs:
        if a["id"] == req_id:
            a["status"] = "rejected"
            break
    save_all_access_requests(reqs)

# ── Search quota ──────────────────────────────────────────────────────────────

def check_and_bump_quota(user_id: int) -> bool:
    """Returns True if the search is allowed (and counts it), False if over the daily limit."""
    quota = _load(QUOTA_FILE, {})
    key = f"{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
    count = quota.get(key, 0)
    if count >= DAILY_SEARCH_LIMIT:
        return False
    quota[key] = count + 1
    _save(QUOTA_FILE, quota)
    return True
