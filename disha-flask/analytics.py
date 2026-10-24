"""
Filtering and aggregation used by the dashboard, All Reports, analytics
and export. Works on plain report dicts from store.all_reports().
"""
from collections import Counter, OrderedDict
from datetime import date, datetime

import config as C


# ─────────────────────────────────────────────
# Dates and financial years
# ─────────────────────────────────────────────
def fy_of(d):
    return d.year if d.month >= 4 else d.year - 1


def fy_label(fy):
    return f"FY {fy}-{str(fy + 1)[-2:]}"


def current_fy(today=None):
    return fy_of(today or date.today())


def created_date(r):
    try:
        return datetime.fromisoformat(str(r.get("created_at"))[:19]).date()
    except (TypeError, ValueError):
        return None


def activity_month(r):
    """(year, month) the work in a report belongs to."""
    if r.get("rtype") == "daily" and r.get("activity_date"):
        d = date.fromisoformat(str(r["activity_date"])[:10])
        return d.year, d.month
    if r.get("rtype") == "monthly" and r.get("month") and r.get("fy"):
        m = int(r["month"])
        return (int(r["fy"]) if m >= 4 else int(r["fy"]) + 1), m
    d = created_date(r)
    return (d.year, d.month) if d else (None, None)


def report_fy(r):
    if r.get("fy"):
        return int(r["fy"])
    y, m = activity_month(r)
    return fy_of(date(y, m, 1)) if y else None


def is_activity(r):
    """A report that represents a field activity (not a consolidated summary)."""
    return r.get("activity") and r.get("activity") != C.CONSOLIDATED


# ─────────────────────────────────────────────
# Filters (shared by every page – tag filter works everywhere)
# ─────────────────────────────────────────────
FILTER_KEYS = ("rtype", "status", "district", "tag", "activity", "fy", "month", "q")


def read_filters(args):
    f = {k: (args.get(k) or "").strip() for k in FILTER_KEYS}
    return {k: v for k, v in f.items() if v}


def filter_reports(reports, rtype=None, status=None, district=None, tag=None,
                   activity=None, fy=None, month=None, q=None, approved_only=False):
    out = []
    ql = (q or "").lower()
    for r in reports:
        if approved_only and r.get("status") != "Approved":
            continue
        if rtype and r.get("rtype") != rtype:
            continue
        if status and r.get("status") != status:
            continue
        if district and r.get("district") != district:
            continue
        if tag and tag not in (r.get("tags") or []):
            continue
        if activity and r.get("activity") != activity:
            continue
        if fy and str(report_fy(r)) != str(fy):
            continue
        if month and str(activity_month(r)[1]) != str(month):
            continue
        if ql:
            hay = " ".join(str(r.get(k) or "") for k in
                           ("id", "district", "activity", "period", "location",
                            "description", "remarks", "submitted_by")).lower()
            hay += " " + " ".join(r.get("tags") or []).lower()
            if ql not in hay:
                continue
        out.append(r)
    return out


def available_fys(reports, today=None):
    fys = {report_fy(r) for r in reports if report_fy(r)}
    fys.add(current_fy(today))
    return sorted(fys, reverse=True)


# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────
def dashboard(reports, today=None):
    today = today or date.today()
    fy = current_fy(today)
    status = Counter(r.get("status") for r in reports)
    this_month = [r for r in reports if activity_month(r) == (today.year, today.month)]
    total = len(reports)
    fy_months = OrderedDict((m, 0) for m in C.FY_MONTHS)
    for r in reports:
        if report_fy(r) == fy:
            fy_months[activity_month(r)[1]] += 1
    by_district = Counter(r.get("district") for r in reports)
    by_activity = Counter(r.get("activity") for r in reports if is_activity(r))
    return {
        "fy": fy,
        "fy_label": fy_label(fy),
        "total": total,
        "this_month": len(this_month),
        "pending": status.get("Pending", 0),
        "approved": status.get("Approved", 0),
        "approval_rate": round(100 * status.get("Approved", 0) / total) if total else 0,
        "active_districts": len(C.DISTRICTS),
        "reporting_districts": len({r.get("district") for r in this_month
                                    if r.get("district") in C.DISTRICTS}),
        "charts": {
            "monthly": {"labels": [C.MONTHS_SHORT[m - 1] for m in fy_months],
                        "data": list(fy_months.values())},
            "status": {"labels": C.STATUSES,
                       "data": [status.get(s, 0) for s in C.STATUSES]},
            "district": {"labels": C.PERIODIC_DISTRICTS,
                         "data": [by_district.get(d, 0) for d in C.PERIODIC_DISTRICTS]},
            "activity": {"labels": C.ACTIVITY_NAMES,
                         "data": [by_activity.get(a, 0) for a in C.ACTIVITY_NAMES]},
        },
    }


