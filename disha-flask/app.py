import hmac
import io
import logging
import os
from datetime import date, datetime
from functools import wraps

from dotenv import load_dotenv

load_dotenv()

from flask import (  # noqa: E402
    Flask, abort, flash, g, jsonify, redirect, render_template, request,
    send_file, send_from_directory, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash  # noqa: E402

import analytics as A  # noqa: E402
import b2  # noqa: E402
import backup  # noqa: E402
import config as C  # noqa: E402
import exports  # noqa: E402
import store  # noqa: E402
from store import StoreError  # noqa: E402

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")))
# 10 attachments × 25 MB plus form fields
app.config["MAX_CONTENT_LENGTH"] = (C.MAX_ATTACHMENTS * C.MAX_FILE_MB + 5) * 1024 * 1024


# ─────────────────────────────────────────────
# Auth helpers and permissions (revised module, section 10)
#
#                       Admin   Approver        Back Office   Guest
#   View reports        all     own districts   own entries   as Admin allows
#   Enter / tag data    yes     no              yes           no
#   Approve / query     yes     yes             no            no
#   Comment             yes     yes             yes           if allowed
#   Download            yes     yes             own (option)  no
#   Users, settings,
#   guest access,
#   backup & restore    yes     no              no            no
# Session "mode" is "admin" for every logged-in account and "guest" for guests.
# ─────────────────────────────────────────────
def is_staff():
    return session.get("mode") == "admin"


def is_guest():
    return session.get("mode") == "guest"


def is_logged_in():
    return "mode" in session


def role():
    return session.get("role") if is_staff() else None


def is_admin():
    return role() == C.ADMIN


def can_approve():
    return role() in (C.ADMIN, C.APPROVER)


def can_enter():
    return role() in (C.ADMIN, C.BACK_OFFICE)


def can_manage_users():
    return is_admin()


def can_download():
    if role() in (C.ADMIN, C.APPROVER):
        return True
    return role() == C.BACK_OFFICE and settings().get("backoffice_can_download", True)


def can_comment():
    return is_staff() or (is_guest() and settings().get("guest_can_comment", True))


def settings():
    if "settings" not in g:
        g.settings = store.get_settings()
    return g.settings


def is_own(report):
    """Entered by the logged-in user (older reports only have a display name)."""
    if report.get("created_by"):
        return report["created_by"] == session.get("username")
    return bool(report.get("submitted_by")) and report.get("submitted_by") == session.get("display_name")


def can_view(report):
    if is_admin():
        return True
    if role() == C.APPROVER:
        districts = session.get("districts") or []
        return not districts or report.get("district") in districts
    if role() == C.BACK_OFFICE:
        return is_own(report)
    if is_guest():
        s = settings()
        return (report.get("status") == "Approved" and not report.get("guest_hidden")
                and (not s["guest_districts"] or report.get("district") in s["guest_districts"])
                and (not s["guest_report_types"] or report.get("rtype") in s["guest_report_types"]))
    return False


def can_edit(report):
    """Admin can correct any report (override). Back Office can edit its own
    report until it is approved; after a query or rejection that is how it
    answers and resubmits."""
    if is_admin():
        return True
    return (role() == C.BACK_OFFICE and is_own(report)
            and report.get("status") != "Approved")


def can_review(report):
    return can_approve() and can_view(report) and report.get("status") != "Approved"


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not is_logged_in():
            return redirect(url_for("login"))
        return view(*a, **kw)
    return wrapped


def staff_required(view):
    """Logged in with a real account (not guest)."""
    @wraps(view)
    def wrapped(*a, **kw):
        if not is_logged_in():
            return redirect(url_for("login"))
        if is_guest():
            flash("Log in to use this section.", "error")
            return redirect(url_for("dashboard"))
        return view(*a, **kw)
    return wrapped


@app.before_request
def refresh_session():
    """Apply Admin changes at once: a disabled account is logged out, and a
    changed role or district list takes effect on the next page."""
    if request.endpoint in (None, "static", "health", "cron_nightly"):
        return
    if is_guest() and not settings().get("guest_enabled", True):
        session.clear()
        flash("Guest access is switched off. Please log in.", "error")
        return redirect(url_for("login"))
    if not is_staff():
        return
    try:
        user = store.get_user(session.get("username", ""))
    except StoreError:
        return   # database hiccup: keep the session rather than log everyone out
    if not user or not user.get("active", True):
        session.clear()
        flash("Your account has been disabled or removed. Contact the Admin.", "error")
        return redirect(url_for("login"))
    session.update(role=user["role"], districts=user["districts"],
                   display_name=user.get("full_name") or user["username"])


def all_reports():
    """Every report, read once per request."""
    if "all_reports" not in g:
        g.all_reports = store.all_reports()
    return g.all_reports


def load_reports():
    """All reports the current user is allowed to see."""
    try:
        reports = all_reports()
    except StoreError as e:
        flash(str(e), "error")
        reports = []
    return [r for r in reports if can_view(r)]


def get_visible_report(report_id):
    """The report, or None (with a message) if missing or not visible."""
    try:
        r = store.get_report(report_id)
    except StoreError as e:
        flash(str(e), "error")
        return None
    if not r or not can_view(r):
        flash("Report not found, or you do not have access to it.", "error")
        return None
    return r


@app.context_processor
def inject_globals():
    returned = 0
    if role() == C.BACK_OFFICE and request.endpoint not in (None, "static"):
        try:
            returned = sum(1 for r in all_reports()
                           if is_own(r) and r.get("status") in C.RETURNED_STATUSES)
        except StoreError:
            pass
    return {
        "C": C,
        "role": role(),
        "is_admin": is_admin(),
        "can_approve": can_approve(),
        "can_enter": can_enter(),
        "can_manage_users": can_manage_users(),
        "can_download": can_download(),
        "can_comment": can_comment(),
        "can_edit": can_edit,
        "can_review": can_review,
        "settings": settings(),
        "returned_count": returned,
        "backend": store.BACKEND,
        "insecure_db": store.INSECURE_KEY,
        "fy_label": A.fy_label,
        "today": date.today(),
    }


@app.template_filter("dt")
def fmt_dt(value, with_time=False):
    if not value:
        return ""
    try:
        d = datetime.fromisoformat(str(value)[:19])
    except ValueError:
        return value
    return d.strftime("%d %b %Y, %H:%M" if with_time else "%d %b %Y")


def file_url(f):
    if f.get("storage") in ("b2", "local") or not f.get("url"):
        return url_for("uploaded_file", path=f.get("path", ""), name=f.get("name"))
    return f["url"]


app.jinja_env.globals["file_url"] = file_url


# ─────────────────────────────────────────────
# Welcome page and login
# ─────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/fisheries")
def fisheries():
    return redirect(url_for("dashboard") if is_logged_in() else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("action") == "guest":
            if not store.get_settings().get("guest_enabled", True):
                flash("Guest access is switched off.", "error")
                return redirect(url_for("login"))
            session.clear()
            session.update(mode="guest", username="guest", display_name="Guest User",
                           role="View Only")
            return redirect(url_for("dashboard"))

        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        try:
            user = store.get_user(username)
        except StoreError as e:
            flash(str(e), "error")
            return render_template("login.html", demo_active=False)
        if user and user.get("active", True) and check_password_hash(user["password_hash"], password):
            session.clear()
            session.update(mode="admin", username=user["username"],
                           display_name=user.get("full_name") or user["username"],
                           role=user["role"], districts=user["districts"])
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    try:
        demo_active = store.demo_logins_active()
    except StoreError:
        demo_active = False
    return render_template("login.html", demo_active=demo_active,
                           guest_enabled=store.get_settings().get("guest_enabled", True))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ─────────────────────────────────────────────
# Primary dashboard
# ─────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    tag = request.args.get("tag", "")
    reports = load_reports()
    if tag:
        reports = A.filter_reports(reports, tag=tag)
    stats = A.dashboard(reports)
    if role() == C.BACK_OFFICE:
        # Back Office: own reports that need an answer first
        pending = [r for r in reports if r.get("status") in C.RETURNED_STATUSES][:8]
    else:
        pending = [r for r in reports if r.get("status") in C.REVIEW_STATUSES][:8]
    return render_template("dashboard.html", stats=stats, pending=pending, tag=tag)


# ─────────────────────────────────────────────
# Submit report
# ─────────────────────────────────────────────
def archive_files(reports):
    """Files already uploaded with earlier reports, for re-use by reference."""
    out = []
    for r in reports:
        for i, f in enumerate(r.get("attachments") or []):
            out.append({"ref": f"{r['id']}|{i}", "report_id": r["id"], "name": f.get("name"),
                        "category": f.get("category"), "district": r.get("district"),
                        "period": r.get("period")})
    return out


def period_from_form(rtype, form):
    """Return (period_label, extra_fields, error)."""
    if rtype == "daily":
        d = form.get("activity_date", "")
        try:
            dd = date.fromisoformat(d)
        except ValueError:
            return None, None, "Please enter the date of the activity."
        return dd.strftime("%d %b %Y"), {"activity_date": d, "fy": A.fy_of(dd),
                                         "month": dd.month}, None
    try:
        fy = int(form.get("fy", ""))
    except ValueError:
        return None, None, "Please select the period."
    if rtype == "monthly":
        try:
            m = int(form.get("month", ""))
        except ValueError:
            return None, None, "Please select the month."
        year = fy if m >= 4 else fy + 1
        return f"{C.MONTHS[m - 1]} {year}", {"fy": fy, "month": m}, None
    if rtype == "quarterly":
        q = int(form.get("quarter") or 0)
        if not 1 <= q <= 4:
            return None, None, "Please select the quarter."
        return f"{C.QUARTERS[q - 1]} {A.fy_label(fy)}", {"fy": fy, "quarter": q}, None
    if rtype == "halfyearly":
        h = int(form.get("half") or 0)
        if h not in (1, 2):
            return None, None, "Please select the half-year."
        return f"{C.HALVES[h - 1]} {A.fy_label(fy)}", {"fy": fy, "half": h}, None
    return A.fy_label(fy), {"fy": fy}, None


def parse_report_form(f, files, reports, existing=None):
    """Read the submit/edit form. Returns (report fields, new uploads, errors).

    existing: the report being edited; its attachments can be kept or removed.
    """
    rtype = existing["rtype"] if existing else f.get("rtype", "daily")
    if rtype not in C.REPORT_TYPE_KEYS:
        abort(400)
    allowed_districts = C.DISTRICTS if rtype == "daily" else C.PERIODIC_DISTRICTS
    district = f.get("district", "")
    activity = f.get("activity", "")
    errors = []
    if district not in allowed_districts:
        errors.append("Please select the Active District.")
    if activity not in C.ACTIVITY_FIELDS or (rtype == "daily" and activity == C.CONSOLIDATED):
        errors.append("Please select the Activity Type.")
    period, extra, err = period_from_form(rtype, f)
    if err:
        errors.append(err)
    if not f.get("description", "").strip():
        errors.append("Please write a description.")

    # Participants: Total plus ticked sub-categories
    participants = {}
    try:
        total = int(f.get("p_total") or 0)
    except ValueError:
        total = 0
    for key in f.getlist("pcat"):
        if key in C.PARTICIPANT_LABEL:
            try:
                participants[key] = max(0, int(f.get(f"p_{key}") or 0))
            except ValueError:
                pass
    if not total:
        total = participants.get("women", 0) + participants.get("men", 0)
    if total:
        participants["total"] = total

    tags = [t for t in f.getlist("tags") if t in C.ISSUE_TAGS]
    details = {fd["key"]: f.get(f"d_{fd['key']}", "").strip()
               for fd in C.ACTIVITY_FIELDS.get(activity, [])
               if f.get(f"d_{fd['key']}", "").strip()}

    # Attachments: two categories, max 10 including archive references
    uploads = []
    for cat in C.ATTACHMENT_CATEGORIES:
        for fs in files.getlist(f"files_{cat['key']}"):
            if fs and fs.filename:
                uploads.append((cat["key"], fs))
    kept, refs = [], []
    if existing:
        keep = set(f.getlist("keep_file"))
        kept = [a for i, a in enumerate(existing["attachments"]) if f"a{i}" in keep]
        refs = [a for i, a in enumerate(existing["archive_refs"]) if f"r{i}" in keep]
    by_ref = {a["ref"]: a for a in archive_files(reports)}
    for ref in f.getlist("archive_ref"):
        if ref in by_ref:
            rid, idx = ref.split("|")
            src = next(r for r in reports if str(r["id"]) == rid)["attachments"][int(idx)]
            refs.append({"report_id": int(rid), "name": src.get("name"),
                         "category": src.get("category"), "type": src.get("type"),
                         "url": src.get("url"), "path": src.get("path"),
                         "storage": src.get("storage")})
    if len(kept) + len(uploads) + len(refs) > C.MAX_ATTACHMENTS:
        errors.append(f"A report can have at most {C.MAX_ATTACHMENTS} attachments.")
    for _, fs in uploads:
        ext = fs.filename.rsplit(".", 1)[-1].lower() if "." in fs.filename else ""
        if ext not in C.ALLOWED_EXTENSIONS:
            errors.append(f"File type not allowed: {fs.filename}")

    fields = {
        "rtype": rtype, "district": district, "activity": activity,
        "period": period, "location": f.get("location", "").strip(),
        "participants": participants, "participants_total": participants.get("total", 0),
        "tags": tags, "details": details,
        "description": f.get("description", "").strip(),
        "remarks": f.get("remarks", "").strip(),
        "submitted_by": f.get("submitted_by", "").strip() or session.get("display_name"),
        "attachments": kept, "archive_refs": refs,
        "activity_date": None, "month": None, "quarter": None, "half": None,
    }
    fields.update(extra or {})
    return fields, uploads, errors


def save_uploads(uploads):
    """Store new files; returns attachment records. Oversized files are skipped."""
    out = []
    for cat, fs in uploads:
        content = fs.read()
        if len(content) > C.MAX_FILE_MB * 1024 * 1024:
            flash(f"{fs.filename} is larger than {C.MAX_FILE_MB} MB and was skipped.", "error")
            continue
        url, path, storage = store.save_file(fs.filename, content, fs.content_type)
        out.append({"category": cat, "name": fs.filename,
                    "type": fs.content_type or "application/octet-stream",
                    "size": len(content), "url": url, "path": path, "storage": storage})
    return out


def history_entry(action, note="", changes=None):
    e = {"at": store.now_iso(), "by": session.get("display_name"),
         "role": role() or "Guest", "action": action}
    if note:
        e["note"] = note
    if changes:
        e["changes"] = changes
    return e


def comment_entry(text, kind="comment"):
    c = {"by": session.get("display_name") if is_staff() else "Guest",
         "at": store.now_iso(), "text": text}
    if kind != "comment":
        c["kind"] = kind
    if is_staff():
        c["role"] = role()
    else:
        c["guest"] = True
    return c


def form_context(reports, **extra):
    return dict(archive=archive_files(reports), fys=A.available_fys(reports),
                current_fy=A.current_fy(), **extra)


@app.route("/submit", methods=["GET", "POST"])
@staff_required
def submit():
    if not can_enter():
        flash("Approvers review reports; data entry is done by Back Office or Admin.", "error")
        return redirect(url_for("dashboard"))
    reports = load_reports()
    if request.method == "GET":
        return render_template("submit.html", report=None,
                               **form_context(reports, preset=request.args.get("rtype", "")))

    fields, uploads, errors = parse_report_form(request.form, request.files, reports)
    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("submit", rtype=fields["rtype"]))
    try:
        fields["attachments"] = save_uploads(uploads)
        fields.update(status="Pending", comments=[], created_by=session.get("username"),
                      history=[history_entry("Submitted")], guest_hidden=False)
        new_id = store.insert_report(fields)
    except StoreError as e:
        flash(str(e), "error")
        return redirect(url_for("submit", rtype=fields["rtype"]))
    flash(f"Report #{new_id} submitted successfully. It is now Pending approval.")
    return redirect(url_for("reports", rtype=fields["rtype"]))


TRACKED_FIELDS = ["district", "activity", "period", "location", "participants", "tags",
                  "details", "description", "remarks", "submitted_by", "attachments",
                  "archive_refs"]


@app.route("/reports/<int:report_id>/edit", methods=["GET", "POST"])
@staff_required
def report_edit(report_id):
    r = get_visible_report(report_id)
    if not r:
        return redirect(url_for("reports"))
    if not can_edit(r):
        flash("This report is approved and locked. Only the Admin can change it."
              if r.get("status") == "Approved" else "You cannot edit this report.", "error")
        return redirect(url_for("report_detail", report_id=report_id))
    reports = load_reports()
    if request.method == "GET":
        return render_template("submit.html", report=r, **form_context(reports, preset=r["rtype"]))

    fields, uploads, errors = parse_report_form(request.form, request.files, reports, existing=r)
    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("report_edit", report_id=report_id))
    note = request.form.get("change_note", "").strip()
    try:
        fields["attachments"] = fields["attachments"] + save_uploads(uploads)
        changed = [k for k in TRACKED_FIELDS if fields.get(k) != r.get(k)]
        history = list(r.get("history") or [])
        comments = list(r.get("comments") or [])
        status = r.get("status")
        # Back Office answers a query/rejection by resubmitting; the Admin
        # may also just correct the report and leave the status as it is
        resubmit = status in C.RETURNED_STATUSES and (
            not is_admin() or request.form.get("resubmit") == "1")
        if resubmit:
            fields["status"] = "Resubmitted"
            history.append(history_entry("Resubmitted", note, changed))
            comments.append(comment_entry(note or "Corrected and resubmitted.", "resubmit"))
        else:
            history.append(history_entry(
                "Corrected by Admin" if status == "Approved" else "Edited", note, changed))
        fields.update(history=history, comments=comments, updated_at=store.now_iso())
        store.update_report(report_id, fields)
    except StoreError as e:
        flash(str(e), "error")
        return redirect(url_for("report_edit", report_id=report_id))
    flash(f"Report #{report_id} resubmitted for approval." if resubmit
          else f"Report #{report_id} updated.")
    return redirect(url_for("report_detail", report_id=report_id))


