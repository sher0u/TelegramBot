# -*- coding: utf-8 -*-
"""Storage layer — شرلوك الجزائري (scam/thief check & report)."""
import json, os, re, uuid, unicodedata
from datetime import datetime
from difflib import SequenceMatcher

_DIR                 = os.path.dirname(__file__)
REPORTS_FILE         = os.path.join(_DIR, "scam_reports.json")
ACCESS_REQUESTS_FILE = os.path.join(_DIR, "scam_access_requests.json")
QUOTA_FILE           = os.path.join(_DIR, "scam_search_quota.json")
SEARCH_LOG_FILE      = os.path.join(_DIR, "scam_search_log.json")

DAILY_SEARCH_LIMIT = 10
MAX_QUERY_LEN      = 200   # anything longer is junk, not an identifier
MAX_CANDIDATES     = 20    # cap name-match lists shown to the user

# ── Search-based risk ("detective") tuning ────────────────────────────────────
# Every time someone checks a phone/CCP/card/passport/Telegram id, we log it.
# Many DIFFERENT people checking the same number is itself a danger signal —
# it means that person is approaching a lot of people — even before anyone files
# a formal report. These constants turn that into a risk %.
SUSPICIOUS_MIN_SEARCHERS = 3   # need this many distinct checkers before we warn
SEARCH_LOG_MAX_USERS     = 500 # cap stored searcher-ids per identifier

HARD_FIELDS = ["telegram_user_id", "phone", "ccp", "card", "passport", "cle_rip"]
NAME_FIELDS = ["full_name", "surname", "full_name_ru"]

# Known trusted guarantors — shown as a positive result instead of a scam match.
GUARANTORS = [
    {
        "name": "Yousfi", "surname": "Abdelkader", "full_name": "Yousfi Abdelkader",
        "full_name_ru": "Юсфи Абделькадер", "full_name_ar": "يوسفي عبدالقادر", "phone": "+79158846143",
        "contact": "https://t.me/Yousfi_Abdelkader", "contact_label": "تيليجرام",
    },
    {
        "name": "Derouiche", "surname": "Abdennour", "full_name": "Derouiche Abdennour",
        "full_name_ru": "Деруиш Абденнур", "phone": "+79967996510",
        "contact": "https://wa.me/79967996510", "contact_label": "واتساب",
    },
]

# ── Text / identifier normalization ──────────────────────────────────────────
# Users type the same fact in many shapes: Arabic-Indic digits (٠١٢٣), Arabic
# letters with diacritics or alef/ya/ta-marbuta variants, phone numbers with
# spaces and dashes, @usernames or t.me links, dates in any separator style.
# Every comparison goes through a canonical key so all of those collide.

_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_AR_NOISE  = re.compile(r"[ً-ٰٟـ]")  # tashkeel + tatweel
_AR_LETTERS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ة": "ه", "ى": "ي", "ئ": "ي", "ؤ": "و"})

_FUZZY_RATIO = 0.85


def _norm_text(s) -> str:
    """Casefolded, Arabic-normalized text with single spaces preserved."""
    s = unicodedata.normalize("NFKC", str(s or ""))
    s = s.translate(_AR_DIGITS)
    s = _AR_NOISE.sub("", s)
    s = s.translate(_AR_LETTERS)
    return re.sub(r"\s+", " ", s).strip().casefold()


def _norm(s) -> str:
    """Compact form (no spaces) for exact comparisons."""
    return _norm_text(s).replace(" ", "")


def _digits(value) -> str:
    return re.sub(r"\D", "", str(value or "").translate(_AR_DIGITS))


def _phone_key(value) -> str:
    """Canonical form for phone comparisons — the last 9 digits, so the same
    number matches regardless of +213/0 (DZ) or +7/8 (RU) prefix style."""
    digits = _digits(value)
    return digits[-9:] if len(digits) >= 9 else digits


def _id_key(value) -> str:
    """Canonical form for CCP / card / RIP / passport — case-insensitive with
    every separator (spaces, dashes, dots) stripped."""
    return re.sub(r"[^0-9a-z؀-ۿЀ-ӿ]", "", _norm_text(value))


