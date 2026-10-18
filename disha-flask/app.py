import os
import json
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# ─────────────────────────────────────────────
# Supabase client (optional – gracefully skipped if not configured)
# ─────────────────────────────────────────────
supabase = None
try:
    from supabase import create_client
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    pass  # runs fine without Supabase; uses in-memory demo data

# ─────────────────────────────────────────────
# Demo users
# ─────────────────────────────────────────────
DEMO_USERS = {
    "admin":  {"password": "admin123", "role": "Super Admin",  "tab": "admin"},
    "staff":  {"password": "staff123", "role": "Back Office",  "tab": "backoffice"},
}

# ─────────────────────────────────────────────
# In-memory fallback report store
# (replaced by Supabase when configured)
# ─────────────────────────────────────────────
REPORTS = [
    {"id": 47, "office": "Kolkata North",   "activity": "Community Meeting (incl. Women's & Youth)", "rtype": "daily",   "period": "21 Sep 2026", "participants": 62,  "by": "Raju Das",    "date": "20 Sep", "status": "Pending",  "desc": "Community meeting at Palta Ghat with 62 members including women's and youth groups. Agenda: welfare scheme awareness and PMMSY registration.", "attachments": []},
    {"id": 46, "office": "Diamond Harbour", "activity": "Training Programme",                         "rtype": "daily",   "period": "19 Sep 2026", "participants": 45,  "by": "Mita Mondal", "date": "19 Sep", "status": "Approved", "desc": "Three-day training on sustainable fishing practices. 45 fishermen attended. Certificates issued.", "attachments": []},
    {"id": 45, "office": "Basirhat",        "activity": "Legal Clinic & Counselling",                 "rtype": "quarter", "period": "Q3 2026",     "participants": 18,  "by": "Suresh Biswas","date": "18 Sep","status": "Queried",  "desc": "Quarterly legal clinic for 18 fishermen. Query raised regarding supporting affidavits.", "attachments": []},
    {"id": 44, "office": "Kakdwip",         "activity": "Campaign & Awareness",                       "rtype": "daily",   "period": "15 Sep 2026", "participants": 120, "by": "Priya Roy",   "date": "15 Sep", "status": "Approved", "desc": "Mass awareness campaign. 120 individuals reached through pamphlets and street play.", "attachments": []},
    {"id": 43, "office": "Canning",         "activity": "Exposure Visit",                             "rtype": "annual",  "period": "Annual 2026", "participants": 22,  "by": "Arun Ghosh",  "date": "14 Sep", "status": "Approved", "desc": "Annual exposure visit to fishing cooperative in Odisha. 22 members participated.", "attachments": []},
    {"id": 42, "office": "Sagar Island",    "activity": "Deputation & Meeting with Govt. Officials",  "rtype": "daily",   "period": "10 Sep 2026", "participants": 8,   "by": "Mita Mondal", "date": "10 Sep", "status": "Approved", "desc": "Deputation to BDO regarding fishermen ID card delay. BDO committed to resolution in 30 days.", "attachments": []},
    {"id": 41, "office": "Kolkata North",   "activity": "Research & Investigation",                   "rtype": "quarter", "period": "Q3 2026",     "participants": 0,   "by": "Raju Das",    "date": "5 Sep",  "status": "Pending",  "desc": "Field survey of 38 ponds. Water quality, ownership and productivity being documented.", "attachments": []},
]


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def get_reports(filter_type=None, filter_status=None, approved_only=False):
    """Return reports from Supabase if available, otherwise from in-memory list."""
    if supabase:
        try:
            query = supabase.table("reports").select("*").order("id", desc=True)
            if filter_type:
                query = query.eq("rtype", filter_type)
            if filter_status:
                query = query.eq("status", filter_status)
            if approved_only:
                query = query.eq("status", "Approved")
            result = query.execute()
            return result.data or []
        except Exception:
            pass  # fall through to in-memory

    data = list(REPORTS)
    if filter_type:
        data = [r for r in data if r["rtype"] == filter_type]
    if filter_status:
        data = [r for r in data if r["status"] == filter_status]
    if approved_only:
        data = [r for r in data if r["status"] == "Approved"]
    return data


