#!/usr/bin/env python3
"""
Database Migration - Add Category table and update structure
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "scrapping.db"

def migrate_add_category():
    """Add Category table and update Source to reference it"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Starting database migration...")
    
    # Create Category table
    print("\n1️⃣ Creating Category table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    
    # Insert categories from .env or defaults
    print("2️⃣ Inserting categories...")
    categories = os.getenv('CATEGORIES', 'Relg,Soft,Kids,Misc,English').split(',')
    for category in categories:
        cursor.execute("INSERT OR IGNORE INTO Category (name) VALUES (?)", (category.strip(),))
    
    # Get existing themes from Source
    cursor.execute("SELECT DISTINCT theme FROM Source")
    existing_themes = [row[0] for row in cursor.fetchall()]
    
    # Add any missing themes as categories
    for theme in existing_themes:
        if theme and theme not in categories:
            cursor.execute("INSERT OR IGNORE INTO Category (name) VALUES (?)", (theme,))
            print(f"  Added existing theme: {theme}")
    
    conn.commit()
    
    # Create new Source table with category_id
    print("3️⃣ Creating new Source table structure...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Source_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            parent_url TEXT NOT NULL,
            author TEXT NOT NULL,
            UNIQUE(category_id, parent_url, author),
            FOREIGN KEY (category_id) REFERENCES Category(id)
        )
    """)
    
    # Migrate data
    print("4️⃣ Migrating Source data...")
    cursor.execute("""
        INSERT INTO Source_new (id, category_id, parent_url, author)
        SELECT 
            s.id,
            c.id,
            s.parent_url,
            s.author
        FROM Source s
        INNER JOIN Category c ON s.theme = c.name
    """)
    
    # Drop old table and rename
    print("5️⃣ Replacing old Source table...")
    cursor.execute("DROP TABLE Source")
    cursor.execute("ALTER TABLE Source_new RENAME TO Source")
    
    # Create indexes
    print("6️⃣ Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_category_id ON Source(category_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_author ON Source(author)")
    
    conn.commit()
    
    # Verify
    print("\n✅ Verifying migration...")
    cursor.execute("SELECT COUNT(*) FROM Category")
    category_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Source")
    source_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Reels")
    reels_count = cursor.fetchone()[0]
    
    print(f"   Category: {category_count} records")
    print(f"   Source: {source_count} records")
    print(f"   Reels: {reels_count} records")
    
    # Show categories
    print("\n📋 Categories in database:")
    cursor.execute("SELECT name FROM Category ORDER BY name")
    for row in cursor.fetchall():
        print(f"   - {row[0]}")
    
    conn.close()
    
    print("\n🎉 Migration completed successfully!")
    print("\nNew structure:")
    print("  - Category: id, name")
    print("  - Source: id, category_id, parent_url, author")
    print("  - Reels: id, url, added_date, processed, source_id, parent_video_id")
    print("  - ParentVideo: id, name, theme, created_date, output_path")

if __name__ == "__main__":
    migrate_add_category()
