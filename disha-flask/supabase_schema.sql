-- DISHA MIS v2 schema (client review 28.09.2026)
-- Run this whole file in the Supabase SQL Editor.
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
    status              TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending','Approved')),
    approved_by         TEXT,
    approved_at         TIMESTAMPTZ,
    comments            JSONB DEFAULT '[]'::jsonb,   -- [{"by","at","text"}]
    attachments         JSONB DEFAULT '[]'::jsonb,   -- [{"category":"minutes|supporting","name","type","size","url","path"}]
    archive_refs        JSONB DEFAULT '[]'::jsonb,   -- files re-used from earlier reports
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS reports_district_idx ON reports (district);
CREATE INDEX IF NOT EXISTS reports_rtype_idx    ON reports (rtype);
CREATE INDEX IF NOT EXISTS reports_tags_idx     ON reports USING GIN (tags);

ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow anon read"   ON reports;
DROP POLICY IF EXISTS "Allow anon insert" ON reports;
DROP POLICY IF EXISTS "Allow authenticated insert" ON reports;
DROP POLICY IF EXISTS "Allow anon update" ON reports;
CREATE POLICY "Allow anon read"   ON reports FOR SELECT USING (true);
CREATE POLICY "Allow anon insert" ON reports FOR INSERT WITH CHECK (true);
-- Needed for approvals and comments (without it updates silently do nothing)
CREATE POLICY "Allow anon update" ON reports FOR UPDATE USING (true) WITH CHECK (true);

-- ─────────────────────────────────────────────
-- Users (User Management). Passwords are stored as werkzeug hashes.
-- While this table is empty the demo logins admin/admin123 and staff/staff123
-- work; as soon as one user exists they stop working.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS app_users (
    username       TEXT PRIMARY KEY,
    full_name      TEXT,
    password_hash  TEXT NOT NULL,
    role           TEXT NOT NULL CHECK (role IN ('Super Admin','Back Office')),
    district       TEXT DEFAULT '',
    active         BOOLEAN DEFAULT TRUE,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow anon read users"   ON app_users;
DROP POLICY IF EXISTS "Allow anon insert users" ON app_users;
DROP POLICY IF EXISTS "Allow anon update users" ON app_users;
CREATE POLICY "Allow anon read users"   ON app_users FOR SELECT USING (true);
CREATE POLICY "Allow anon insert users" ON app_users FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anon update users" ON app_users FOR UPDATE USING (true) WITH CHECK (true);

-- ─────────────────────────────────────────────
-- Storage bucket for attachments (photos, videos, PDFs, minutes)
-- ─────────────────────────────────────────────
INSERT INTO storage.buckets (id, name, public)
VALUES ('attachments', 'attachments', true)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS "Allow anon upload attachments" ON storage.objects;
DROP POLICY IF EXISTS "Allow anon read attachments"   ON storage.objects;
CREATE POLICY "Allow anon upload attachments" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'attachments');
CREATE POLICY "Allow anon read attachments" ON storage.objects
    FOR SELECT USING (bucket_id = 'attachments');

-- Optional demo data: run supabase_seed.sql after this file.
