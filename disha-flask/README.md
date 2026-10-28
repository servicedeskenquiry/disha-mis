# DISHA MIS — Flask + Supabase

Management Information System for the **Society for Direct Initiative for Social and Health Action (DISHA)**.
The Small-Scale Fisheries section ("Fisheries Data Management System") is live. The other four sections show as *Coming Soon*.

This version includes the changes from the client's *Preliminary Review and Observation Note* (28.09.2026) and the remaining modules: Approval Queue, Reports Dashboard (analytics), Export and User Management.

---

## Quick start (local)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # add Supabase URL/key, or leave empty for demo data
flask run
```

Open `http://localhost:5000`. Without Supabase the app runs on in-memory demo data (about 250 reports across the 15 districts, reset on restart).

Demo logins `admin / admin123` (Super Admin) and `staff / staff123` (Back Office) work **only until the first user is created** under *User Management*. Create your own Super Admin first.

---

## Supabase setup

1. **SQL Editor** → run `supabase_schema.sql`. It creates `reports`, `app_users`, the RLS policies (including the UPDATE policy approvals need) and the public `attachments` storage bucket.
   - If you ran the old v1 schema, uncomment the `DROP TABLE IF EXISTS reports;` line at the top first. The old table only held demo data.
2. Optional: run `supabase_seed.sql` for demo reports.
3. **Settings → API → Legacy API Keys** → copy the `anon` key (starts with `eyJ...`). `supabase==2.7.4` rejects the newer `sb_publishable_...` keys.
4. Put `SUPABASE_URL` and `SUPABASE_KEY` in `.env` (local) or the Render environment.
5. Check `https://your-app/health`. It should say `"backend": "supabase"`.

Supabase errors are now shown on screen and logged, instead of silently falling back to demo data.

Security note: the anon key is only used on the server, never sent to the browser. Anyone who has the key can still read the tables (including password hashes), so keep it secret and never commit `.env`.

---

## Deploy on Render

`render.yaml` is unchanged. Add `SUPABASE_URL` and `SUPABASE_KEY` in the Render dashboard. Attachments go to Supabase Storage. Without Supabase they are saved to the local disk, which Render wipes on every deploy.

---

## Where to change lists

Everything the client may revise is in **`config.py`**:

| Setting | What it is |
|---|---|
| `DISTRICTS`, `HEAD_OFFICE` | The 15 active districts/units. Head Office is offered for periodic reports only |
| `REPORT_TYPES` | Daily Activity, Monthly, Quarterly, Half-Yearly, Annual |
| `ACTIVITY_TYPES` | 5 activity types + Others, each with the format/template fields that open when it is chosen. **Provisional** until the Fisheries Team shares their formats |
| `ISSUE_TAGS` | **Provisional** list until the Fisheries Team shares theirs |
| `PARTICIPANT_CATEGORIES` | Women, Men, Fisher, Fish Workers, Fish Farmers, Leaders, Organisers, Experts, Others |
| `QUARTERS`, `HALVES` | Indian financial year (Q1 = Apr–Jun, H1 = Apr–Sep) |
| `MAX_ATTACHMENTS`, `MAX_FILE_MB` | 10 files per report, 25 MB each |
| `LOGO_FILE`, `FAVICON_FILE` | Official DISHA green-leaf logo in `static/img/` |

Bengali text lives in `static/js/i18n_bn.js`, keyed by the English text. Add a line there for any new label.

---

## Project structure

```
app.py               Routes
config.py            Master lists (districts, report types, activities, tags …)
store.py             Supabase / in-memory data access, file storage, users
analytics.py         Filters and dashboard/analytics aggregations
exports.py           Word, Excel, PowerPoint and PDF export
demo_data.py         Demo reports
supabase_schema.sql  Tables, RLS policies, storage bucket
supabase_seed.sql    Optional demo data
static/js/main.js    Language switch, charts (values printed on charts), submit form
static/js/i18n_bn.js Bengali translations
static/js/vendor/    Chart.js 4.4.1 + chartjs-plugin-datalabels 2.2.0 (bundled, no CDN)
templates/
  home.html              Welcome page: org name, logo, 5 sections, language switch
  login.html             Fisheries login
  dashboard.html         Primary dashboard
  submit.html            Submit report (5 types)
  reports.html           All Reports + type sub-sections + Monthly Due/Done tracker
  reports_dashboard.html Submission overview, district-wise progress
  report_detail.html     Report view, admin comments, approval
  approvals.html         Approval Queue
  export.html            Export page
  users.html             User Management
```

## Roles

| Role | Can do |
|---|---|
| Super Admin | Everything, including approving reports and managing users |
| Back Office | Submit, view, comment, analytics, export |
| Guest | Dashboard and a preview of approved reports (unchanged) |

## Known limitations

- PDF export uses standard fonts, so Bengali text typed into reports will not render in the PDF. Word, Excel and PowerPoint exports handle Bengali fine.
- Report period labels (e.g. "September 2026") are stored in English and are not translated on screen.
- "Save Draft" was removed because it did not save anything. It can be added properly later.