def _tg_key(value) -> str:
    """Canonical Telegram id/username — tolerates @, t.me/... links and case."""
    s = _norm_text(value)
    s = re.sub(r"^(https?://)?(www\.)?(t\.me|telegram\.me)/", "", s)
    return s.lstrip("@")


def _dob_key(value) -> str:
    """Canonical yyyy-mm-dd for any common date shape (1/2/1999, 01-02-1999,
    1999-02-01, ٠١/٠٢/١٩٩٩). Falls back to the raw digit string."""
    s = str(value or "").translate(_AR_DIGITS)
    nums = re.findall(r"\d+", s)
    if len(nums) == 3:
        a, b, c = nums
        if len(a) == 4:
            y, m, d = a, b, c        # yyyy-mm-dd
        elif len(c) == 4:
            d, m, y = a, b, c        # dd-mm-yyyy
        else:
            return "".join(nums)
        if len(m) <= 2 and len(d) <= 2:
            return f"{y}-{int(m):02d}-{int(d):02d}"
    return "".join(nums)


# ── Search log & risk scoring ─────────────────────────────────────────────────

def _canon_probe(value) -> str | None:
    """A stable key for the thing being searched, but ONLY when it looks like a
    real identifier (phone / CCP / card / passport / Telegram). Plain names
    return None so they never inflate a number's risk — too many people share a
    first name for "10 people searched Ahmed" to mean anything."""
    d = _digits(value)
    if len(d) >= 9:
        return "num:" + d[-9:]        # phones & long numeric ids collapse by last 9
    if len(d) >= 6:
        return "num:" + d             # short CCP/card/passport digit runs
    s = str(value or "").strip().lower()
    if s.startswith("@") or "t.me/" in s or "telegram.me/" in s:
        t = _tg_key(value)
        return "id:" + t if t else None
    return None


def _probe_keys_from_fields(fields: dict) -> list:
    keys = []
    for f in HARD_FIELDS:
        k = _canon_probe(fields.get(f))
        if k:
            keys.append(k)
    return keys


def log_search(user_id, keys) -> None:
    """Record that `user_id` searched each identifier key (deduped per identifier).
    Silently does nothing for name-only searches (empty keys)."""
    keys = [k for k in dict.fromkeys(keys) if k]  # unique, order-preserving
    if not keys:
        return
    log = _load(SEARCH_LOG_FILE, {})
    now = datetime.now().isoformat()
    uid = str(user_id) if user_id is not None else ""
    changed = False
    for k in keys:
        entry = log.get(k) or {"count": 0, "users": [], "first": now, "last": now}
        entry["count"] += 1
        entry["last"] = now
        if uid and uid not in entry["users"]:
            entry["users"].append(uid)
            if len(entry["users"]) > SEARCH_LOG_MAX_USERS:
                entry["users"] = entry["users"][-SEARCH_LOG_MAX_USERS:]
        log[k] = entry
        changed = True
    if changed:
        _save(SEARCH_LOG_FILE, log)


def search_stats(keys, exclude_user=None) -> dict:
    """Aggregate search activity across the given identifier keys:
    total lookups and how many DISTINCT other people searched them."""
    log = _load(SEARCH_LOG_FILE, {})
    total, users = 0, set()
    for k in dict.fromkeys(keys):
        entry = log.get(k)
        if not entry:
            continue
        total += entry.get("count", 0)
        users.update(entry.get("users", []))
    users.discard(str(exclude_user) if exclude_user is not None else None)
    users.discard("")
    return {"search_count": total, "searchers": len(users)}


def risk_score(reports: int, searchers: int) -> dict:
    """Combine confirmed reports (strong) with distinct searchers (soft) into a
    single risk %. A filed report means near-certain danger; many people merely
    *checking* an unreported number is a capped suspicion, never "confirmed"."""
    if reports >= 1:
        pct = min(99, 55 + 20 * reports + 3 * min(searchers, 10))
        label = "خطر مؤكد" if reports >= 2 else "خطر مرتفع"
        return {"percent": pct, "label": label, "level": "danger"}
    if searchers >= SUSPICIOUS_MIN_SEARCHERS:
        pct = min(49, 12 + 7 * searchers)   # capped below "confirmed"
        return {"percent": pct, "label": "اشتباه", "level": "suspicious"}
    return {"percent": 0, "label": "", "level": "none"}