# ─────────────────────────────────────────────
# All Reports (sub-sections by type) + dashboard
# ─────────────────────────────────────────────
@app.route("/reports")
@login_required
def reports():
    filters = A.read_filters(request.args)
    all_r = load_reports()
    tracker = None
    data = A.filter_reports(all_r, **filters)
    if filters.get("rtype") == "monthly" and is_staff():
        fy = int(filters.get("fy") or A.current_fy())
        tracker = A.monthly_tracker(all_r, fy)
    return render_template("reports.html", reports=data, filters=filters,
                           fys=A.available_fys(all_r), tracker=tracker)


@app.route("/reports/dashboard")
@staff_required
def reports_dashboard():
    all_r = load_reports()
    filters = A.read_filters(request.args)
    tag = filters.get("tag")
    base = A.filter_reports(all_r, tag=tag) if tag else all_r
    today = date.today()
    year = int(request.args.get("year") or today.year)
    month = int(request.args.get("omonth") or 0) or None
    fy = int(filters.get("fy") or A.current_fy())
    district = filters.get("district", "")
    return render_template(
        "reports_dashboard.html",
        filters=filters, year=year, omonth=month, fy=fy, district=district,
        years=sorted({d.year for d in (A.created_date(r) for r in all_r) if d} | {today.year},
                     reverse=True),
        fys=A.available_fys(all_r),
        overview=A.submission_overview(base, year, month),
        progress=A.district_progress(base, district, fy),
        matrix=A.district_matrix(base, fy),
    )


