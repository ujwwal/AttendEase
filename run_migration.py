"""
Database migration script for multiple lectures per day support.
Run this script to add the new columns to the existing database.
"""
import sqlite3
import os

# Determine the database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'attendance.db')

print(f"Migrating database: {db_path}")

if not os.path.exists(db_path):
    print("Database file not found. It will be created when the app runs.")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if the columns already exist
    cursor.execute("PRAGMA table_info(attendance)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'lectures_present' in columns and 'lectures_total' in columns:
        print("Migration already completed. Columns exist.")
    else:
        print("Adding new columns...")
        
        # Add the new columns
        if 'lectures_present' not in columns:
            cursor.execute("ALTER TABLE attendance ADD COLUMN lectures_present INTEGER DEFAULT 1")
            print("Added 'lectures_present' column")
        
        if 'lectures_total' not in columns:
            cursor.execute("ALTER TABLE attendance ADD COLUMN lectures_total INTEGER DEFAULT 1")
            print("Added 'lectures_total' column")
        
        # Migrate existing data
        if 'is_present' in columns:
            print("Migrating existing data...")
            cursor.execute("""
                UPDATE attendance 
                SET lectures_present = CASE WHEN is_present = 1 THEN 1 ELSE 0 END
                WHERE lectures_present IS NULL
            """)
            cursor.execute("""
                UPDATE attendance 
                SET lectures_total = 1
                WHERE lectures_total IS NULL
            """)
            print("Data migration complete")
        
        conn.commit()
        print("Migration successful!")
        
except Exception as e:
    print(f"Migration error: {e}")
    conn.rollback()
finally:
    conn.close()
