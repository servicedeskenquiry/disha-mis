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

1. **SQL Editor** → run `supabase_schema.sql`, then `supabase_lockdown.sql`. They create `reports`, `app_users`, Row Level Security with no open policies, and the `disha_restore()` function used by Backup & Restore.
   - If you ran the old v1 schema, uncomment the `DROP TABLE IF EXISTS reports;` line at the top first. The old table only held demo data.
2. Optional: run `supabase_seed.sql` for demo reports.
3. **Settings → API Keys → Legacy API Keys** → copy the `service_role` key (starts with `eyJ...`). `supabase==2.7.4` rejects the newer `sb_secret_...` keys.
4. Put `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env` (local) or the Render environment.
5. Check `https://your-app/health`. It should say `"backend": "supabase"`.

Supabase errors are now shown on screen and logged, instead of silently falling back to demo data.

Security note: the service_role key can read and change everything. It is only used on the server, never sent to the browser. Keep it secret and never commit `.env`. The old anon-key setup (`SUPABASE_KEY`) still works until `supabase_lockdown.sql` is run; while it is in use, Super Admins see a warning banner.

---

## Backblaze B2 (attachments and backups)

Set `B2_KEY_ID`, `B2_APP_KEY`, `B2_BUCKET` and `B2_ENDPOINT` (the bucket's S3 endpoint). The bucket should be **private**. Attachments are stored under `attachments/` and opened through `/files/...`, which redirects logged-in users to a link that expires after 10 minutes. Without B2, files go to Supabase Storage.

Files uploaded before B2 was set up can be copied over from **Admin › Backup & Restore › Copy files to Backblaze B2**. When all are copied, the Supabase bucket is made private.

## Backups

**Admin › Backup & Restore** (Super Admin only):
- Save a backup to B2 now, or download one to the computer (`disha-backup-….json.gz`: every row of `reports` and `app_users`).
- Restore from a saved backup or an uploaded file. A safety backup is saved first, and the restore runs in one transaction.

Nightly backups: `.github/workflows/nightly-backup.yml` (in the repository root, not in `disha-flask/`) calls `POST /cron/nightly` at 02:00 IST with the `X-Cron-Secret` header. Set `CRON_SECRET` in Render and the GitHub secrets `APP_URL` and `CRON_SECRET`. Backups older than 30 days are deleted (the newest 7 are always kept). The nightly read also keeps the free Supabase project from pausing.

---

## Deploy on Render

Add the variables from `.env.example` in the Render dashboard (Environment). Attachments go to Backblaze B2, or to Supabase Storage when B2 is not set. Without either they are saved to the local disk, which Render wipes on every deploy.

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
store.py             Supabase / in-memory data access, file storage, users, backup data
b2.py                Backblaze B2 storage (S3-compatible API)
backup.py            Backup files: build, save to B2, list, prune, restore
analytics.py         Filters and dashboard/analytics aggregations
exports.py           Word, Excel, PowerPoint and PDF export
demo_data.py         Demo reports
supabase_schema.sql  Tables and RLS
supabase_lockdown.sql Removes open policies, adds disha_restore()
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
