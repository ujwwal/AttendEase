-- Migration: Add multiple lectures per day support
-- This script converts the existing is_present boolean to lectures_present/lectures_total

-- Step 1: Add the new columns
ALTER TABLE attendance ADD COLUMN lectures_present INTEGER DEFAULT 1;
ALTER TABLE attendance ADD COLUMN lectures_total INTEGER DEFAULT 1;

-- Step 2: Migrate existing data
-- is_present = 1 (True) -> lectures_present = 1, lectures_total = 1
-- is_present = 0 (False) -> lectures_present = 0, lectures_total = 1
UPDATE attendance SET lectures_present = CASE WHEN is_present = 1 THEN 1 ELSE 0 END;
UPDATE attendance SET lectures_total = 1;

-- Step 3: Drop the old column (optional - keep for rollback if needed)
-- ALTER TABLE attendance DROP COLUMN is_present;

-- Note: SQLite does not support DROP COLUMN directly in older versions.
-- For SQLite, you may need to recreate the table if you want to remove the column.