def insert_report(report_data: dict):
    """Insert into Supabase or in-memory list."""
    if supabase:
        try:
            supabase.table("reports").insert(report_data).execute()
            return
        except Exception:
            pass

    new_id = max((r["id"] for r in REPORTS), default=0) + 1
    report_data["id"] = new_id
    report_data["date"] = datetime.now().strftime("%-d %b")
    REPORTS.insert(0, report_data)


def get_report_by_id(report_id: int):
    if supabase:
        try:
            result = supabase.table("reports").select("*").eq("id", report_id).single().execute()
            return result.data
        except Exception:
            pass
    return next((r for r in REPORTS if r["id"] == report_id), None)


# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────
def is_admin():
    return session.get("mode") == "admin"

def is_guest():
    return session.get("mode") == "guest"

def is_logged_in():
    return "mode" in session


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.route("/")
def index():
    if is_logged_in():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "guest":
            session["mode"] = "guest"
            session["username"] = "Guest User"
            session["role"] = "View Only"
            return redirect(url_for("dashboard"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = DEMO_USERS.get(username)
        if user and user["password"] == password:
            session["mode"] = "admin"
            session["username"] = username.capitalize() + " User"
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))
    reports = get_reports(approved_only=is_guest())
    stats = {
        "total": 47,
        "pending": sum(1 for r in REPORTS if r["status"] == "Pending"),
        "approved": sum(1 for r in REPORTS if r["status"] == "Approved"),
        "offices": 6,
    }
    recent = REPORTS[:4]
    return render_template("dashboard.html", stats=stats, recent=recent)


@app.route("/submit", methods=["GET", "POST"])
def submit():
    if not is_logged_in():
        return redirect(url_for("login"))
    if is_guest():
        flash("Log in to submit reports.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        office    = request.form.get("office", "")
        rtype     = request.form.get("rtype", "daily")
        period    = request.form.get("period", "")
        location  = request.form.get("location", "")
        activity  = request.form.get("activity", "")
        desc      = request.form.get("desc", "")
        remarks   = request.form.get("remarks", "")
        by        = request.form.get("by", session.get("username", ""))
        participants = int(request.form.get("participants") or 0)

        # Handle file uploads
        attachments = []
        files = request.files.getlist("attachments")
        for f in files:
            if f and f.filename:
                import base64
                data = base64.b64encode(f.read()).decode()
                attachments.append({
                    "name": f.filename,
                    "type": f.content_type or "application/octet-stream",
                    "data": f"data:{f.content_type};base64,{data}",
                    "size": len(data),
                })

        report = {
            "office":       office,
            "activity":     activity if rtype == "daily" else (
                "Quarter Report" if rtype == "quarter" else "Annual Report"
            ),
            "rtype":        rtype,
            "period":       period,
            "location":     location,
            "participants": participants,
            "by":           by,
            "status":       "Pending",
            "desc":         desc,
            "remarks":      remarks,
            "attachments":  attachments,
        }
        insert_report(report)
        flash(f"Report submitted successfully! It is now Pending Approval.")
        return redirect(url_for("reports"))

    return render_template("submit.html")


@app.route("/reports")
def reports():
    if not is_logged_in():
        return redirect(url_for("login"))

    filter_type   = request.args.get("type")
    filter_status = request.args.get("status")

    if is_guest():
        data = get_reports(approved_only=True)[:3]
    else:
        data = get_reports(filter_type=filter_type, filter_status=filter_status)

    return render_template(
        "reports.html",
        reports=data,
        filter_type=filter_type,
        filter_status=filter_status,
    )


@app.route("/reports/<int:report_id>")
def report_detail(report_id):
    if not is_logged_in():
        return redirect(url_for("login"))
    if is_guest():
        flash("Log in to view full report details.")
        return redirect(url_for("reports"))
    r = get_report_by_id(report_id)
    if not r:
        flash("Report not found.")
        return redirect(url_for("reports"))
    return render_template("report_detail.html", report=r)


# ─────────────────────────────────────────────
# API endpoints (for JS fetch calls)
# ─────────────────────────────────────────────
@app.route("/api/reports")
def api_reports():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    data = get_reports(approved_only=is_guest())
    return jsonify(data)


@app.route("/api/reports/<int:report_id>")
def api_report(report_id):
    if not is_logged_in() or is_guest():
        return jsonify({"error": "Unauthorized"}), 401
    r = get_report_by_id(report_id)
    return jsonify(r) if r else (jsonify({"error": "Not found"}), 404)


if __name__ == "__main__":
    app.run(debug=True)
