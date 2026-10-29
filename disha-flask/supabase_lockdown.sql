-- DISHA MIS Phase 1: lock down the database
-- Run this whole file ONCE in the Supabase SQL Editor, but only AFTER
-- SUPABASE_SERVICE_KEY has been added in Render and the site works again.
--
-- What it does:
--   1. Removes the open "anon" rules, so the public key can no longer read
--      or change reports, user accounts or files. The app keeps working
--      because it now uses the private service_role key, which is allowed
--      past these rules.
--   2. Adds the disha_restore() function used by Admin › Backup & Restore.
-- Safe to run more than once.

-- 1. Close the open rules ─────────────────────────────────────────
ALTER TABLE reports   ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow anon read"            ON reports;
DROP POLICY IF EXISTS "Allow anon insert"          ON reports;
DROP POLICY IF EXISTS "Allow anon update"          ON reports;
DROP POLICY IF EXISTS "Allow authenticated insert" ON reports;
DROP POLICY IF EXISTS "Allow anon read users"      ON app_users;
DROP POLICY IF EXISTS "Allow anon insert users"    ON app_users;
DROP POLICY IF EXISTS "Allow anon update users"    ON app_users;
DROP POLICY IF EXISTS "Allow anon upload attachments" ON storage.objects;
DROP POLICY IF EXISTS "Allow anon read attachments"   ON storage.objects;

REVOKE ALL ON reports, app_users FROM anon, authenticated;
REVOKE ALL ON SEQUENCE reports_id_seq FROM anon, authenticated;
REVOKE ALL ON app_settings FROM anon, authenticated;

-- 2. Restore function ──────────────────────────────────────────────
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