@app.route("/reports/<int:report_id>")
@login_required
def report_detail(report_id):
    r = get_visible_report(report_id)
    if not r:
        return redirect(url_for("reports"))
    show_files = not is_guest() or settings().get("guest_see_attachments", True)
    return render_template("report_detail.html", report=r, show_files=show_files)


@app.route("/reports/<int:report_id>/comment", methods=["POST"])
@login_required
def report_comment(report_id):
    text = request.form.get("comment", "").strip()
    nxt = safe_next(url_for("report_detail", report_id=report_id))
    if not can_comment():
        flash("Comments are switched off for guests.", "error")
        return redirect(nxt)
    if not text:
        flash("Comment is empty.", "error")
        return redirect(nxt)
    r = get_visible_report(report_id)
    if not r:
        return redirect(url_for("reports"))
    try:
        c = comment_entry(text[:2000])
        if is_guest():
            name = request.form.get("guest_name", "").strip()[:60]
            c["by"] = f"{name} (Guest)" if name else "Guest"
        store.update_report(report_id, {"comments": list(r.get("comments") or []) + [c]})
        flash("Comment added.")
    except StoreError as e:
        flash(str(e), "error")
    return redirect(nxt)


def safe_next(default):
    """Only allow redirects back into this site."""
    nxt = request.form.get("next") or ""
    return nxt if nxt.startswith("/") and not nxt.startswith("//") else default


