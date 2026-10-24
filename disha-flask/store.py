"""
Data access for DISHA MIS.

Two backends behind one interface:
  • Supabase (when SUPABASE_URL and SUPABASE_KEY are set)
  • In-memory demo store (data resets on restart)

Unlike the first version, Supabase errors are logged and raised as
StoreError instead of silently falling back to demo data, so a bad key
or a missing RLS policy shows up immediately.
"""
import logging
import os
import uuid
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

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
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
if SUPABASE_URL and SUPABASE_KEY:
    if not SUPABASE_KEY.startswith("eyJ"):
        log.error("SUPABASE_KEY does not look like a JWT (eyJ...). supabase==2.7.4 "
                  "needs the legacy anon key, not the sb_publishable_ key.")
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        log.exception("Could not create Supabase client – using in-memory demo data")
        supabase = None

BACKEND = "supabase" if supabase else "memory"

# ─────────────────────────────────────────────
# In-memory store
# ─────────────────────────────────────────────
_REPORTS = demo_data.build_reports()
_USERS = {}   # username -> user dict; empty means "demo logins active"
DEMO_USERS = {
    "admin": {"username": "admin", "full_name": "Admin User", "role": "Super Admin",
              "district": "", "active": True,
              "password_hash": generate_password_hash("admin123")},
    "staff": {"username": "staff", "full_name": "Staff User", "role": "Back Office",
              "district": "", "active": True,
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
    for k in ("participants", "details"):
        if r.get(k) is None:
            r[k] = {}
    for k in ("tags", "comments", "attachments", "archive_refs"):
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
                raise StoreError("Update was blocked. Check that the 'Allow anon update' "
                                 "RLS policy from supabase_schema.sql exists.")
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
    """Store a file and return (url, path)."""
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)[-80:]
    path = f"{datetime.now():%Y/%m}/{uuid.uuid4().hex[:12]}_{safe}"
    if supabase:
        try:
            supabase.storage.from_(BUCKET).upload(
                path, content, {"content-type": content_type or "application/octet-stream"})
            return supabase.storage.from_(BUCKET).get_public_url(path), path
        except Exception as e:
            log.exception("Supabase storage upload failed")
            raise StoreError(f"Could not upload {filename}: {e}")
    full = os.path.join(LOCAL_UPLOAD_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as fh:
        fh.write(content)
    return None, path   # URL is built by the /files route


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────
def list_users():
    if supabase:
        try:
            res = supabase.table("app_users").select("*").order("username").execute()
            return res.data or []
        except Exception as e:
            log.exception("Supabase users read failed")
            raise StoreError(f"Could not read users: {e}")
    return sorted(_USERS.values(), key=lambda u: u["username"])


def get_user(username):
    """Look up a login. Demo logins work only while no users have been created."""
    users = list_users()
    if users:
        return next((u for u in users if u["username"] == username), None)
    return DEMO_USERS.get(username)


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
