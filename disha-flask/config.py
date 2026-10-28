"""
DISHA MIS – master lists and settings.

Everything the client may want to change without touching the app logic
lives here: districts, report types, activity types and their templates,
participant categories and issue tags.

PLACEHOLDERS: ACTIVITY_TYPES (and their template fields) and ISSUE_TAGS are
provisional. The Fisheries Team will share their existing formats and the
proposed issue-tag list; replace the lists below when those arrive.
"""

ORG_NAME = "Society for Direct Initiative for Social and Health Action (DISHA)"
ORG_SHORT = "DISHA"
SYSTEM_NAME = "Fisheries Data Management System"
# Official DISHA logo (green leaf). Favicon is a small copy of the same logo.
LOGO_FILE = "img/disha-logo.png"
FAVICON_FILE = "img/favicon.png"

# ─────────────────────────────────────────────
# Welcome page sections (only Fisheries is active for now)
# ─────────────────────────────────────────────
SECTIONS = [
    {"key": "fisheries",   "name": "Small-Scale Fisheries",   "icon": "🐟", "active": True},
    {"key": "waste",       "name": "Waste Management",        "icon": "♻️", "active": False},
    {"key": "child",       "name": "Child Development",       "icon": "🧒", "active": False},
    {"key": "forest",      "name": "Forest Dwellers",         "icon": "🌳", "active": False},
    {"key": "agriculture", "name": "Sustainable Agriculture", "icon": "🌾", "active": False},
]

# ─────────────────────────────────────────────
# Active districts / units (client list, 15 units)
# ─────────────────────────────────────────────
DISTRICTS = [
    "South 24 Parganas",
    "North 24 Parganas",
    "Howrah",
    "Hooghly",
    "Nadia",
    "Purba Medinipur",
    "Purba Medinipur – Vendor",
    "Paschim Medinipur",
    "Jhargram",
    "Murshidabad",
    "Malda",
    "Dakshin Dinajpur",
    "Jalpaiguri",
    "Cooch Behar",
    "Alipurduar",
]
HEAD_OFFICE = "Head Office"
# Periodic reports may also be filed by Head Office
PERIODIC_DISTRICTS = DISTRICTS + [HEAD_OFFICE]

# ─────────────────────────────────────────────
# Report types (same names used everywhere in the system)
# ─────────────────────────────────────────────
REPORT_TYPES = [
    {"key": "daily",      "label": "Daily Activity Report", "short": "Daily",       "icon": "📋"},
    {"key": "monthly",    "label": "Monthly Report",        "short": "Monthly",     "icon": "🗓️"},
    {"key": "quarterly",  "label": "Quarterly Report",      "short": "Quarterly",   "icon": "📊"},
    {"key": "halfyearly", "label": "Half-Yearly Report",    "short": "Half-Yearly", "icon": "📑"},
    {"key": "annual",     "label": "Annual Report",         "short": "Annual",      "icon": "📈"},
]
REPORT_TYPE_KEYS = [t["key"] for t in REPORT_TYPES]
REPORT_TYPE_LABEL = {t["key"]: t["label"] for t in REPORT_TYPES}
REPORT_TYPE_SHORT = {t["key"]: t["short"] for t in REPORT_TYPES}
PERIODIC_TYPES = ["monthly", "quarterly", "halfyearly", "annual"]

STATUSES = ["Pending", "Approved"]

# ─────────────────────────────────────────────
# Activity types (5 + Others) and the template that opens for each.
# Field types: text, textarea, number. PROVISIONAL – to be replaced with the
# Fisheries Team's formats.
# ─────────────────────────────────────────────
OTHERS = "Others"
CONSOLIDATED = "Consolidated (all activities)"

