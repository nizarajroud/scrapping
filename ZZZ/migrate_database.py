#!/usr/bin/env python3
"""
Database Migration - Split Reels table into ParentVideo and Reels
"""

import sqlite3
import os

DB_PATH = "scrapping.db"

def migrate_database():
    """Migrate database structure"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Starting database migration...")
    
    # Create ParentVideo table
    print("\n1️⃣ Creating ParentVideo table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ParentVideo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            theme TEXT NOT NULL,
            created_date TEXT NOT NULL,
            output_path TEXT
        )
    """)
    
    # Get existing parent videos from Reels table
    print("2️⃣ Extracting parent videos from Reels...")
    cursor.execute("""
        SELECT DISTINCT parent_video, theme 
        FROM Reels 
        WHERE parent_video IS NOT NULL AND parent_video != ''
    """)
    parent_videos = cursor.fetchall()
    
    # Insert into ParentVideo table
    print(f"3️⃣ Inserting {len(parent_videos)} parent videos...")
    for parent_name, theme in parent_videos:
        cursor.execute("""
            INSERT OR IGNORE INTO ParentVideo (name, theme, created_date)
            VALUES (?, ?, datetime('now'))
        """, (parent_name, theme))
    
    # Create new Reels table with foreign key
    print("4️⃣ Creating new Reels table structure...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reels_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_url TEXT,
            url TEXT NOT NULL UNIQUE,
            added_date TEXT NOT NULL,
            processed INTEGER DEFAULT 0,
            theme TEXT,
            author TEXT,
            parent_video_id INTEGER,
            FOREIGN KEY (parent_video_id) REFERENCES ParentVideo(id)
        )
    """)
    
    # Migrate data to new Reels table
    print("5️⃣ Migrating Reels data...")
    cursor.execute("""
        INSERT INTO Reels_new (id, parent_url, url, added_date, processed, theme, author, parent_video_id)
        SELECT 
            r.id,
            r.parent_url,
            r.url,
            r.added_date,
            r.processed,
            r.theme,
            r.author,
            pv.id
        FROM Reels r
        LEFT JOIN ParentVideo pv ON r.parent_video = pv.name
    """)
    
    # Drop old table and rename new one
    print("6️⃣ Replacing old Reels table...")
    cursor.execute("DROP TABLE Reels")
    cursor.execute("ALTER TABLE Reels_new RENAME TO Reels")
    
    # Create indexes for performance
    print("7️⃣ Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reels_theme ON Reels(theme)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reels_author ON Reels(author)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reels_processed ON Reels(processed)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reels_parent_video_id ON Reels(parent_video_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parent_video_theme ON ParentVideo(theme)")
    
    conn.commit()
    
    # Verify migration
    print("\n✅ Verifying migration...")
    cursor.execute("SELECT COUNT(*) FROM ParentVideo")
    parent_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Reels")
    reels_count = cursor.fetchone()[0]
    
    print(f"   ParentVideo: {parent_count} records")
    print(f"   Reels: {reels_count} records")
    
    conn.close()
    
    print("\n🎉 Migration completed successfully!")
    print("\nNew structure:")
    print("  - ParentVideo: id, name, theme, created_date, output_path")
    print("  - Reels: id, parent_url, url, added_date, processed, theme, author, parent_video_id")

if __name__ == "__main__":
    migrate_database()