# ── Name matching ─────────────────────────────────────────────────────────────

def _tokens(s) -> list:
    return [t for t in _norm_text(s).split(" ") if t]


def _edit_distance(a: str, b: str, cap: int) -> int:
    """Levenshtein distance, short-circuited once it exceeds `cap`."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        best = i
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            val = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            cur.append(val)
            best = min(best, val)
        if best > cap:
            return cap + 1
        prev = cur
    return prev[-1]


def _allowed_edits(n: int) -> int:
    """How many typos to forgive for a token of length n. Names are short, so
    tolerance scales with length: 0 for <4, 1 for 4-6, 2 for 7+."""
    if n < 4:
        return 0
    if n <= 6:
        return 1
    return 2


def _token_match(qt: str, st: str) -> bool:
    if qt == st:
        return True
    cap = min(_allowed_edits(len(qt)), _allowed_edits(len(st)))
    return cap > 0 and _edit_distance(qt, st, cap) <= cap


def _name_forms(r: dict) -> list:
    fn, sn, ru = r.get("full_name", ""), r.get("surname", ""), r.get("full_name_ru", "")
    return [f for f in (fn, sn, ru, f"{fn} {sn}".strip()) if f]


def _name_matches(r: dict, value) -> bool:
    """Order-insensitive, typo-tolerant name match: every word of the query must
    match (exactly or fuzzily) some word of the stored names, so "Abdelkader
    Yousfi", "yousfi abdelkader" and "Yousfi Abdelkadir" all hit the same entry,
    and a first name alone still surfaces candidates."""
    q_tokens = _tokens(value)
    if not q_tokens:
        return False
    stored = set()
    for f in _name_forms(r):
        stored.update(_tokens(f))
    if not stored:
        return False
    if all(any(_token_match(qt, st) for st in stored) for qt in q_tokens):
        return True
    # names typed or stored without spaces
    qc = _norm(value)
    return any(SequenceMatcher(None, qc, _norm(f)).ratio() >= _FUZZY_RATIO for f in _name_forms(r))


def _matches_field(stored: dict, field: str, value) -> bool:
    if field == "phone":
        qk = _phone_key(value)
        return bool(qk) and qk == _phone_key(stored.get("phone"))
    if field == "telegram_user_id":
        qk = _tg_key(value)
        return bool(qk) and qk == _tg_key(stored.get("telegram_user_id"))
    if field in ("ccp", "card", "passport", "cle_rip"):
        qk = _id_key(value)
        return bool(qk) and qk == _id_key(stored.get(field))
    if field == "date_of_birth":
        qk = _dob_key(value)
        return bool(qk) and qk == _dob_key(stored.get("date_of_birth"))
    if field in NAME_FIELDS:
        return _name_matches(stored, value)
    return _norm(value) == _norm(stored.get(field))


def normalize_phone(country: str, raw: str) -> str:
    """Forces a phone into +213... (Algeria) or +7... (Russia) format,
    accepting the common local shorthand (leading 0 for DZ, leading 8 for RU)."""
    digits = _digits(raw)
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
    digits = _digits(raw)
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


def check_guarantor(value: str) -> dict | None:
    """Trusted-guarantor match. Deliberately strict — a phone match or the FULL
    name (all of its words, any order) — so a common single first name like
    "Abdelkader" can never shadow a real scam report for someone else."""
    v = _norm_text(value)
    if not v:
        return None
    vphone = _phone_key(value)
    v_tokens = set(_tokens(value))
    for g in GUARANTORS:
        if vphone and vphone == _phone_key(g["phone"]):
            return g
        for form in (g["full_name"], g["full_name_ru"], g.get("full_name_ar", "")):
            f_tokens = set(_tokens(form))
            if f_tokens and (v == _norm_text(form) or (len(v_tokens) >= 2 and v_tokens == f_tokens)):
                return g
    return None

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load(path: str, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def _save(path: str, data) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # atomic — a crash mid-write can't corrupt the DB

def _new_id() -> str:
    return str(uuid.uuid4())[:8]

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
        "full_name":           (full_name or "").strip(),
        "surname":             (surname or "").strip(),
        "full_name_ru":        (full_name_ru or "").strip(),
        "date_of_birth":       (date_of_birth or "").strip(),
        "telegram_user_id":    (telegram_user_id or "").strip(),
        "phone":               normalize_phone_auto(phone) if phone else "",
        "ccp":                 (ccp or "").strip(),
        "cle_rip":             (cle_rip or "").strip(),
        "card":                (card or "").strip(),
        "passport":            (passport or "").strip(),
        "reason":              (reason or "").strip(),
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
                    v = (fields[k] or "").strip()
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

def _mask_phone(value: str) -> str:
    """Show only the last 5 digits of a phone — enough to help recognize it,
    not enough to give away the full number (privacy)."""
    digits = _digits(value)
    if not digits:
        return ""
    if len(digits) <= 5:
        return "*" * len(digits)
    return "*" * (len(digits) - 5) + digits[-5:]

def _mask_dob(value: str) -> str:
    """Day/month only — the birth year is never shown (privacy)."""
    s = str(value or "").translate(_AR_DIGITS)
    nums = re.findall(r"\d+", s)
    if len(nums) == 3:
        a, b, c = nums
        if len(a) == 4:
            m, d = b, c              # yyyy-mm-dd -> keep mm-dd
        elif len(c) == 4:
            d, m = a, b              # dd-mm-yyyy -> keep dd-mm
        else:
            d, m = a, b
        if len(m) <= 2 and len(d) <= 2:
            return f"{int(d):02d}/{int(m):02d}"
    # unparseable shape — strip anything that looks like a 4-digit year
    stripped = re.sub(r"\b\d{4}\b", "", s).strip(" /-.")
    return stripped or ""

def masked_report(r: dict) -> dict:
    return {
        "id": r["id"],
        "full_name": r["full_name"],
        "surname": r["surname"],
        "full_name_ru": r.get("full_name_ru", ""),
        "date_of_birth": _mask_dob(r["date_of_birth"]),
        "telegram_user_id": r["telegram_user_id"],
        "phone": _mask_phone(r["phone"]),
        "ccp": _mask(r["ccp"]),
        "cle_rip": _mask(r.get("cle_rip", "")),
        "card": _mask(r["card"]),
        "passport": _mask(r["passport"]),
        "reason": r["reason"],
        "photos": r["photos"],
        "created_at": r["created_at"],
    }

def _candidates(matches: list) -> list:
    matches = sorted(matches, key=lambda r: r.get("created_at", ""), reverse=True)
    return [{
        "id": r["id"],
        "full_name": r["full_name"],
        "surname": r["surname"],
        "full_name_ru": r.get("full_name_ru", ""),
        "date_of_birth": _mask_dob(r["date_of_birth"]),
    } for r in matches[:MAX_CANDIDATES]]


_COMPLETENESS_FIELDS = HARD_FIELDS + NAME_FIELDS + ["date_of_birth", "reason", "photos"]


def _consolidate(matches: list) -> dict:
    """Several reports about the same person (they matched the same identifier)
    collapse into one card: the most complete report is primary, and every
    report's reason/photos are attached so the corroboration is visible."""
    matches = sorted(matches, key=lambda r: r.get("created_at", ""))
    primary = max(matches, key=lambda r: sum(1 for f in _COMPLETENESS_FIELDS if r.get(f)))
    card = masked_report(primary)
    card["report_count"] = len(matches)
    card["reasons"] = [
        {"reason": r.get("reason", ""), "created_at": r.get("created_at", "")}
        for r in matches if r.get("reason")
    ]
    photos = [p for r in matches for p in (r.get("photos") or [])]
    card["photos"] = list(dict.fromkeys(photos))  # dedupe identical file ids
    return card


