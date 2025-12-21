-- Clean up users and their related data
-- Deleting users with IDs: 1, 10, 13, 16

-- 1. First delete their attendance records (to satisfy Foreign Key constraints)
DELETE FROM attendance WHERE user_id IN (1, 10, 13, 16);

-- 2. Then delete the users themselves
DELETE FROM users WHERE id IN (1, 10, 13, 16);

-- 3. Verify deletion
-- SELECT id, username, name FROM users WHERE id IN (1, 10, 13, 16);
