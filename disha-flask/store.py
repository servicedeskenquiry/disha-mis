"""
Data access for DISHA MIS.

Two backends behind one interface:
  • Supabase (when SUPABASE_URL and a key are set)
  • In-memory demo store (data resets on restart)

Files go to Backblaze B2 when it is configured (see b2.py), otherwise to
Supabase Storage, otherwise to the local disk.

Unlike the first version, Supabase errors are logged and raised as
StoreError instead of silently falling back to demo data, so a bad key
or a missing RLS policy shows up immediately.
"""
import base64
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

import b2
import config as C
import demo_data

log = logging.getLogger("disha.store")

LOCAL_UPLOAD_DIR = os.environ.get(
    "UPLOAD_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "uploads")
)
BUCKET = os.environ.get("SUPABASE_BUCKET", "attachments")


class StoreError(Exception):
    pass


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ─────────────────────────────────────────────
# Supabase client
# ─────────────────────────────────────────────
supabase = None
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
# The service_role key lets the server bypass Row Level Security, so the
# database itself can refuse everyone else. SUPABASE_KEY (anon) is the old
# setup and only works while the open RLS policies still exist.
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
SUPABASE_KEY = SUPABASE_SERVICE_KEY or os.environ.get("SUPABASE_KEY", "").strip()


def _jwt_role(key):
    """The 'role' claim of a legacy Supabase key: 'anon' or 'service_role'."""
    try:
        payload = key.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get("role", "")
    except Exception:
        return ""


KEY_ROLE = _jwt_role(SUPABASE_KEY) if SUPABASE_KEY else ""
if SUPABASE_URL and SUPABASE_KEY:
    if not SUPABASE_KEY.startswith("eyJ"):
        log.error("The Supabase key does not look like a JWT (eyJ...). supabase==2.7.4 "
                  "needs the legacy keys, not the sb_publishable_ / sb_secret_ keys.")
    elif SUPABASE_SERVICE_KEY and KEY_ROLE != "service_role":
        log.error("SUPABASE_SERVICE_KEY is not a service_role key (role=%r).", KEY_ROLE)
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        log.exception("Could not create Supabase client – using in-memory demo data")
        supabase = None

BACKEND = "supabase" if supabase else "memory"
# True when the database still relies on the open anon policies
INSECURE_KEY = bool(supabase) and KEY_ROLE != "service_role"
FILE_STORAGE = "b2" if b2.ENABLED else ("supabase" if supabase else "local")

# ─────────────────────────────────────────────
# In-memory store
# ─────────────────────────────────────────────
_REPORTS = demo_data.build_reports()
_USERS = {}   # username -> user dict; empty means "demo logins active"
_SETTINGS = {}
DEMO_USERS = {
    "admin": {"username": "admin", "full_name": "Admin User", "role": C.ADMIN,
              "districts": [], "active": True,
              "password_hash": generate_password_hash("admin123")},
    "approver": {"username": "approver", "full_name": "Approver User", "role": C.APPROVER,
                 "districts": [], "active": True,
                 "password_hash": generate_password_hash("approver123")},
    "staff": {"username": "staff", "full_name": "Staff User", "role": C.BACK_OFFICE,
              "districts": [], "active": True,
              "password_hash": generate_password_hash("staff123")},
}


def _normalise(r):
    """Fill defaults so templates never trip on missing keys."""
    r.setdefault("participants", {})
    r.setdefault("tags", [])
    r.setdefault("details", {})
    r.setdefault("comments", [])
    r.setdefault("attachments", [])
    r.setdefault("archive_refs", [])
    r.setdefault("history", [])
    r.setdefault("guest_hidden", False)
    r.setdefault("created_by", None)
    for k in ("participants", "details"):
        if r.get(k) is None:
            r[k] = {}
    for k in ("tags", "comments", "attachments", "archive_refs", "history"):
        if r.get(k) is None:
            r[k] = []
    r["participants_total"] = r.get("participants_total") or 0
    return r


# ─────────────────────────────────────────────
# Reports
# ─────────────────────────────────────────────
def all_reports():
    """Every report, newest first."""
    if supabase:
        try:
            rows, start, page = [], 0, 1000
            while True:
                res = (supabase.table("reports").select("*")
                       .order("id", desc=True).range(start, start + page - 1).execute())
                batch = res.data or []
                rows.extend(batch)
                if len(batch) < page:
                    break
                start += page
            return [_normalise(r) for r in rows]
        except Exception as e:
            log.exception("Supabase read failed")
            raise StoreError(f"Could not read reports from Supabase: {e}")
    return [_normalise(dict(r)) for r in sorted(_REPORTS, key=lambda r: r["id"], reverse=True)]


def get_report(report_id):
    if supabase:
        try:
            res = supabase.table("reports").select("*").eq("id", report_id).limit(1).execute()
            return _normalise(res.data[0]) if res.data else None
        except Exception as e:
            log.exception("Supabase read failed")
            raise StoreError(f"Could not read report: {e}")
    r = next((r for r in _REPORTS if r["id"] == report_id), None)
    return _normalise(dict(r)) if r else None


