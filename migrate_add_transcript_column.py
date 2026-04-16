#!/usr/bin/env python3
"""
Database Migration - Add transcript column to Category table
"""

import sqlite3
import os

DB_PATH = "scrapping.db"

def migrate_add_transcript():
    """Add transcript column to Category table"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Adding transcript column to Category table...")
    
    # Add transcript column (0 = no, 1 = yes)
    cursor.execute("""
        ALTER TABLE Category ADD COLUMN transcript INTEGER DEFAULT 0
    """)
    
    conn.commit()
    
    # Show current categories
    print("\n✅ Migration completed!")
    print("\n📋 Categories with transcript status:")
    cursor.execute("SELECT id, name, transcript FROM Category ORDER BY name")
    for row in cursor.fetchall():
        transcript_status = "Yes" if row[2] == 1 else "No"
        print(f"   {row[1]}: transcript = {transcript_status}")
    
    conn.close()
    
    print("\nYou can update transcript values with:")
    print("  UPDATE Category SET transcript=1 WHERE name='CategoryName';")

if __name__ == "__main__":
    migrate_add_transcript()