REVIEW_ACTIONS = {
    # action: (new status, history label, comment kind, reason required)
    "approve": ("Approved", "Approved", "approve", False),
    "query": ("Query", "Query raised", "query", True),
    "reject": ("Rejected", "Rejected", "reject", True),
}


@app.route("/reports/<int:report_id>/review", methods=["POST"])
@staff_required
def report_review(report_id):
    nxt = safe_next(url_for("report_detail", report_id=report_id))
    action = request.form.get("action")
    if action not in REVIEW_ACTIONS:
        abort(400)
    r = get_visible_report(report_id)
    if not r:
        return redirect(url_for("approvals"))
    if not can_review(r):
        flash("Only an Admin or Approver can review this report." if not can_approve()
              else "This report is already approved and locked.", "error")
        return redirect(nxt)
    status, label, kind, needs_text = REVIEW_ACTIONS[action]
    text = request.form.get("comment", "").strip()[:2000]
    if needs_text and not text:
        flash("Please write the query or the reason for rejection.", "error")
        return redirect(nxt)
    changes = {"status": status, "updated_at": store.now_iso(),
               "history": list(r.get("history") or []) + [history_entry(label, text)]}
    if status == "Approved":
        changes.update(approved_by=session.get("display_name"), approved_at=store.now_iso())
    if text:
        changes["comments"] = list(r.get("comments") or []) + [comment_entry(text, kind)]
    try:
        store.update_report(report_id, changes)
        flash(f"Report #{report_id}: {C.STATUS_LABEL[status]}.")
    except StoreError as e:
        flash(str(e), "error")
    return redirect(nxt)


