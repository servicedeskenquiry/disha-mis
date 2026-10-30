-- DISHA MIS Phase 3: data entry (Block / GP / Village, source, 3-level tags)
-- Run this whole file ONCE in the Supabase SQL Editor, BEFORE uploading the
-- Phase 3 code. The current site keeps working after it runs.
-- Safe to run more than once.

ALTER TABLE reports ADD COLUMN IF NOT EXISTS block          TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS gp             TEXT;   -- Gram Panchayat
ALTER TABLE reports ADD COLUMN IF NOT EXISTS village        TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS source_channel TEXT;   -- WhatsApp, Email, Word document, PDF, ...
ALTER TABLE reports ADD COLUMN IF NOT EXISTS tag_paths      TEXT[] DEFAULT '{}';  -- 'Issue › Subject › Sub-subject'

-- Older reports: their issue tags become their tag paths
UPDATE reports SET tag_paths = tags
 WHERE (tag_paths IS NULL OR tag_paths = '{}') AND tags IS NOT NULL AND tags <> '{}';

CREATE INDEX IF NOT EXISTS reports_tag_paths_idx ON reports USING GIN (tag_paths);
CREATE INDEX IF NOT EXISTS reports_block_idx     ON reports (district, block);
-- Speeds up the duplicate check
CREATE INDEX IF NOT EXISTS reports_dup_idx       ON reports (rtype, district, activity, period);
