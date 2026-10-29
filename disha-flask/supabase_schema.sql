-- DISHA MIS v2 schema (client review 28.09.2026)
-- Run this whole file in the Supabase SQL Editor, then supabase_lockdown.sql.
--
-- If you ran the OLD schema earlier, the old "reports" table only holds demo
-- data and has different columns. Drop it first by uncommenting the next line:
-- DROP TABLE IF EXISTS reports;

-- ─────────────────────────────────────────────
-- Reports
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reports (
    id                  BIGSERIAL PRIMARY KEY,
    rtype               TEXT NOT NULL CHECK (rtype IN ('daily','monthly','quarterly','halfyearly','annual')),
    district            TEXT NOT NULL,           -- 15 active districts, or 'Head Office' for periodic reports
    activity            TEXT NOT NULL,
    activity_date       DATE,                    -- Daily Activity Report only
    period              TEXT NOT NULL,           -- display label, e.g. 'September 2026', '1st Quarter (Apr–Jun) FY 2026-27'
    fy                  INTEGER,                 -- financial year start (2026 = FY 2026-27)
    month               INTEGER CHECK (month BETWEEN 1 AND 12),
    quarter             INTEGER CHECK (quarter BETWEEN 1 AND 4),
    half                INTEGER CHECK (half IN (1, 2)),
    location            TEXT,
    participants        JSONB DEFAULT '{}'::jsonb,   -- {"total": 32, "women": 12, "men": 20, ...}
    participants_total  INTEGER DEFAULT 0,
    tags                TEXT[] DEFAULT '{}',         -- issue tags
    details             JSONB DEFAULT '{}'::jsonb,   -- activity-template fields
    description         TEXT,
    remarks             TEXT,
    submitted_by        TEXT,
    status              TEXT NOT NULL DEFAULT 'Pending'
                        CHECK (status IN ('Pending','Query','Rejected','Resubmitted','Approved')),
    approved_by         TEXT,
    approved_at         TIMESTAMPTZ,
    comments            JSONB DEFAULT '[]'::jsonb,   -- [{"by","at","text"}]
    attachments         JSONB DEFAULT '[]'::jsonb,   -- [{"category":"minutes|supporting","name","type","size","url","path"}]
    archive_refs        JSONB DEFAULT '[]'::jsonb,   -- files re-used from earlier reports
    created_by          TEXT,                        -- username of the person who entered it
    history             JSONB DEFAULT '[]'::jsonb,   -- [{"at","by","role","action","note","changes"}]
    guest_hidden        BOOLEAN DEFAULT FALSE,
    updated_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS reports_district_idx ON reports (district);
CREATE INDEX IF NOT EXISTS reports_rtype_idx    ON reports (rtype);
CREATE INDEX IF NOT EXISTS reports_tags_idx     ON reports USING GIN (tags);
CREATE INDEX IF NOT EXISTS reports_status_idx   ON reports (status);
CREATE INDEX IF NOT EXISTS reports_created_by_idx ON reports (created_by);

-- Row Level Security is on with no policies: only the server's
-- service_role key (SUPABASE_SERVICE_KEY) can read or write.
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────
-- Users (User Management). Passwords are stored as werkzeug hashes.
-- While this table is empty the demo logins (admin/admin123, approver/approver123,
-- staff/staff123)
-- work; as soon as one user exists they stop working.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS app_users (
    username       TEXT PRIMARY KEY,
    full_name      TEXT,
    password_hash  TEXT NOT NULL,
    role           TEXT NOT NULL CHECK (role IN ('Admin','Super Admin','Approver','Back Office')),
    district       TEXT DEFAULT '',                 -- first of districts (older code)
    districts      TEXT[] DEFAULT '{}',             -- Approver: districts they review; empty = all
    active         BOOLEAN DEFAULT TRUE,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────
-- Settings (Admin › Settings), one row per setting
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS app_settings (
    key         TEXT PRIMARY KEY,
    value       JSONB,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;

-- Attachments and backups are stored in Backblaze B2 (see b2.py), not in
-- Supabase Storage.

-- Lock-down and the restore function used by Backup & Restore:
-- run supabase_lockdown.sql after this file.
-- Optional demo data: run supabase_seed.sql after this file.
