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
FILTER_KEYS = ("rtype", "status", "district", "tag", "subject", "activity", "fy", "month", "q")


def read_filters(args):
    f = {k: (args.get(k) or "").strip() for k in FILTER_KEYS}
    return {k: v for k, v in f.items() if v}


def filter_reports(reports, rtype=None, status=None, district=None, tag=None,
                   activity=None, fy=None, month=None, q=None, approved_only=False,
                   subject=None):
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
        if subject and subject not in (r.get("tag_paths") or r.get("tags") or []):
            continue
        if activity and r.get("activity") != activity:
            continue
        if fy and str(report_fy(r)) != str(fy):
            continue
        if month and str(activity_month(r)[1]) != str(month):
            continue
        if ql:
            hay = " ".join(str(r.get(k) or "") for k in
                           ("id", "district", "block", "gp", "village", "activity",
                            "period", "location", "source_channel", "description",
                            "remarks", "submitted_by")).lower()
            hay += " " + " ".join((r.get("tags") or []) + (r.get("tag_paths") or [])).lower()
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
        "pending": sum(status.get(s, 0) for s in C.REVIEW_STATUSES),
        "returned": sum(status.get(s, 0) for s in C.RETURNED_STATUSES),
        "approved": status.get("Approved", 0),
        "approval_rate": round(100 * status.get("Approved", 0) / total) if total else 0,
        "active_districts": len(C.DISTRICTS),
        "reporting_districts": len({r.get("district") for r in this_month
                                    if r.get("district") in C.DISTRICTS}),
        "charts": {
            "monthly": {"labels": [C.MONTHS_SHORT[m - 1] for m in fy_months],
                        "data": list(fy_months.values())},
            "status": {"labels": [C.STATUS_LABEL[s] for s in C.STATUSES],
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


# ─────────────────────────────────────────────
# Report linking: daily reports ↔ monthly / quarterly / half-yearly / annual
# ─────────────────────────────────────────────
def _add_months(y, m, n):
    m0 = m - 1 + n
    return y + m0 // 12, m0 % 12 + 1


def _month_end(y, m):
    ny, nm = _add_months(y, m, 1)
    return date.fromordinal(date(ny, nm, 1).toordinal() - 1)


def period_range(r):
    """(first day, last day) a report covers, or None if unknown."""
    try:
        if r.get("rtype") == "daily":
            d = date.fromisoformat(str(r.get("activity_date"))[:10])
            return d, d
        fy = int(r.get("fy"))
        if r["rtype"] == "monthly":
            m = int(r["month"])
            y = fy if m >= 4 else fy + 1
            return date(y, m, 1), _month_end(y, m)
        if r["rtype"] == "quarterly":
            y, m = _add_months(fy, 4, 3 * (int(r["quarter"]) - 1))
            ey, em = _add_months(y, m, 2)
            return date(y, m, 1), _month_end(ey, em)
        if r["rtype"] == "halfyearly":
            y, m = _add_months(fy, 4, 6 * (int(r["half"]) - 1))
            ey, em = _add_months(y, m, 5)
            return date(y, m, 1), _month_end(ey, em)
        if r["rtype"] == "annual":
            return date(fy, 4, 1), date(fy + 1, 3, 31)
    except (TypeError, ValueError, KeyError):
        return None
    return None


def _covers(periodic, daily):
    """Head Office reports cover every district."""
    return (periodic.get("district") == C.HEAD_OFFICE
            or periodic.get("district") == daily.get("district"))


def linked_daily(periodic, reports):
    """Daily reports that fall inside a periodic report's period and district."""
    rng = period_range(periodic)
    if not rng or periodic.get("rtype") == "daily":
        return []
    out = []
    for r in reports:
        if r.get("rtype") != "daily" or not _covers(periodic, r):
            continue
        d = period_range(r)
        if d and rng[0] <= d[0] <= rng[1]:
            out.append(r)
    return sorted(out, key=lambda r: str(r.get("activity_date")), reverse=True)


def containing_periodic(daily, reports):
    """Monthly, quarterly, half-yearly and annual reports a daily report belongs to."""
    d = period_range(daily)
    if not d or daily.get("rtype") != "daily":
        return []
    order = {k: i for i, k in enumerate(C.REPORT_TYPE_KEYS)}
    out = []
    for r in reports:
        if r.get("rtype") == "daily" or not _covers(r, daily):
            continue
        rng = period_range(r)
        if rng and rng[0] <= d[0] <= rng[1]:
            out.append(r)
    return sorted(out, key=lambda r: (order.get(r["rtype"], 9), r.get("district") == C.HEAD_OFFICE))


def link_summary(daily_reports):
    """Totals of linked daily reports (rejected ones left out)."""
    rs = [r for r in daily_reports if r.get("status") != "Rejected"]
    return {
        "count": len(rs),
        "approved": sum(1 for r in rs if r.get("status") == "Approved"),
        "participants": sum(int(r.get("participants_total") or 0) for r in rs),
        "by_activity": Counter(r.get("activity") for r in rs).most_common(),
        "by_issue": Counter(t for r in rs for t in (r.get("tags") or [])).most_common(),
    }


# ─────────────────────────────────────────────
# Issue tracking
# ─────────────────────────────────────────────
def sort_date(r):
    rng = period_range(r)
    return rng[0] if rng else (created_date(r) or date.min)


FOLLOWUP_REPLY = ("Awaiting reply", "No reply after deadline")


def needs_followup(r):
    """A follow-up is noted, or a letter/RTI is still waiting for a reply."""
    d = r.get("details") or {}
    return bool(d.get("followup") or d.get("referrals") or d.get("reply") in FOLLOWUP_REPLY)


def issue_overview(reports, issue_names):
    """One row per issue: activities, approved, districts, latest date, follow-ups."""
    rows = []
    names = list(issue_names) + sorted({t for r in reports for t in (r.get("tags") or [])}
                                       - set(issue_names))
    for name in names:
        rs = [r for r in reports if name in (r.get("tags") or [])]
        acts = [r for r in rs if is_activity(r)]
        latest = max((sort_date(r) for r in rs), default=None)
        rows.append({
            "issue": name, "in_list": name in issue_names, "total": len(rs),
            "activities": len(acts),
            "approved": sum(1 for r in rs if r.get("status") == "Approved"),
            "districts": len({r.get("district") for r in rs}),
            "participants": sum(int(r.get("participants_total") or 0) for r in acts),
            "followups": sum(1 for r in rs if needs_followup(r)),
            "latest": latest if latest and latest != date.min else None,
        })
    return rows


def issue_detail(reports, path, subjects, fy=None):
    """Everything tagged with an issue (or one of its subjects), for one FY or all time.

    subjects: [(path, label)] of the next level down, for the breakdown.
    """
    rs = [r for r in reports if path in (r.get("tag_paths") or r.get("tags") or [])]
    if fy:
        rs = [r for r in rs if str(report_fy(r)) == str(fy)]
    rs.sort(key=sort_date, reverse=True)
    acts = [r for r in rs if is_activity(r)]
    month_idx = {m: i for i, m in enumerate(C.FY_MONTHS)}
    # Monthly volume: one FY, or the last 12 months that have data
    if fy:
        labels = [C.MONTHS_SHORT[m - 1] for m in C.FY_MONTHS]
        monthly = [0] * 12
        for r in acts:
            monthly[month_idx[sort_date(r).month]] += 1
    else:
        counts = Counter((sort_date(r).year, sort_date(r).month) for r in acts)
        keys = sorted(counts)[-12:]
        labels = [f"{C.MONTHS_SHORT[m - 1]} {str(y)[-2:]}" for y, m in keys]
        monthly = [counts[k] for k in keys]
    timeline = OrderedDict()
    for r in rs:
        d = sort_date(r)
        timeline.setdefault(f"{C.MONTHS[d.month - 1]} {d.year}" if d != date.min else "—", []).append(r)
    by_activity = Counter(r.get("activity") for r in acts)
    by_district = Counter(r.get("district") for r in rs)
    status = Counter(r.get("status") for r in rs)
    return {
        "reports": rs, "total": len(rs), "activities": len(acts),
        "approved": status.get("Approved", 0),
        "pending": sum(status.get(s, 0) for s in C.REVIEW_STATUSES + C.RETURNED_STATUSES),
        "participants": sum(int(r.get("participants_total") or 0) for r in acts),
        "districts": len(by_district),
        "followups": [r for r in rs if needs_followup(r)],
        "timeline": timeline,
        "subjects": [(p, label, sum(1 for r in rs if p in (r.get("tag_paths") or [])))
                     for p, label in subjects],
        "charts": {
            "monthly": {"labels": labels, "data": monthly},
            "activity": {"labels": [a for a, _ in by_activity.most_common()],
                         "data": [n for _, n in by_activity.most_common()]},
            "district": {"labels": [d for d, _ in by_district.most_common()],
                         "data": [n for _, n in by_district.most_common()]},
            "status": {"labels": [C.STATUS_LABEL[s] for s in C.STATUSES],
                       "data": [status.get(s, 0) for s in C.STATUSES]},
        },
    }