def _clean_query_value(v) -> str:
    return str(v or "").strip()[:MAX_QUERY_LEN]


def _risk_payload(keys, reports: int, user_id) -> dict:
    stats = search_stats(keys, exclude_user=user_id)
    risk = risk_score(reports, stats["searchers"])
    return {**stats, "reports": reports, "risk": risk}


def search_reports(query: dict, user_id=None) -> dict:
    """Returns {"mode": "detail"|"candidates"|"suspicious"|"none"|"guarantor", ...}.
    Hard identifiers (phone/ccp/card/...) are tried first, but a mismatch there
    doesn't hide a legitimate name match if a name was also given — it falls
    back to name-based candidates instead of returning "none" outright.
    date_of_birth is searchable on its own (candidates of everyone born that
    day) and narrows (AND) a name search when given alongside one.
    When `user_id` is given, hard-identifier lookups are logged so repeated
    checks of the same number build a search-based risk signal."""
    q = {k: _clean_query_value(v) for k, v in query.items() if _clean_query_value(v)}

    probe_keys = _probe_keys_from_fields(q)
    if user_id is not None:
        log_search(user_id, probe_keys)

    # guarantor is only checked against fields that can identify a person
    guarantor_probes = [q[k] for k in ("full_name", "surname", "full_name_ru", "phone", "telegram_user_id") if k in q]
    if q.get("full_name") and q.get("surname"):
        guarantor_probes.append(f"{q['full_name']} {q['surname']}")
    for v in guarantor_probes:
        g = check_guarantor(v)
        if g:
            return {"mode": "guarantor", "results": [g]}

    approved = get_approved_reports()
    hard = {k: v for k, v in q.items() if k in HARD_FIELDS}
    name_qs = {k: v for k, v in q.items() if k in NAME_FIELDS}
    dob = q.get("date_of_birth")

    if hard:
        matches = [r for r in approved if any(_matches_field(r, k, v) for k, v in hard.items())]
        if matches:
            return {"mode": "detail", "results": [_consolidate(matches)],
                    **_risk_payload(probe_keys, len(matches), user_id)}

    if not name_qs and not dob:
        return _suspicious_or_none(probe_keys, user_id)

    if name_qs:
        # a combined "full_name surname" query must match as a whole too
        probes = list(name_qs.values())
        if "full_name" in name_qs and "surname" in name_qs:
            probes = [f"{name_qs['full_name']} {name_qs['surname']}"] + probes
        matches = [r for r in approved if any(_name_matches(r, v) for v in probes)]
        if dob:
            matches = [r for r in matches if _matches_field(r, "date_of_birth", dob)]
    else:
        matches = [r for r in approved if _matches_field(r, "date_of_birth", dob)]

    if not matches:
        return _suspicious_or_none(probe_keys, user_id)
    return {"mode": "candidates", "results": _candidates(matches)}