@app.route("/reports/<int:report_id>/unlock", methods=["POST"])
@staff_required
def report_unlock(report_id):
    """Admin only: move an approved (locked) report back to Pending."""
    if not is_admin():
        abort(403)
    r = get_visible_report(report_id)
    if not r:
        return redirect(url_for("reports"))
    note = request.form.get("comment", "").strip()[:2000]
    try:
        store.update_report(report_id, {
            "status": "Pending", "approved_by": None, "approved_at": None,
            "updated_at": store.now_iso(),
            "history": list(r.get("history") or []) + [history_entry("Unlocked by Admin", note)],
        })
        flash(f"Report #{report_id} unlocked and moved back to Pending.")
    except StoreError as e:
        flash(str(e), "error")
    return redirect(url_for("report_detail", report_id=report_id))


@app.route("/reports/<int:report_id>/guest-visibility", methods=["POST"])
@staff_required
def report_guest_visibility(report_id):
    """Admin only: hide or show one report to guests."""
    if not is_admin():
        abort(403)
    r = get_visible_report(report_id)
    if not r:
        return redirect(url_for("reports"))
    hidden = request.form.get("hidden") == "1"
    try:
        store.update_report(report_id, {
            "guest_hidden": hidden,
            "history": list(r.get("history") or []) + [
                history_entry("Hidden from guests" if hidden else "Shown to guests")],
        })
        flash("Guests can no longer see this report." if hidden else "Guests can now see this report.")
    except StoreError as e:
        flash(str(e), "error")
    return redirect(url_for("report_detail", report_id=report_id))