def insert_report(data):
    data = dict(data)
    data.setdefault("created_at", now_iso())
    if supabase:
        try:
            res = supabase.table("reports").insert(data).execute()
            return res.data[0]["id"] if res.data else None
        except Exception as e:
            log.exception("Supabase insert failed")
            raise StoreError(f"Could not save the report: {e}")
    data["id"] = max((r["id"] for r in _REPORTS), default=0) + 1
    _REPORTS.append(data)
    return data["id"]


def update_report(report_id, changes):
    if supabase:
        try:
            res = supabase.table("reports").update(changes).eq("id", report_id).execute()
            if not res.data:
                # RLS silently filters updates when no UPDATE policy exists
                raise StoreError("Update was blocked by Row Level Security. Set "
                                 "SUPABASE_SERVICE_KEY (the service_role key) in Render.")
            return
        except StoreError:
            raise
        except Exception as e:
            log.exception("Supabase update failed")
            raise StoreError(f"Could not update the report: {e}")
    for r in _REPORTS:
        if r["id"] == report_id:
            r.update(changes)
            return
    raise StoreError("Report not found")


# ─────────────────────────────────────────────
# Attachments
# ─────────────────────────────────────────────
def save_file(filename, content, content_type):
    """Store a file and return (url, path, storage).

    storage is "b2", "supabase" or "local". B2 and local files have no
    public URL: they are served through the /files route to logged-in users.
    """
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)[-80:]
    path = f"{datetime.now():%Y/%m}/{uuid.uuid4().hex[:12]}_{safe}"
    content_type = content_type or "application/octet-stream"
    if b2.ENABLED:
        try:
            b2.put(b2.ATTACHMENT_PREFIX + path, content, content_type)
        except b2.B2Error as e:
            raise StoreError(f"Could not upload {filename}: {e}")
        return None, path, "b2"
    if supabase:
        try:
            supabase.storage.from_(BUCKET).upload(path, content, {"content-type": content_type})
            return supabase.storage.from_(BUCKET).get_public_url(path), path, "supabase"
        except Exception as e:
            log.exception("Supabase storage upload failed")
            raise StoreError(f"Could not upload {filename}: {e}")
    full = os.path.join(LOCAL_UPLOAD_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as fh:
        fh.write(content)
    return None, path, "local"


def files_to_migrate(reports):
    """Attachments still held in Supabase Storage (not yet copied to B2)."""
    n = 0
    for r in reports:
        for f in (r.get("attachments") or []) + (r.get("archive_refs") or []):
            if f.get("path") and f.get("storage") != "b2" and f.get("url"):
                n += 1
    return n


def migrate_files_to_b2(time_budget=20):
    """Copy Supabase Storage attachments to B2, a batch at a time.

    Runs until the time budget is used up so one request never hits the
    server timeout. Returns (copied, remaining, errors). When nothing is
    left, the Supabase bucket is made private so the old public links stop
    working.
    """
    if not (supabase and b2.ENABLED):
        raise StoreError("Both Supabase and Backblaze B2 must be configured.")
    start, copied, errors, done = time.time(), 0, [], {}
    for r in all_reports():
        changed = False
        for key in ("attachments", "archive_refs"):
            for f in r.get(key) or []:
                if not (f.get("path") and f.get("storage") != "b2" and f.get("url")):
                    continue
                if time.time() - start > time_budget:
                    break
                path = f["path"]
                try:
                    if path not in done:
                        content = supabase.storage.from_(BUCKET).download(path)
                        b2.put(b2.ATTACHMENT_PREFIX + path, content,
                               f.get("type") or "application/octet-stream")
                        done[path] = True
                        copied += 1
                    f["storage"], f["url"] = "b2", None
                    changed = True
                except Exception as e:
                    log.exception("Could not migrate %s", path)
                    errors.append(f"{f.get('name') or path}: {e}")
        if changed:
            update_report(r["id"], {"attachments": r["attachments"],
                                    "archive_refs": r["archive_refs"]})
    remaining = files_to_migrate(all_reports())
    if remaining == 0 and not errors:
        try:
            supabase.storage.update_bucket(BUCKET, {"public": False})
        except Exception:
            log.exception("Could not make the Supabase bucket private")
    return copied, remaining, errors


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────
def _normalise_user(u):
    u = dict(u)
    u["role"] = C.ROLE_ALIASES.get(u.get("role"), u.get("role"))
    districts = u.get("districts") or []
    if not districts and u.get("district"):
        districts = [u["district"]]     # accounts from before Phase 2
    u["districts"] = list(districts)
    return u


def list_users():
    if supabase:
        try:
            res = supabase.table("app_users").select("*").order("username").execute()
            return [_normalise_user(u) for u in res.data or []]
        except Exception as e:
            log.exception("Supabase users read failed")
            raise StoreError(f"Could not read users: {e}")
    return [_normalise_user(u) for u in sorted(_USERS.values(), key=lambda u: u["username"])]


def get_user(username):
    """Look up a login. Demo logins work only while no users have been created."""
    users = list_users()
    if users:
        return next((u for u in users if u["username"] == username), None)
    return _normalise_user(DEMO_USERS[username]) if username in DEMO_USERS else None


def demo_logins_active():
    return not list_users()


def save_user(user, is_new):
    user = dict(user)
    if supabase:
        try:
            if is_new:
                user["created_at"] = now_iso()
                supabase.table("app_users").insert(user).execute()
            else:
                res = (supabase.table("app_users").update(user)
                       .eq("username", user["username"]).execute())
                if not res.data:
                    raise StoreError("User update was blocked by RLS.")
            return
        except StoreError:
            raise
        except Exception as e:
            log.exception("Supabase user save failed")
            raise StoreError(f"Could not save user: {e}")
    if is_new:
        user["created_at"] = now_iso()
        _USERS[user["username"]] = user
    else:
        _USERS[user["username"]].update(user)


# ─────────────────────────────────────────────
# Backup and restore (whole database)
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# Settings (Admin › Settings)
# ─────────────────────────────────────────────
_settings_cache = {"at": 0.0, "value": None}
SETTINGS_TTL = 20   # seconds; other server processes see a change within this time


def get_settings():
    """config.DEFAULT_SETTINGS overlaid with what the Admin saved."""
    if _settings_cache["value"] is not None and time.time() - _settings_cache["at"] < SETTINGS_TTL:
        return dict(_settings_cache["value"])
    saved = {}
    if supabase:
        try:
            res = supabase.table("app_settings").select("*").execute()
            saved = {row["key"]: row["value"] for row in res.data or []}
        except Exception:
            # Table missing (supabase_phase2.sql not run yet): use the defaults
            log.exception("Could not read settings")
    else:
        saved = dict(_SETTINGS)
    value = {**C.DEFAULT_SETTINGS, **{k: v for k, v in saved.items() if k in C.DEFAULT_SETTINGS}}
    _settings_cache.update(at=time.time(), value=value)
    return dict(value)


def save_settings(changes):
    changes = {k: v for k, v in changes.items() if k in C.DEFAULT_SETTINGS}
    if supabase:
        try:
            rows = [{"key": k, "value": v, "updated_at": now_iso()} for k, v in changes.items()]
            supabase.table("app_settings").upsert(rows).execute()
        except Exception as e:
            log.exception("Settings save failed")
            raise StoreError(f"Could not save settings: {e}")
    else:
        _SETTINGS.update(changes)
    _settings_cache["value"] = None


BACKUP_TABLES = {"reports": "id", "app_users": "username", "app_settings": "key"}
# Backups made before Phase 2 have no app_settings
OPTIONAL_BACKUP_TABLES = {"app_settings"}


def dump_tables():
    """Every row of every table, unmodified, as a backup payload."""
    tables = {}
    if supabase:
        try:
            for table, order in BACKUP_TABLES.items():
                rows, start, page = [], 0, 1000
                try:
                    while True:
                        res = (supabase.table(table).select("*").order(order)
                               .range(start, start + page - 1).execute())
                        batch = res.data or []
                        rows.extend(batch)
                        if len(batch) < page:
                            break
                        start += page
                except Exception:
                    if table in OPTIONAL_BACKUP_TABLES:
                        log.warning("Backup: table %s not found, skipped", table)
                        continue
                    raise
                tables[table] = rows
        except Exception as e:
            log.exception("Backup read failed")
            raise StoreError(f"Could not read the database for backup: {e}")
    else:
        tables = {"reports": [dict(r) for r in sorted(_REPORTS, key=lambda r: r["id"])],
                  "app_users": [dict(u) for u in sorted(_USERS.values(), key=lambda u: u["username"])],
                  "app_settings": [{"key": k, "value": v} for k, v in sorted(_SETTINGS.items())]}
    return {"app": "disha-mis", "version": 1, "created_at": now_iso(),
            "backend": BACKEND, "tables": tables}


def validate_backup(payload):
    if not isinstance(payload, dict) or payload.get("app") != "disha-mis":
        raise StoreError("This file is not a DISHA MIS backup.")
    tables = payload.get("tables") or {}
    for t in BACKUP_TABLES:
        if t in OPTIONAL_BACKUP_TABLES and t not in tables:
            continue
        if not isinstance(tables.get(t), list):
            raise StoreError(f"The backup is missing the '{t}' table.")
    return {t: len(tables[t]) for t in BACKUP_TABLES if t in tables}


def restore_tables(payload):
    """Replace all data with the backup, in one transaction (Supabase)."""
    counts = validate_backup(payload)
    if supabase:
        try:
            res = supabase.rpc("disha_restore", {"payload": payload}).execute()
            return res.data or counts
        except Exception as e:
            log.exception("Restore failed")
            raise StoreError(f"Restore failed, nothing was changed: {e}")
    _REPORTS[:] = [dict(r) for r in payload["tables"]["reports"]]
    _USERS.clear()
    _USERS.update({u["username"]: dict(u) for u in payload["tables"]["app_users"]})
    if "app_settings" in payload["tables"]:
        _SETTINGS.clear()
        _SETTINGS.update({row["key"]: row["value"] for row in payload["tables"]["app_settings"]})
    _settings_cache["value"] = None
    return counts
