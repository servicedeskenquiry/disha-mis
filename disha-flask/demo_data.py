"""
Demo reports for the in-memory store (and the Supabase seed file).

Generated deterministically so charts look realistic and the same on
every restart. Uses the real district list from config.py.
"""
import random
from datetime import date, timedelta

import config as C

PEOPLE = ["Raju Das", "Mita Mondal", "Suresh Biswas", "Priya Roy", "Arun Ghosh",
          "Tapas Jana", "Rina Bera", "Sujit Maity", "Anjali Sardar", "Bikash Pal"]
PLACES = ["Fraserganj", "Kakdwip", "Digha", "Tajpur", "Shankarpur", "Hingalganj",
          "Uluberia", "Balagarh", "Krishnanagar", "Farakka", "Kaliachak", "Balurghat",
          "Mal Bazar", "Tufanganj", "Kumargram"]
SAMPLE_TEXT = {
    "Community Meeting (incl. Women's & Youth)":
        "Community meeting with fisher families including women's and youth groups. "
        "Discussed welfare scheme awareness and registration support.",
    "Training Programme":
        "Training on sustainable fishing practices and safety at sea. Certificates issued.",
    "Campaign & Awareness":
        "Awareness campaign on fishermen ID cards and social security entitlements.",
    "Deputation & Meeting with Govt. Officials":
        "Deputation to the BDO / Fisheries Extension Officer on pending ID cards and "
        "compensation claims.",
    "Research & Investigation (Survey / Field Visit)":
        "Field survey of village ponds and landing centres to document access and ownership.",
    "Block / District / State Conference":
        "Block-level conference of fisher unions on the net ban period and relief.",
    "Letter to Authorities (incl. RTI)":
        "RTI application on the status of savings-cum-relief payments.",
    "Policy Intervention Document":
        "Memorandum on inland water body leasing submitted to the district office.",
    "Legal Clinic & Counselling":
        "Legal clinic on fishing licence and boat registration disputes.",
    "Exposure Visit":
        "Exposure visit of women fish workers to a fish drying cooperative.",
    C.OTHERS: "Support visit to the fisher cooperative.",
}
ACTIVITY_WEIGHTS = {
    "Community Meeting (incl. Women's & Youth)": 9, "Training Programme": 7,
    "Campaign & Awareness": 6, "Deputation & Meeting with Govt. Officials": 5,
    "Research & Investigation (Survey / Field Visit)": 4,
    "Letter to Authorities (incl. RTI)": 3, "Block / District / State Conference": 2,
    "Legal Clinic & Counselling": 2, "Policy Intervention Document": 1,
    "Exposure Visit": 1, C.OTHERS: 1,
}
BLOCKS = ["Block A", "Block B", "Block C"]


