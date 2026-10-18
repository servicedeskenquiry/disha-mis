# DISHA MIS — Flask + Supabase

DISHA Management Information System demo for fisheries NGO.  
**30% complete** — shows working Login, Dashboard, Submit Report, View Reports.  
Remaining 70% (Approval Queue, Analytics, Export, etc.) shown as locked modules.

---

## Quick Start (local)

```bash
# 1. Clone and enter
git clone https://github.com/YOUR_ORG/disha-mis.git
cd disha-mis

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your Supabase URL and key

# 5. Run
flask run
```

Open `http://localhost:5000`

---

## Demo credentials

| Username | Password  | Role        |
|----------|-----------|-------------|
| admin    | admin123  | Super Admin |
| staff    | staff123  | Back Office |

Or click **"Continue as Guest"** for read-only access.

---

## Supabase Setup

1. Go to [supabase.com](https://supabase.com) → New Project
2. Open **SQL Editor** → paste contents of `supabase_schema.sql` → Run
3. Go to **Settings → API** → copy Project URL and anon/public key
4. Paste into your `.env`:
   ```
   SUPABASE_URL=https://xxxx.supabase.co
   SUPABASE_KEY=your-anon-key
   ```

> Without Supabase configured, the app runs with in-memory demo data (data resets on restart).

---

## Deploy on Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml`
5. Add environment variables in Render dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
6. Deploy 🚀

---

## Project Structure

```
disha-mis/
├── app.py                  # Flask routes + Supabase integration
├── requirements.txt
├── render.yaml             # Render deployment config
├── .env.example
├── supabase_schema.sql     # Supabase table + demo data
├── static/
│   ├── css/style.css       # All styles
│   └── js/main.js          # Charts, translations, file upload
└── templates/
    ├── base.html           # Sidebar, topbar, modal layout
    ├── login.html          # Login screen
    ├── dashboard.html      # Charts + stats
    ├── submit.html         # 3-step report submission
    ├── reports.html        # Report list with filters
    └── report_detail.html  # Single report view
```

---

## Features

### Working (30%)
- ✅ Login (Admin / Back Office / Guest modes)
- ✅ Dashboard with 4 live charts (Chart.js)
- ✅ Submit Report (Daily / Quarter / Annual) with file attachment
- ✅ View Reports with type/status filters
- ✅ Guest mode — blurred report list, locked submission
- ✅ English ↔ বাংলা language toggle (persists in localStorage)
- ✅ "30% Complete" progress banner
- ✅ Supabase database integration (optional)

### Coming Soon (70% — shown as locked)
- 🔒 Approval Queue (Approve / Query / Reject)
- 🔒 Analytics & detailed charts
- 🔒 Export (Excel / PDF / Word)
- 🔒 Issue Tags
- 🔒 Case Studies
- 🔒 Govt. Schemes
- 🔒 User Profiles & role management