# ─────────────────────────────────────────────
# Approval queue (Admin, Approver) / Returned to me (Back Office)
# ─────────────────────────────────────────────
@app.route("/approvals")
@staff_required
def approvals():
    filters = A.read_filters(request.args)
    filters.pop("status", None)
    all_r = load_reports()
    view = request.args.get("view", "review")
    if role() == C.BACK_OFFICE:
        view = "returned"
    wanted = C.REVIEW_STATUSES if view == "review" else C.RETURNED_STATUSES
    pool = [r for r in all_r if r.get("status") in wanted]
    data = A.filter_reports(pool, **filters)
    counts = {"review": sum(1 for r in all_r if r.get("status") in C.REVIEW_STATUSES),
              "returned": sum(1 for r in all_r if r.get("status") in C.RETURNED_STATUSES)}
    return render_template("approvals.html", reports=data, filters=filters, view=view,
                           counts=counts, fys=A.available_fys(all_r))


# ─────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────
def download_allowed():
    if can_download():
        return True
    flash("Downloads are not available for your account.", "error")
    return False


@app.route("/export")
@staff_required
def export_page():
    if not download_allowed():
        return redirect(url_for("dashboard"))
    all_r = load_reports()
    filters = A.read_filters(request.args)
    count = len(A.filter_reports(all_r, **filters))
    return render_template("export.html", filters=filters, count=count,
                           fys=A.available_fys(all_r))


@app.route("/export/<fmt>")
@staff_required
def export_file(fmt):
    if fmt not in exports.EXPORTERS:
        abort(404)
    if not download_allowed():
        return redirect(url_for("dashboard"))
    all_r = load_reports()
    ids = request.args.get("id")
    if ids:
        wanted = {int(i) for i in ids.split(",") if i.isdigit()}
        data = [r for r in all_r if r["id"] in wanted]
        title = f"Report #{ids}" if len(wanted) == 1 else "Selected reports"
        subtitle = ""
    else:
        filters = A.read_filters(request.args)
        data = A.filter_reports(all_r, **filters)
        title = (C.REPORT_TYPE_LABEL[filters["rtype"]] + "s") if filters.get("rtype") else "All Reports"
        parts = []
        if filters.get("district"):
            parts.append(filters["district"])
        if filters.get("fy"):
            parts.append(A.fy_label(int(filters["fy"])))
        if filters.get("month"):
            parts.append(C.MONTHS[int(filters["month"]) - 1])
        if filters.get("tag"):
            parts.append(f"Tag: {filters['tag']}")
        if filters.get("status"):
            parts.append(filters["status"])
        if filters.get("activity"):
            parts.append(filters["activity"])
        subtitle = " · ".join(parts) or "All districts, all periods"
    buf = exports.EXPORTERS[fmt](data, f"{C.SYSTEM_NAME} – {title}", subtitle)
    name = f"DISHA_{title.replace(' ', '_').replace('#', '')}_{date.today():%Y%m%d}.{fmt}"
    return send_file(buf, mimetype=exports.MIMETYPES[fmt], as_attachment=True,
                     download_name=name)


# ─────────────────────────────────────────────
# User management
# ─────────────────────────────────────────────
def districts_from_form(f):
    return [d for d in f.getlist("districts") if d in C.PERIODIC_DISTRICTS]


