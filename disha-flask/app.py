import logging
import os
from datetime import date, datetime
from functools import wraps

from dotenv import load_dotenv

load_dotenv()

from flask import (  # noqa: E402
    Flask, abort, flash, jsonify, redirect, render_template, request,
    send_file, send_from_directory, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash  # noqa: E402

import analytics as A  # noqa: E402
import config as C  # noqa: E402
import exports  # noqa: E402
import store  # noqa: E402
from store import StoreError  # noqa: E402

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
# 10 attachments × 25 MB plus form fields
app.config["MAX_CONTENT_LENGTH"] = (C.MAX_ATTACHMENTS * C.MAX_FILE_MB + 5) * 1024 * 1024


# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────
def is_admin():
    return session.get("mode") == "admin"


def is_guest():
    return session.get("mode") == "guest"


def is_logged_in():
    return "mode" in session


def can_approve():
    return is_admin() and session.get("role") in C.APPROVER_ROLES


def can_manage_users():
    return is_admin() and session.get("role") in C.USER_ADMIN_ROLES


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


def load_reports():
    """All reports visible to the current user (guests see approved only)."""
    try:
        reports = store.all_reports()
    except StoreError as e:
        flash(str(e), "error")
        reports = []
    if is_guest():
        reports = [r for r in reports if r.get("status") == "Approved"]
    return reports


@app.context_processor
def inject_globals():
    return {
        "C": C,
        "can_approve": can_approve(),
        "can_manage_users": can_manage_users(),
        "backend": store.BACKEND,
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
    return f.get("url") or url_for("uploaded_file", path=f.get("path", ""))


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
                           role=user.get("role", "Back Office"),
                           district=user.get("district") or "")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    try:
        demo_active = store.demo_logins_active()
    except StoreError:
        demo_active = False
    return render_template("login.html", demo_active=demo_active)


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
    pending = [r for r in reports if r.get("status") == "Pending"][:8]
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


@app.route("/submit", methods=["GET", "POST"])
@staff_required
def submit():
    reports = load_reports()
    if request.method == "GET":
        return render_template("submit.html", archive=archive_files(reports),
                               fys=A.available_fys(reports),
                               current_fy=A.current_fy(),
                               preset=request.args.get("rtype", ""))

    f = request.form
    rtype = f.get("rtype", "daily")
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
        for fs in request.files.getlist(f"files_{cat['key']}"):
            if fs and fs.filename:
                uploads.append((cat["key"], fs))
    refs = []
    by_ref = {a["ref"]: a for a in archive_files(reports)}
    for ref in f.getlist("archive_ref"):
        if ref in by_ref:
            rid, idx = ref.split("|")
            src = next(r for r in reports if str(r["id"]) == rid)["attachments"][int(idx)]
            refs.append({"report_id": int(rid), "name": src.get("name"),
                         "category": src.get("category"), "type": src.get("type"),
                         "url": src.get("url"), "path": src.get("path")})
    if len(uploads) + len(refs) > C.MAX_ATTACHMENTS:
        errors.append(f"A report can have at most {C.MAX_ATTACHMENTS} attachments.")
    for _, fs in uploads:
        ext = fs.filename.rsplit(".", 1)[-1].lower() if "." in fs.filename else ""
        if ext not in C.ALLOWED_EXTENSIONS:
            errors.append(f"File type not allowed: {fs.filename}")

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("submit", rtype=rtype))

    attachments = []
    try:
        for cat, fs in uploads:
            content = fs.read()
            if len(content) > C.MAX_FILE_MB * 1024 * 1024:
                flash(f"{fs.filename} is larger than {C.MAX_FILE_MB} MB and was skipped.", "error")
                continue
            url, path = store.save_file(fs.filename, content, fs.content_type)
            attachments.append({"category": cat, "name": fs.filename,
                                "type": fs.content_type or "application/octet-stream",
                                "size": len(content), "url": url, "path": path})

        report = {
            "rtype": rtype, "district": district, "activity": activity,
            "period": period, "location": f.get("location", "").strip(),
            "participants": participants, "participants_total": participants.get("total", 0),
            "tags": tags, "details": details,
            "description": f.get("description", "").strip(),
            "remarks": f.get("remarks", "").strip(),
            "submitted_by": f.get("submitted_by", "").strip() or session.get("display_name"),
            "status": "Pending", "comments": [], "attachments": attachments,
            "archive_refs": refs,
            "activity_date": None, "month": None, "quarter": None, "half": None,
        }
        report.update(extra)
        new_id = store.insert_report(report)
    except StoreError as e:
        flash(str(e), "error")
        return redirect(url_for("submit", rtype=rtype))
    flash(f"Report #{new_id} submitted successfully. It is now Pending approval.")
    return redirect(url_for("reports", rtype=rtype))