def _suspicious_or_none(probe_keys, user_id) -> dict:
    """No report matched. If a real identifier was searched and enough other
    people have checked it, flag it as suspicious with a soft risk %."""
    if not probe_keys:
        return {"mode": "none", "results": []}
    payload = _risk_payload(probe_keys, 0, user_id)
    if payload["risk"]["level"] == "suspicious":
        return {"mode": "suspicious", "results": [], **payload}
    return {"mode": "none", "results": [], **payload}


def smart_search(value: str, user_id=None) -> dict:
    """Bot chat entry point — a single free-text value, unknown which field it is.
    Tries it against every hard identifier first, then falls back to a name
    or date-of-birth match."""
    value = _clean_query_value(value)
    if not _norm(value):
        return {"mode": "none", "results": []}

    probe_keys = [k for k in [_canon_probe(value)] if k]
    if user_id is not None:
        log_search(user_id, probe_keys)

    g = check_guarantor(value)
    if g:
        return {"mode": "guarantor", "results": [g]}

    approved = get_approved_reports()

    matches = [r for r in approved if any(_matches_field(r, f, value) for f in HARD_FIELDS)]
    if matches:
        return {"mode": "detail", "results": [_consolidate(matches)],
                **_risk_payload(probe_keys, len(matches), user_id)}

    matches = [r for r in approved
               if _name_matches(r, value) or _matches_field(r, "date_of_birth", value)]
    if not matches:
        return _suspicious_or_none(probe_keys, user_id)
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
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"{user_id}:{today}"
    count = quota.get(key, 0)
    if count >= DAILY_SEARCH_LIMIT:
        return False
    # drop stale per-day keys so the file never grows unbounded
    quota = {k: v for k, v in quota.items() if k.endswith(f":{today}")}
    quota[key] = count + 1
    _save(QUOTA_FILE, quota)
    return True