@app.route("/users", methods=["GET", "POST"])
@staff_required
def users():
    if not can_manage_users():
        flash("Only the Admin can manage users.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        f = request.form
        username = f.get("username", "").strip().lower()
        password = f.get("password", "")
        new_role = f.get("role")
        if not username or not username.replace("_", "").replace(".", "").isalnum():
            flash("Username may contain letters, numbers, dots and underscores only.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif new_role not in C.ROLES:
            flash("Please choose a role.", "error")
        else:
            try:
                existing = store.list_users()
                if any(u["username"] == username for u in existing):
                    flash(f"User '{username}' already exists.", "error")
                elif not existing and new_role != C.ADMIN:
                    # The first account ends the demo logins, so it must be an Admin
                    flash("The first account must be an Admin. Create your own Admin "
                          "account first, then the other users.", "error")
                else:
                    districts = districts_from_form(f)
                    store.save_user({
                        "username": username, "full_name": f.get("full_name", "").strip(),
                        "role": new_role, "districts": districts,
                        "district": districts[0] if districts else "", "active": True,
                        "password_hash": generate_password_hash(password),
                    }, is_new=True)
                    flash(f"User '{username}' created.")
                    if not existing:
                        session.clear()
                        flash("The demo logins are now switched off. Log in with your new "
                              "Admin account.")
                        return redirect(url_for("login"))
            except StoreError as e:
                flash(str(e), "error")
        return redirect(url_for("users"))
    try:
        user_list = store.list_users()
    except StoreError as e:
        flash(str(e), "error")
        user_list = []
    return render_template("users.html", users=user_list, demo_active=not user_list)


@app.route("/users/<username>", methods=["POST"])
@staff_required
def user_update(username):
    if not can_manage_users():
        abort(403)
    f = request.form
    try:
        users_now = store.list_users()
    except StoreError as e:
        flash(str(e), "error")
        return redirect(url_for("users"))
    user = next((u for u in users_now if u["username"] == username), None)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("users"))
    changes = {"username": username}
    if f.get("role") in C.ROLES:
        changes["role"] = f["role"]
    if f.get("set_districts") == "1":
        changes["districts"] = districts_from_form(f)
        changes["district"] = changes["districts"][0] if changes["districts"] else ""
    if "active" in f:
        changes["active"] = f.get("active") == "1"
    if f.get("password"):
        if len(f["password"]) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("users"))
        changes["password_hash"] = generate_password_hash(f["password"])

    # Never leave the system without an active Admin
    stays_admin = (changes.get("role", user["role"]) == C.ADMIN
                   and changes.get("active", user.get("active", True)))
    other_admins = [u for u in users_now if u["username"] != username
                    and u["role"] == C.ADMIN and u.get("active", True)]
    if user["role"] == C.ADMIN and not stays_admin and not other_admins:
        flash("This is the only active Admin. Create another Admin first.", "error")
        return redirect(url_for("users"))
    try:
        store.save_user(changes, is_new=False)
        flash(f"User '{username}' updated.")
    except (StoreError, KeyError) as e:
        flash(str(e), "error")
    return redirect(url_for("users"))


# ─────────────────────────────────────────────
# Settings (Admin only)
# ─────────────────────────────────────────────
@app.route("/admin/settings", methods=["GET", "POST"])
@staff_required
def settings_page():
    if not is_admin():
        flash("Only the Admin can change settings.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        f = request.form
        try:
            store.save_settings({
                "guest_enabled": f.get("guest_enabled") == "1",
                "guest_districts": [d for d in f.getlist("guest_districts")
                                    if d in C.PERIODIC_DISTRICTS],
                "guest_report_types": [t for t in f.getlist("guest_report_types")
                                       if t in C.REPORT_TYPE_KEYS],
                "guest_can_comment": f.get("guest_can_comment") == "1",
                "guest_see_attachments": f.get("guest_see_attachments") == "1",
                "backoffice_can_download": f.get("backoffice_can_download") == "1",
            })
            flash("Settings saved.")
        except StoreError as e:
            flash(str(e), "error")
        return redirect(url_for("settings_page"))
    hidden = [r for r in load_reports() if r.get("guest_hidden")]
    return render_template("settings.html", s=store.get_settings(), hidden=hidden)


# ─────────────────────────────────────────────
# Files, health and API
# ─────────────────────────────────────────────
@app.route("/files/<path:path>")
@login_required
def uploaded_file(path):
    if is_guest() and not settings().get("guest_see_attachments", True):
        abort(403)
    # Only files that belong to a report this user can see
    if not any(f.get("path") == path for r in load_reports()
               for f in (r.get("attachments") or []) + (r.get("archive_refs") or [])):
        abort(404)
    if b2.ENABLED:
        # Private bucket: a signed link that stops working after 10 minutes
        return redirect(b2.signed_url(b2.ATTACHMENT_PREFIX + path, request.args.get("name")))
    return send_from_directory(store.LOCAL_UPLOAD_DIR, path)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "backend": store.BACKEND,
                    "file_storage": store.FILE_STORAGE,
                    "database_locked": store.BACKEND == "supabase" and not store.INSECURE_KEY})


# ─────────────────────────────────────────────
# Backup and restore (Admin only)
# ─────────────────────────────────────────────
def admin_only(view):
    @wraps(view)
    @staff_required
    def wrapped(*a, **kw):
        if not is_admin():
            flash("Only the Admin can use Backup & Restore.", "error")
            return redirect(url_for("dashboard"))
        return view(*a, **kw)
    return wrapped


