-- DISHA MIS Phase 2: roles and approval workflow
-- Run this whole file ONCE in the Supabase SQL Editor, BEFORE uploading the
-- Phase 2 code. The current site keeps working after it runs.
-- Safe to run more than once.

-- Reports ─────────────────────────────────────────────────────────
-- New statuses: Query raised, Rejected, Resubmitted
ALTER TABLE reports DROP CONSTRAINT IF EXISTS reports_status_check;
ALTER TABLE reports ADD CONSTRAINT reports_status_check
    CHECK (status IN ('Pending','Query','Rejected','Resubmitted','Approved'));
ALTER TABLE reports ADD COLUMN IF NOT EXISTS created_by   TEXT;            -- username of the person who entered it
ALTER TABLE reports ADD COLUMN IF NOT EXISTS history      JSONB DEFAULT '[]'::jsonb;  -- who did what, when
ALTER TABLE reports ADD COLUMN IF NOT EXISTS guest_hidden BOOLEAN DEFAULT FALSE;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS updated_at   TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS reports_status_idx     ON reports (status);
CREATE INDEX IF NOT EXISTS reports_created_by_idx ON reports (created_by);

-- Users ───────────────────────────────────────────────────────────
-- Roles: Admin, Approver, Back Office ("Super Admin" is still accepted and
-- treated as Admin). An Approver can cover several districts.
ALTER TABLE app_users DROP CONSTRAINT IF EXISTS app_users_role_check;
ALTER TABLE app_users ADD CONSTRAINT app_users_role_check
    CHECK (role IN ('Admin','Super Admin','Approver','Back Office'));
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS districts TEXT[] DEFAULT '{}';
UPDATE app_users SET districts = ARRAY[district]
    WHERE COALESCE(district, '') <> '' AND COALESCE(cardinality(districts), 0) = 0;

-- Settings (Admin › Settings) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS app_settings (
    key         TEXT PRIMARY KEY,
    value       JSONB,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON app_settings FROM anon, authenticated;

-- Restore function ────────────────────────────────────────────────
-- Replaces all reports, users and settings with the contents of a backup,
-- in one transaction: if anything fails, nothing changes. Backups made
-- before Phase 2 have no settings; the current settings are then kept.
CREATE OR REPLACE FUNCTION disha_restore(payload jsonb) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
    n_reports  integer;
    n_users    integer;
    n_settings integer := 0;
BEGIN
    IF payload->>'app' IS DISTINCT FROM 'disha-mis'
       OR jsonb_typeof(payload->'tables'->'reports')   IS DISTINCT FROM 'array'
       OR jsonb_typeof(payload->'tables'->'app_users') IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'Not a DISHA MIS backup';
    END IF;

    DELETE FROM reports WHERE true;
    INSERT INTO reports
        SELECT * FROM jsonb_populate_recordset(NULL::reports, payload->'tables'->'reports');
    GET DIAGNOSTICS n_reports = ROW_COUNT;

    DELETE FROM app_users WHERE true;
    INSERT INTO app_users
        SELECT * FROM jsonb_populate_recordset(NULL::app_users, payload->'tables'->'app_users');
    GET DIAGNOSTICS n_users = ROW_COUNT;

    IF jsonb_typeof(payload->'tables'->'app_settings') = 'array' THEN
        DELETE FROM app_settings WHERE true;
        INSERT INTO app_settings
            SELECT * FROM jsonb_populate_recordset(NULL::app_settings, payload->'tables'->'app_settings');
        GET DIAGNOSTICS n_settings = ROW_COUNT;
    END IF;

    -- New reports continue numbering after the highest restored id
    PERFORM setval(pg_get_serial_sequence('reports', 'id'),
                   COALESCE((SELECT max(id) FROM reports), 0) + 1, false);

    RETURN jsonb_build_object('reports', n_reports, 'app_users', n_users,
                              'app_settings', n_settings);
END;
$$;
REVOKE ALL ON FUNCTION disha_restore(jsonb) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION disha_restore(jsonb) TO service_role;
