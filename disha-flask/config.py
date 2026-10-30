"""
DISHA MIS – master lists and settings.

Everything the client may want to change without touching the app logic
lives here: districts, report types, activity types and their templates,
participant categories and issue tags.

PLACEHOLDERS: ACTIVITY_TYPES (their template fields) and DEFAULT_ISSUE_TREE are
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

# Approval workflow (revised module, section 5)
#   Pending      submitted, waiting for the Approver
#   Query        Approver asked a question; Back Office must respond
#   Rejected     returned with a reason; Back Office can correct and resubmit
#   Resubmitted  corrected after a query or rejection, waiting again
#   Approved     confirmed and locked (only an Admin can change it)
STATUSES = ["Pending", "Query", "Rejected", "Resubmitted", "Approved"]
STATUS_LABEL = {
    "Pending": "Pending",
    "Query": "Query raised",
    "Rejected": "Rejected",
    "Resubmitted": "Resubmitted",
    "Approved": "Approved",
}
REVIEW_STATUSES = ("Pending", "Resubmitted")    # waiting for the Approver
RETURNED_STATUSES = ("Query", "Rejected")       # waiting for Back Office

# ─────────────────────────────────────────────
# Activity types: the 10 categories of the revised module (section 2), plus
# Others, and the format that opens for each. Field types: text, textarea,
# number, date, select (with "options"). The first five keep their earlier
# names so existing reports stay linked. The formats are a first draft for
# the Fisheries Team to review; activity types can change after go-live.
# ─────────────────────────────────────────────
OTHERS = "Others"
CONSOLIDATED = "Consolidated (all activities)"

ACTIVITY_TYPES = [
    {
        "name": "Community Meeting (incl. Women's & Youth)",
        "short": "Community Meeting",
        "fields": [
            {"key": "meeting_type", "label": "Meeting type", "type": "select",
             "options": ["General community meeting", "Women's meeting", "Youth meeting"]},
            {"key": "agenda",    "label": "Agenda",               "type": "textarea"},
            {"key": "decisions", "label": "Key decisions taken",  "type": "textarea"},
            {"key": "followup",  "label": "Follow-up responsibility", "type": "text"},
        ],
    },
    {
        "name": "Block / District / State Conference",
        "short": "Conference",
        "fields": [
            {"key": "level",       "label": "Conference level", "type": "select",
             "options": ["Block", "District", "State"]},
            {"key": "theme",       "label": "Theme / title",            "type": "text"},
            {"key": "guests",      "label": "Chief guests / speakers",  "type": "text"},
            {"key": "resolutions", "label": "Resolutions adopted",      "type": "textarea"},
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
        "name": "Letter to Authorities (incl. RTI)",
        "short": "Letter / RTI",
        "fields": [
            {"key": "letter_type", "label": "Type", "type": "select",
             "options": ["Letter / memorandum", "RTI application", "RTI appeal"]},
            {"key": "addressed_to", "label": "Addressed to (officer / office)", "type": "text"},
            {"key": "subject",      "label": "Subject",                        "type": "text"},
            {"key": "ref_no",       "label": "Reference / memo number",        "type": "text"},
            {"key": "reply",        "label": "Reply status", "type": "select",
             "options": ["Awaiting reply", "Reply received", "No reply after deadline"]},
            {"key": "reply_note",   "label": "Reply received (summary)",       "type": "textarea"},
        ],
    },
    {
        "name": "Policy Intervention Document",
        "short": "Policy Document",
        "fields": [
            {"key": "title",        "label": "Document title",                 "type": "text"},
            {"key": "submitted_to", "label": "Submitted to",                   "type": "text"},
            {"key": "key_points",   "label": "Key demands / recommendations",  "type": "textarea"},
        ],
    },
    {
        "name": "Research & Investigation (Survey / Field Visit)",
        "short": "Research",
        "fields": [
            {"key": "visit_type", "label": "Type of study / visit", "type": "select",
             "options": ["Survey", "Study", "Landing centre visit", "Fish farming visit",
                         "Fish drying yard visit", "Processing unit visit", "Fish market visit",
                         "Other field visit"]},
            {"key": "area",      "label": "Area covered",         "type": "text"},
            {"key": "sample",    "label": "Households / units surveyed", "type": "number"},
            {"key": "findings",  "label": "Key findings",         "type": "textarea"},
        ],
    },
    {
        "name": "Legal Clinic & Counselling",
        "short": "Legal Clinic",
        "fields": [
            {"key": "lawyer",     "label": "Lawyer / counsellor",          "type": "text"},
            {"key": "cases",      "label": "Number of cases heard",        "type": "number"},
            {"key": "case_types", "label": "Nature of cases",              "type": "textarea"},
            {"key": "referrals",  "label": "Referrals / next steps",       "type": "textarea"},
        ],
    },
    {
        "name": "Exposure Visit",
        "short": "Exposure Visit",
        "fields": [
            {"key": "place",    "label": "Place visited",               "type": "text"},
            {"key": "host",     "label": "Host organisation",           "type": "text"},
            {"key": "learning", "label": "Key learnings",               "type": "textarea"},
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
# Issue › Subject › Sub-subject tags (revised module, section 4).
# The Admin edits this list on the Settings page; this is only the starting
# list. PROVISIONAL until the Fisheries Team shares theirs.
# Format: an issue on its own line, "- " before a subject, "-- " before a
# sub-subject.
# ─────────────────────────────────────────────
DEFAULT_ISSUE_TREE = """\
Fishing Rights & Access
- Net ban / fishing ban period
- Access to water bodies
Fishermen ID / Biometric Card
- New card
- Renewal / correction
Social Security & Welfare Schemes
- Savings-cum-relief
- Old age pension
- Accident insurance
PMMSY
Women Fish Workers
- Market space
- Credit and SHG
Coastal Regulation (CRZ)
Inland Water Bodies & Ponds
- Lease of water bodies
- Pollution
Disaster & Climate
- Cyclone relief
- Compensation
Livelihood & Market
- Fish market infrastructure
- Fair price
Legal Aid
"""

# Top-level issues of the starting list (demo data, first start)
ISSUE_TAGS = [l.strip() for l in DEFAULT_ISSUE_TREE.splitlines()
              if l.strip() and not l.strip().startswith("-")]

# Where the information came from (revised module, section 3)
SOURCE_CHANNELS = ["WhatsApp", "Email", "Word document", "PDF", "Phone call",
                   "Field visit / in person", "Other"]

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
ADMIN = "Admin"
APPROVER = "Approver"
BACK_OFFICE = "Back Office"
ROLES = [ADMIN, APPROVER, BACK_OFFICE]
# Older accounts were created as "Super Admin"
ROLE_ALIASES = {"Super Admin": ADMIN}
ROLE_HELP = {
    ADMIN: "Full control: all reports, approvals, users, settings, backups.",
    APPROVER: "Reviews reports of their districts: approve, raise query, reject.",
    BACK_OFFICE: "Enters and tags reports, answers queries. Sees own entries.",
}

# Defaults for Admin › Settings (stored in the app_settings table)
DEFAULT_SETTINGS = {
    "guest_enabled": True,          # show "Continue as Guest" on the login page
    "guest_districts": [],          # empty = all districts
    "guest_report_types": [],       # empty = all report types
    "guest_can_comment": True,
    "guest_see_attachments": True,
    "backoffice_can_download": True,  # own reports only
    "backoffice_see_all": False,      # read-only view of every report
    "issue_tree": DEFAULT_ISSUE_TREE,
}