ACTIVITY_TYPES = [
    {
        "name": "Community Meeting (incl. Women's & Youth)",
        "short": "Community Meeting",
        "fields": [
            {"key": "agenda",    "label": "Agenda",               "type": "textarea"},
            {"key": "decisions", "label": "Key decisions taken",  "type": "textarea"},
            {"key": "followup",  "label": "Follow-up responsibility", "type": "text"},
        ],
    },
    {
        "name": "Training Programme",
        "short": "Training",
        "fields": [
            {"key": "topic",     "label": "Training topic",       "type": "text"},
            {"key": "days",      "label": "Duration (days)",      "type": "number"},
            {"key": "resource",  "label": "Resource person(s)",   "type": "text"},
        ],
    },
    {
        "name": "Campaign & Awareness",
        "short": "Campaign",
        "fields": [
            {"key": "theme",     "label": "Campaign theme",       "type": "text"},
            {"key": "mode",      "label": "Mode (rally, street play, leaflets…)", "type": "text"},
            {"key": "reach",     "label": "People reached (approx.)", "type": "number"},
        ],
    },
    {
        "name": "Deputation & Meeting with Govt. Officials",
        "short": "Deputation",
        "fields": [
            {"key": "officials", "label": "Officials / office met", "type": "text"},
            {"key": "demands",   "label": "Demands / issues raised", "type": "textarea"},
            {"key": "response",  "label": "Response / commitment received", "type": "textarea"},
        ],
    },
    {
        "name": "Research & Investigation (Survey / Field Visit)",
        "short": "Research",
        "fields": [
            {"key": "area",      "label": "Area covered",         "type": "text"},
            {"key": "sample",    "label": "Households / units surveyed", "type": "number"},
            {"key": "findings",  "label": "Key findings",         "type": "textarea"},
        ],
    },
    {
        "name": OTHERS,
        "short": "Others",
        "fields": [
            {"key": "specify",   "label": "Specify activity",     "type": "text"},
        ],
    },
]
ACTIVITY_NAMES = [a["name"] for a in ACTIVITY_TYPES]
ACTIVITY_SHORT = {a["name"]: a["short"] for a in ACTIVITY_TYPES}
ACTIVITY_SHORT[CONSOLIDATED] = "Consolidated"
ACTIVITY_FIELDS = {a["name"]: a["fields"] for a in ACTIVITY_TYPES}
ACTIVITY_FIELDS[CONSOLIDATED] = [
    {"key": "highlights", "label": "Highlights of the period", "type": "textarea"},
    {"key": "challenges", "label": "Challenges",               "type": "textarea"},
    {"key": "plan",       "label": "Plan for next period",     "type": "textarea"},
]

# ─────────────────────────────────────────────
# Participant sub-categories (user ticks the ones that apply)
# ─────────────────────────────────────────────
PARTICIPANT_CATEGORIES = [
    {"key": "women",        "label": "Women"},
    {"key": "men",          "label": "Men"},
    {"key": "fisher",       "label": "Fisher"},
    {"key": "fish_workers", "label": "Fish Workers"},
    {"key": "fish_farmers", "label": "Fish Farmers"},
    {"key": "leaders",      "label": "Leaders"},
    {"key": "organisers",   "label": "Organisers"},
    {"key": "experts",      "label": "Experts"},
    {"key": "others",       "label": "Others"},
]
PARTICIPANT_LABEL = {c["key"]: c["label"] for c in PARTICIPANT_CATEGORIES}

# ─────────────────────────────────────────────
# Issue tags – PROVISIONAL list until the Fisheries Team shares theirs
# ─────────────────────────────────────────────
ISSUE_TAGS = [
    "Fishing Rights & Access",
    "Fishermen ID / Biometric Card",
    "Social Security & Welfare Schemes",
    "PMMSY",
    "Women Fish Workers",
    "Coastal Regulation (CRZ)",
    "Inland Water Bodies & Ponds",
    "Disaster & Climate",
    "Livelihood & Market",
    "Legal Aid",
]

# ─────────────────────────────────────────────
# Periods. Quarters and halves follow the Indian financial year
# (April–March): Q1 = Apr–Jun, H1 = Apr–Sep.
# ─────────────────────────────────────────────
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MONTHS_SHORT = [m[:3] for m in MONTHS]
FY_MONTHS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]   # financial-year order
QUARTERS = ["1st Quarter (Apr–Jun)", "2nd Quarter (Jul–Sep)",
            "3rd Quarter (Oct–Dec)", "4th Quarter (Jan–Mar)"]
HALVES = ["1st Half (Apr–Sep)", "2nd Half (Oct–Mar)"]

# ─────────────────────────────────────────────
# Attachments
# ─────────────────────────────────────────────
ATTACHMENT_CATEGORIES = [
    {"key": "minutes",    "label": "A. Meeting Resolution / Meeting Minutes"},
    {"key": "supporting", "label": "B. Supporting Documents / Media"},
]
MAX_ATTACHMENTS = 10
MAX_FILE_MB = 25
ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "webp", "heic",
    "mp4", "mov", "avi", "mkv", "3gp", "webm",
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv",
}

# ─────────────────────────────────────────────
# Roles
# ─────────────────────────────────────────────
ROLES = ["Super Admin", "Back Office"]
# Roles that can approve reports and comment as reviewer
APPROVER_ROLES = {"Super Admin"}
# Roles that can manage users
USER_ADMIN_ROLES = {"Super Admin"}
