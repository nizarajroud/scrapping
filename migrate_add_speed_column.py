#!/usr/bin/env python3
"""
Database Migration - Add speed column to Category table
"""

import sqlite3
import os

DB_PATH = "scrapping.db"

def migrate_add_speed():
    """Add speed column to Category table"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Adding speed column to Category table...")
    
    # Add speed column (default 1.0)
    cursor.execute("""
        ALTER TABLE Category ADD COLUMN speed REAL DEFAULT 1.0
    """)
    
    conn.commit()
    
    # Show current categories
    print("\n✅ Migration completed!")
    print("\n📋 Categories with speed:")
    cursor.execute("SELECT id, name, transcript, speed FROM Category ORDER BY name")
    for row in cursor.fetchall():
        transcript_status = "Yes" if row[2] == 1 else "No"
        print(f"   {row[1]}: transcript={transcript_status}, speed={row[3]}")
    
    conn.close()
    
    print("\nYou can update speed values with:")
    print("  UPDATE Category SET speed=1.2 WHERE name='CategoryName';")

if __name__ == "__main__":
    migrate_add_speed()