def _participants(rng, activity):
    if activity.startswith("Research"):
        return {}, 0
    total = rng.randint(8, 120)
    women = rng.randint(total // 5, total // 2)
    p = {"total": total, "women": women, "men": total - women}
    if rng.random() < 0.7:
        p["fisher"] = rng.randint(total // 3, total)
    if rng.random() < 0.4:
        p["fish_workers"] = rng.randint(1, max(1, total // 3))
    if rng.random() < 0.3:
        p["leaders"] = rng.randint(1, 6)
    return p, total


def build_reports():
    rng = random.Random(7)
    reports = []
    rid = 0
    today = date(2026, 10, 23)
    start = date(2026, 4, 1)
    activities = C.ACTIVITY_NAMES

    # Daily activity reports, Apr – Oct 2026
    d = start
    while d <= today:
        for _ in range(rng.choice([0, 0, 1, 1, 2])):
            rid += 1
            act = rng.choices(activities, weights=[ACTIVITY_WEIGHTS[a] for a in activities])[0]
            dist = rng.choice(C.DISTRICTS)
            p, total = _participants(rng, act)
            created = d + timedelta(days=rng.randint(0, 2))
            reports.append({
                "id": rid, "rtype": "daily", "district": dist, "activity": act,
                "activity_date": d.isoformat(), "period": d.strftime("%d %b %Y"),
                "fy": d.year if d.month >= 4 else d.year - 1, "month": d.month,
                "location": rng.choice(PLACES),
                "block": rng.choice(BLOCKS), "village": rng.choice(PLACES).split(",")[0],
                "source_channel": rng.choice(["WhatsApp", "WhatsApp", "WhatsApp", "Email", "PDF"]),
                "participants": p, "participants_total": total,
                "tags": rng.sample(C.ISSUE_TAGS, rng.choice([1, 1, 2, 3])),
                "details": {}, "description": SAMPLE_TEXT[act],
                "remarks": "", "submitted_by": rng.choice(PEOPLE),
                "status": "Approved" if (today - d).days > 10 or rng.random() < 0.4 else "Pending",
                "comments": [], "attachments": [], "archive_refs": [],
                "created_at": f"{created.isoformat()}T10:00:00+00:00",
            })
        d += timedelta(days=1)

    # Monthly reports – most districts done for past months, some due
    for m in [4, 5, 6, 7, 8, 9]:
        for dist in C.DISTRICTS:
            if rng.random() < (0.9 if m < 8 else 0.65):
                rid += 1
                created = date(2026, m, 28) + timedelta(days=rng.randint(3, 9))
                reports.append({
                    "id": rid, "rtype": "monthly", "district": dist,
                    "activity": C.CONSOLIDATED, "activity_date": None,
                    "period": f"{C.MONTHS[m - 1]} 2026", "fy": 2026, "month": m,
                    "location": dist, "participants": {}, "participants_total": 0,
                    "tags": rng.sample(C.ISSUE_TAGS, 2), "details": {},
                    "description": f"Monthly summary of activities in {dist} for "
                                   f"{C.MONTHS[m - 1]} 2026.",
                    "remarks": "", "submitted_by": rng.choice(PEOPLE),
                    "status": "Approved" if m < 9 else rng.choice(["Approved", "Pending"]),
                    "comments": [], "attachments": [], "archive_refs": [],
                    "created_at": f"{created.isoformat()}T10:00:00+00:00",
                })

    # Quarterly / half-yearly for a few districts and Head Office
    for dist in [C.HEAD_OFFICE, "South 24 Parganas", "Purba Medinipur", "North 24 Parganas"]:
        rid += 1
        reports.append({
            "id": rid, "rtype": "quarterly", "district": dist, "activity": C.CONSOLIDATED,
            "activity_date": None, "period": f"{C.QUARTERS[0]} FY 2026-27", "fy": 2026,
            "quarter": 1, "location": dist, "participants": {}, "participants_total": 0,
            "tags": rng.sample(C.ISSUE_TAGS, 2), "details": {},
            "description": f"Quarterly progress report for {dist}.", "remarks": "",
            "submitted_by": rng.choice(PEOPLE), "status": "Approved", "comments": [],
            "attachments": [], "archive_refs": [],
            "created_at": "2026-07-12T10:00:00+00:00",
        })
        rid += 1
        reports.append({
            "id": rid, "rtype": "quarterly", "district": dist, "activity": C.CONSOLIDATED,
            "activity_date": None, "period": f"{C.QUARTERS[1]} FY 2026-27", "fy": 2026,
            "quarter": 2, "location": dist, "participants": {}, "participants_total": 0,
            "tags": rng.sample(C.ISSUE_TAGS, 2), "details": {},
            "description": f"Quarterly progress report for {dist}.", "remarks": "",
            "submitted_by": rng.choice(PEOPLE), "status": "Pending", "comments": [],
            "attachments": [], "archive_refs": [],
            "created_at": "2026-10-14T10:00:00+00:00",
        })
    rid += 1
    reports.append({
        "id": rid, "rtype": "halfyearly", "district": C.HEAD_OFFICE, "activity": C.CONSOLIDATED,
        "activity_date": None, "period": f"{C.HALVES[0]} FY 2026-27", "fy": 2026, "half": 1,
        "location": "Head Office", "participants": {}, "participants_total": 0,
        "tags": ["Social Security & Welfare Schemes"], "details": {},
        "description": "Half-yearly consolidated report, April–September 2026.",
        "remarks": "", "submitted_by": "Admin User", "status": "Pending",
        "comments": [{"by": "Admin User", "at": "2026-10-20T09:30:00+00:00",
                      "text": "Please add district-wise participant totals."}],
        "attachments": [], "archive_refs": [], "created_at": "2026-10-18T10:00:00+00:00",
    })
    rid += 1
    reports.append({
        "id": rid, "rtype": "annual", "district": C.HEAD_OFFICE, "activity": C.CONSOLIDATED,
        "activity_date": None, "period": "FY 2025-26", "fy": 2025,
        "location": "Head Office", "participants": {}, "participants_total": 0,
        "tags": ["Fishing Rights & Access", "Legal Aid"], "details": {},
        "description": "Annual report for financial year 2025-26.", "remarks": "",
        "submitted_by": "Admin User", "status": "Approved", "comments": [],
        "attachments": [], "archive_refs": [], "created_at": "2026-05-10T10:00:00+00:00",
    })
    return reports
