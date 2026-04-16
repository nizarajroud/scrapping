#!/usr/bin/env python3
"""
Database Migration - Add repetitions column to Category table
"""

import sqlite3
import os

DB_PATH = "scrapping.db"

def migrate_add_repetitions():
    """Add repetitions column to Category table"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Adding repetitions column to Category table...")
    
    # Add repetitions column (default 1)
    cursor.execute("""
        ALTER TABLE Category ADD COLUMN repetitions INTEGER DEFAULT 1
    """)
    
    conn.commit()
    
    # Set English to 5 repetitions
    cursor.execute("UPDATE Category SET repetitions=5 WHERE name='English'")
    conn.commit()
    
    # Show current categories
    print("\n✅ Migration completed!")
    print("\n📋 Categories with all settings:")
    cursor.execute("SELECT name, transcript, speed, repetitions FROM Category ORDER BY name")
    for row in cursor.fetchall():
        transcript_status = "Yes" if row[1] == 1 else "No"
        print(f"   {row[0]}: transcript={transcript_status}, speed={row[2]}, repetitions={row[3]}")
    
    conn.close()

if __name__ == "__main__":
    migrate_add_repetitions()
