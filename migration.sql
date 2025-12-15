-- AttendEase Database Migration Script
-- Run this on your production PostgreSQL database (Neon) before deploying
-- This adds the new columns required for the password reset feature

-- Add 'name' column with default value for existing users
ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(100) DEFAULT 'User' NOT NULL;

-- Add 'reset_token' column for password reset codes
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(6);

-- Add 'reset_token_expires' column for token expiration
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;

-- Optional: Update existing users' names from their username (ERP number)
-- Uncomment the line below if you want to set name = username for existing users
-- UPDATE users SET name = username WHERE name = 'User';

-- Verify the migration was successful
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'users';