@app.route("/admin/backup")
@admin_only
def backup_page():
    backups, to_migrate = [], 0
    try:
        backups = backup.list_backups()
    except StoreError as e:
        flash(str(e), "error")
    if b2.ENABLED and store.BACKEND == "supabase":
        try:
            to_migrate = store.files_to_migrate(store.all_reports())
        except StoreError as e:
            flash(str(e), "error")
    return render_template("backup.html", backups=backups, b2_enabled=b2.ENABLED,
                           to_migrate=to_migrate, keep_days=backup.KEEP_DAYS,
                           cron_ready=bool(os.environ.get("CRON_SECRET")))


@app.route("/admin/backup/now", methods=["POST"])
@admin_only
def backup_now():
    try:
        name, counts = backup.save_to_b2()
        flash(f"Backup saved: {name} ({counts['reports']} reports, {counts['app_users']} users).")
    except StoreError as e:
        flash(str(e), "error")
    return redirect(url_for("backup_page"))


@app.route("/admin/backup/download")
@admin_only
def backup_download():
    """A fresh backup straight to the Admin's computer."""
    try:
        name, data, _ = backup.build()
    except StoreError as e:
        flash(str(e), "error")
        return redirect(url_for("backup_page"))
    return send_file(io.BytesIO(data), mimetype="application/gzip",
                     as_attachment=True, download_name=name)


@app.route("/admin/backup/file/<name>")
@admin_only
def backup_file(name):
    try:
        data = backup.load_from_b2(name)
    except StoreError as e:
        flash(str(e), "error")
        return redirect(url_for("backup_page"))
    return send_file(io.BytesIO(data), mimetype="application/gzip",
                     as_attachment=True, download_name=name)


@app.route("/admin/restore", methods=["POST"])
@admin_only
def restore():
    f = request.form
    if f.get("confirm", "").strip().upper() != "RESTORE":
        flash("Type RESTORE in the box to confirm. Nothing was changed.", "error")
        return redirect(url_for("backup_page"))
    try:
        upload = request.files.get("backup_file")
        if upload and upload.filename:
            data = upload.read()
        elif f.get("name"):
            data = backup.load_from_b2(f["name"])
        else:
            raise StoreError("Choose a backup to restore.")
        counts, safety = backup.restore(backup.parse(data))
    except StoreError as e:
        flash(str(e), "error")
        return redirect(url_for("backup_page"))
    msg = (f"Restore complete: {counts.get('reports', 0)} reports and "
           f"{counts.get('app_users', 0)} users are now in the system.")
    if safety:
        msg += f" The data from before the restore was saved as {safety}."
    flash(msg)
    restored_users = store.list_users()
    if restored_users and not any(u["username"] == session.get("username") for u in restored_users):
        session.clear()
        flash("Your account is not in the restored data. Log in with an account from the backup.")
        return redirect(url_for("login"))
    return redirect(url_for("backup_page"))


@app.route("/admin/migrate-files", methods=["POST"])
@admin_only
def migrate_files():
    try:
        copied, remaining, errors = store.migrate_files_to_b2()
    except StoreError as e:
        flash(str(e), "error")
        return redirect(url_for("backup_page"))
    for e in errors[:5]:
        flash(f"Could not copy {e}", "error")
    if remaining:
        flash(f"Copied {copied} files to Backblaze B2. {remaining} still to go: "
              f"press the button again.")
    else:
        flash(f"Copied {copied} files. All attachments are now stored in Backblaze B2.")
    return redirect(url_for("backup_page"))


@app.route("/cron/nightly", methods=["POST"])
def cron_nightly():
    """Called once a night by the GitHub Action (.github/workflows/nightly-backup.yml).

    Saves a backup to B2. Reading the database also keeps the free
    Supabase project from pausing.
    """
    secret = os.environ.get("CRON_SECRET", "")
    given = request.headers.get("X-Cron-Secret", "")
    if not secret or not hmac.compare_digest(secret, given):
        abort(403)
    try:
        name, counts = backup.save_to_b2()
    except StoreError as e:
        return jsonify({"status": "error", "error": str(e)}), 500
    return jsonify({"status": "ok", "backup": name, "counts": counts})


@app.route("/api/reports")
@login_required
def api_reports():
    return jsonify(A.filter_reports(load_reports(), **A.read_filters(request.args)))


@app.errorhandler(413)
def too_large(_e):
    flash(f"Upload too large. Each file can be up to {C.MAX_FILE_MB} MB, "
          f"{C.MAX_ATTACHMENTS} files per report.", "error")
    return redirect(url_for("submit"))


if __name__ == "__main__":
    app.run(debug=True)
