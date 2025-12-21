-- Migration for Production Database
-- Run these commands in order to upgrade your database

-- 1. Add the new columns for tracking multiple lectures
ALTER TABLE attendance ADD COLUMN lectures_present INTEGER DEFAULT 1;
ALTER TABLE attendance ADD COLUMN lectures_total INTEGER DEFAULT 1;

-- 2. Migrate existing data from the old 'is_present' column
-- This keeps your history intact. We assume 1 lecture total for past records.

-- Update lectures_present: 
-- If is_present was TRUE (t), they attended 1 lecture.
-- If is_present was FALSE (f), they attended 0 lectures.
UPDATE attendance 
SET lectures_present = CASE 
    WHEN is_present = TRUE THEN 1 
    WHEN is_present = 't' THEN 1  -- Handle text representation if any
    WHEN is_present = 1 THEN 1    -- Handle integer representation
    ELSE 0 
END;

-- Update lectures_total:
-- All past records were single lectures, so set total to 1.
UPDATE attendance SET lectures_total = 1;

-- 3. Verify the migration (Optional)
-- SELECT * FROM attendance ORDER BY id DESC LIMIT 5;