# ─────────────────────────────────────────────
# All Reports › Dashboard
# ─────────────────────────────────────────────
def submission_overview(reports, year, month=None):
    """Reports submitted per month of a year (or per day of a month), by report type."""
    import calendar
    if month:
        days = calendar.monthrange(year, month)[1]
        labels = [str(d) for d in range(1, days + 1)]
    else:
        labels = list(C.MONTHS_SHORT)
    series = {t: [0] * len(labels) for t in C.REPORT_TYPE_KEYS}
    by_activity = Counter()
    count = 0
    for r in reports:
        d = created_date(r)
        if not d or d.year != year or (month and d.month != month):
            continue
        idx = (d.day if month else d.month) - 1
        series[r["rtype"]][idx] += 1
        count += 1
        if is_activity(r):
            by_activity[r["activity"]] += 1
    return {
        "labels": labels,
        "datasets": [{"key": t["key"], "label": t["label"], "data": series[t["key"]]}
                     for t in C.REPORT_TYPES],
        "total": count,
        "by_type": {t: sum(v) for t, v in series.items()},
        "by_activity": [(a, by_activity.get(a, 0)) for a in C.ACTIVITY_NAMES],
    }


def district_progress(reports, district, fy):
    """Month-wise activity progress for one district (or all if district is empty)."""
    acts = [r for r in reports if is_activity(r) and report_fy(r) == fy
            and (not district or r.get("district") == district)]
    month_idx = {m: i for i, m in enumerate(C.FY_MONTHS)}
    matrix = {a: [0] * 12 for a in C.ACTIVITY_NAMES}
    participants = 0
    for r in acts:
        m = activity_month(r)[1]
        if r["activity"] in matrix and m in month_idx:
            matrix[r["activity"]][month_idx[m]] += 1
        participants += int(r.get("participants_total") or 0)
    monthly = [sum(matrix[a][i] for a in matrix) for i in range(12)]
    return {
        "district": district,
        "fy": fy,
        "fy_label": fy_label(fy),
        "total": len(acts),
        "participants": participants,
        "labels": [C.MONTHS_SHORT[m - 1] for m in C.FY_MONTHS],
        "monthly": monthly,
        "by_activity": [(a, sum(matrix[a])) for a in C.ACTIVITY_NAMES],
        "matrix": [{"activity": a, "data": matrix[a]} for a in C.ACTIVITY_NAMES],
    }


def district_matrix(reports, fy):
    """Districts × activity types table for the selected FY."""
    rows = []
    for d in C.PERIODIC_DISTRICTS:
        c = Counter(r["activity"] for r in reports
                    if is_activity(r) and r.get("district") == d and report_fy(r) == fy)
        rows.append({"district": d, "counts": [c.get(a, 0) for a in C.ACTIVITY_NAMES],
                     "total": sum(c.values())})
    totals = [sum(r["counts"][i] for r in rows) for i in range(len(C.ACTIVITY_NAMES))]
    return {"rows": rows, "totals": totals, "grand": sum(totals)}


def monthly_tracker(reports, fy, today=None):
    """Due / Done grid of monthly reports: districts × FY months."""
    today = today or date.today()
    done = {}
    for r in reports:
        if r.get("rtype") == "monthly" and str(r.get("fy")) == str(fy) and r.get("month"):
            done.setdefault((r["district"], int(r["month"])), r)
    rows = []
    for d in C.PERIODIC_DISTRICTS:
        cells = []
        for m in C.FY_MONTHS:
            year = fy if m >= 4 else fy + 1
            r = done.get((d, m))
            if r:
                cells.append({"state": "done", "id": r["id"], "status": r.get("status")})
            elif (year, m) < (today.year, today.month):
                cells.append({"state": "due"})
            else:
                cells.append({"state": "upcoming"})
        rows.append({"district": d, "cells": cells,
                     "done": sum(c["state"] == "done" for c in cells),
                     "due": sum(c["state"] == "due" for c in cells)})
    return {"fy": fy, "fy_label": fy_label(fy),
            "labels": [C.MONTHS_SHORT[m - 1] for m in C.FY_MONTHS], "rows": rows}
