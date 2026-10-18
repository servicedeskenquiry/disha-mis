-- Run this in your Supabase SQL Editor to create the reports table

CREATE TABLE IF NOT EXISTS reports (
    id            SERIAL PRIMARY KEY,
    office        TEXT NOT NULL,
    activity      TEXT NOT NULL,
    rtype         TEXT NOT NULL CHECK (rtype IN ('daily', 'quarter', 'annual')),
    period        TEXT NOT NULL,
    location      TEXT,
    participants  INTEGER DEFAULT 0,
    by            TEXT,
    status        TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Queried')),
    "desc"        TEXT,
    remarks       TEXT,
    attachments   JSONB DEFAULT '[]'::jsonb,
    date          TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Allow anon reads (public demo)
CREATE POLICY "Allow anon read" ON reports
    FOR SELECT USING (true);

-- Allow authenticated inserts
CREATE POLICY "Allow authenticated insert" ON reports
    FOR INSERT WITH CHECK (true);

-- Insert demo data
INSERT INTO reports (id, office, activity, rtype, period, participants, by, date, status, "desc", attachments) VALUES
(47, 'Kolkata North',   'Community Meeting (incl. Women''s & Youth)', 'daily',   '21 Sep 2026', 62,  'Raju Das',    '20 Sep', 'Pending',  'Community meeting at Palta Ghat with 62 members including women''s and youth groups.', '[]'),
(46, 'Diamond Harbour', 'Training Programme',                         'daily',   '19 Sep 2026', 45,  'Mita Mondal', '19 Sep', 'Approved', 'Three-day training on sustainable fishing practices. 45 fishermen attended. Certificates issued.', '[]'),
(45, 'Basirhat',        'Legal Clinic & Counselling',                 'quarter', 'Q3 2026',     18,  'Suresh Biswas','18 Sep','Queried',  'Quarterly legal clinic for 18 fishermen. Query raised regarding supporting affidavits.', '[]'),
(44, 'Kakdwip',         'Campaign & Awareness',                       'daily',   '15 Sep 2026', 120, 'Priya Roy',   '15 Sep', 'Approved', 'Mass awareness campaign. 120 individuals reached through pamphlets and street play.', '[]'),
(43, 'Canning',         'Exposure Visit',                             'annual',  'Annual 2026', 22,  'Arun Ghosh',  '14 Sep', 'Approved', 'Annual exposure visit to fishing cooperative in Odisha. 22 members participated.', '[]'),
(42, 'Sagar Island',    'Deputation & Meeting with Govt. Officials',  'daily',   '10 Sep 2026', 8,   'Mita Mondal', '10 Sep', 'Approved', 'Deputation to BDO regarding fishermen ID card delay.', '[]'),
(41, 'Kolkata North',   'Research & Investigation',                   'quarter', 'Q3 2026',     0,   'Raju Das',    '5 Sep',  'Pending',  'Field survey of 38 ponds. Water quality, ownership and productivity being documented.', '[]');

-- Reset the sequence after manual inserts
SELECT setval('reports_id_seq', (SELECT MAX(id) FROM reports));
