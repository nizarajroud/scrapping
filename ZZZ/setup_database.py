#!/usr/bin/env python3

import sqlite3

DB_PATH = "scrapping.db"

def setup_database():
    """Create database and required tables"""
    print(f"Setting up database: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Reels table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_url TEXT,
            url TEXT NOT NULL UNIQUE,
            added_date TEXT NOT NULL,
            processed INTEGER DEFAULT 0,
            theme TEXT,
            author TEXT,
            parent_video TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("✓ Database setup complete")
    print("✓ Table 'Reels' created")

if __name__ == "__main__":
    setup_database()