# ─────────────────────────────────────────────
# All Reports (sub-sections by type) + dashboard
# ─────────────────────────────────────────────
@app.route("/reports")
@login_required
def reports():
    filters = A.read_filters(request.args)
    all_r = load_reports()
    tracker = None
    if is_guest():
        data = A.filter_reports(all_r)[:3]
    else:
        data = A.filter_reports(all_r, **filters)
        if filters.get("rtype") == "monthly":
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
    if is_guest():
        flash("Log in to view full report details.", "error")
        return redirect(url_for("reports"))
    try:
        r = store.get_report(report_id)
    except StoreError as e:
        flash(str(e), "error")
        r = None
    if not r:
        flash("Report not found.", "error")
        return redirect(url_for("reports"))
    return render_template("report_detail.html", report=r)


def _add_comment(report, text):
    comments = list(report.get("comments") or [])
    comments.append({"by": session.get("display_name"), "at": store.now_iso(), "text": text})
    return comments


@app.route("/reports/<int:report_id>/comment", methods=["POST"])
@staff_required
def report_comment(report_id):
    text = request.form.get("comment", "").strip()
    nxt = request.form.get("next") or url_for("report_detail", report_id=report_id)
    if not text:
        flash("Comment is empty.", "error")
        return redirect(nxt)
    try:
        r = store.get_report(report_id)
        if not r:
            abort(404)
        store.update_report(report_id, {"comments": _add_comment(r, text)})
        flash("Comment added.")
    except StoreError as e:
        flash(str(e), "error")
    return redirect(nxt)


@app.route("/reports/<int:report_id>/status", methods=["POST"])
@staff_required
def report_status(report_id):
    if not can_approve():
        flash("Only a Super Admin can approve reports.", "error")
        return redirect(url_for("report_detail", report_id=report_id))
    status = request.form.get("status")
    nxt = request.form.get("next") or url_for("report_detail", report_id=report_id)
    if status not in C.STATUSES:
        abort(400)
    try:
        r = store.get_report(report_id)
        if not r:
            abort(404)
        changes = {"status": status}
        if status == "Approved":
            changes.update(approved_by=session.get("display_name"), approved_at=store.now_iso())
        else:
            changes.update(approved_by=None, approved_at=None)
        text = request.form.get("comment", "").strip()
        if text:
            changes["comments"] = _add_comment(r, text)
        store.update_report(report_id, changes)
        flash(f"Report #{report_id} marked {status}.")
    except StoreError as e:
        flash(str(e), "error")
    return redirect(nxt)


# ─────────────────────────────────────────────
# Approval queue
# ─────────────────────────────────────────────
@app.route("/approvals")
@staff_required
def approvals():
    filters = A.read_filters(request.args)
    filters.pop("status", None)
    all_r = load_reports()
    data = A.filter_reports(all_r, status="Pending", **filters)
    return render_template("approvals.html", reports=data, filters=filters,
                           fys=A.available_fys(all_r))


# ─────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────
@app.route("/export")
@staff_required
def export_page():
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
@app.route("/users", methods=["GET", "POST"])
@staff_required
def users():
    if not can_manage_users():
        flash("Only a Super Admin can manage users.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        f = request.form
        username = f.get("username", "").strip().lower()
        password = f.get("password", "")
        role = f.get("role")
        if not username or not username.replace("_", "").replace(".", "").isalnum():
            flash("Username may contain letters, numbers, dots and underscores only.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif role not in C.ROLES:
            flash("Please choose a role.", "error")
        else:
            try:
                if any(u["username"] == username for u in store.list_users()):
                    flash(f"User '{username}' already exists.", "error")
                else:
                    store.save_user({
                        "username": username, "full_name": f.get("full_name", "").strip(),
                        "role": role, "district": f.get("district", ""), "active": True,
                        "password_hash": generate_password_hash(password),
                    }, is_new=True)
                    flash(f"User '{username}' created.")
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
    changes = {"username": username}
    if f.get("role") in C.ROLES:
        changes["role"] = f["role"]
    if "district" in f:
        changes["district"] = f.get("district", "")
    if "active" in f:
        changes["active"] = f.get("active") == "1"
    if f.get("password"):
        if len(f["password"]) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("users"))
        changes["password_hash"] = generate_password_hash(f["password"])
    try:
        store.save_user(changes, is_new=False)
        flash(f"User '{username}' updated.")
    except (StoreError, KeyError) as e:
        flash(str(e), "error")
    return redirect(url_for("users"))


# ─────────────────────────────────────────────
# Files, health and API
# ─────────────────────────────────────────────
@app.route("/files/<path:path>")
@staff_required
def uploaded_file(path):
    return send_from_directory(store.LOCAL_UPLOAD_DIR, path)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "backend": store.BACKEND})


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
