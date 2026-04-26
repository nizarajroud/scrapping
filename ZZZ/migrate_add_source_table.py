#!/usr/bin/env python3
"""
Database Migration - Add Source table for theme/author/parent_url
"""

import sqlite3
import os

DB_PATH = "scrapping.db"

def migrate_add_source():
    """Add Source table and update Reels structure"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Starting database migration...")
    
    # Create Source table
    print("\n1️⃣ Creating Source table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Source (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme TEXT NOT NULL,
            parent_url TEXT NOT NULL,
            author TEXT NOT NULL,
            UNIQUE(theme, parent_url, author)
        )
    """)
    
    # Extract unique combinations from Reels
    print("2️⃣ Extracting sources from Reels...")
    cursor.execute("""
        SELECT DISTINCT theme, parent_url, author 
        FROM Reels 
        WHERE theme IS NOT NULL AND parent_url IS NOT NULL AND author IS NOT NULL
    """)
    sources = cursor.fetchall()
    
    # Insert into Source table
    print(f"3️⃣ Inserting {len(sources)} sources...")
    for theme, parent_url, author in sources:
        cursor.execute("""
            INSERT OR IGNORE INTO Source (theme, parent_url, author)
            VALUES (?, ?, ?)
        """, (theme, parent_url, author))
    
    # Create new Reels table
    print("4️⃣ Creating new Reels table structure...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reels_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            added_date TEXT NOT NULL,
            processed INTEGER DEFAULT 0,
            source_id INTEGER NOT NULL,
            parent_video_id INTEGER,
            FOREIGN KEY (source_id) REFERENCES Source(id),
            FOREIGN KEY (parent_video_id) REFERENCES ParentVideo(id)
        )
    """)
    
    # Migrate data
    print("5️⃣ Migrating Reels data...")
    cursor.execute("""
        INSERT INTO Reels_new (id, url, added_date, processed, source_id, parent_video_id)
        SELECT 
            r.id,
            r.url,
            r.added_date,
            r.processed,
            s.id,
            r.parent_video_id
        FROM Reels r
        INNER JOIN Source s ON r.theme = s.theme 
            AND r.parent_url = s.parent_url 
            AND r.author = s.author
    """)
    
    # Drop old table and rename
    print("6️⃣ Replacing old Reels table...")
    cursor.execute("DROP TABLE Reels")
    cursor.execute("ALTER TABLE Reels_new RENAME TO Reels")
    
    # Create indexes
    print("7️⃣ Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reels_source_id ON Reels(source_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reels_processed ON Reels(processed)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reels_parent_video_id ON Reels(parent_video_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_theme ON Source(theme)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_author ON Source(author)")
    
    conn.commit()
    
    # Verify
    print("\n✅ Verifying migration...")
    cursor.execute("SELECT COUNT(*) FROM Source")
    source_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Reels")
    reels_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ParentVideo")
    parent_count = cursor.fetchone()[0]
    
    print(f"   Source: {source_count} records")
    print(f"   Reels: {reels_count} records")
    print(f"   ParentVideo: {parent_count} records")
    
    conn.close()
    
    print("\n🎉 Migration completed successfully!")
    print("\nNew structure:")
    print("  - Source: id, theme, parent_url, author")
    print("  - Reels: id, url, added_date, processed, source_id, parent_video_id")
    print("  - ParentVideo: id, name, theme, created_date, output_path")

if __name__ == "__main__":
    migrate_add_source()
