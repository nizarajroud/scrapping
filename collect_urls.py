#!/usr/bin/env python3

import sqlite3
import subprocess
import sys
import os
import random
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_PATH = "scrapping.db"

def ensure_db_exists():
    """Ensure database and tables exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Source (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            parent_url TEXT NOT NULL,
            author TEXT NOT NULL,
            UNIQUE(category_id, parent_url, author),
            FOREIGN KEY (category_id) REFERENCES Category(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ParentVideo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            theme TEXT NOT NULL,
            created_date TEXT NOT NULL,
            output_path TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reels (
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
    conn.commit()
    conn.close()

def install_playwright():
    """Install Playwright if needed"""
    try:
        import playwright
    except ImportError:
        print("Installing Playwright...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'playwright'])
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])

def get_reel_links(page_url, profile_path, max_scrolls=1000, delay=2, url_limit=100, category_id=None, author=None, parent_url=None):
    """Scrape reel URLs and save to database in real-time"""
    from playwright.sync_api import sync_playwright
    
    # Check headless mode from environment
    headless = os.getenv('HEADLESS', '1') == '1'
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get or create source_id
    cursor.execute("""
        INSERT OR IGNORE INTO Source (category_id, parent_url, author)
        VALUES (?, ?, ?)
    """, (category_id, parent_url, author))
    conn.commit()
    
    cursor.execute("""
        SELECT id FROM Source WHERE category_id=? AND parent_url=? AND author=?
    """, (category_id, parent_url, author))
    source_id = cursor.fetchone()[0]
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        page = browser.new_page()
        
        try:
            print(f"🌐 Navigating to: {page_url}")
            page.goto(page_url)
            page.wait_for_timeout(5000)
            
            is_instagram = "instagram.com" in page_url.lower()
            is_youtube = "youtube.com" in page_url.lower()
            is_tiktok = "tiktok.com" in page_url.lower()
            
            scroll_count = 0
            no_new_content_count = 0
            total_saved = 0
            previous_total = 0
            
            print("🔄 Starting reel collection and saving to database...")
            
            while scroll_count < max_scrolls:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(random.randint(2000, 4000))
                
                links = page.query_selector_all("a[href]")
                for link in links:
                    href = link.get_attribute("href")
                    if href:
                        if href.startswith('/'):
                            if is_instagram:
                                href = f"https://www.instagram.com{href}"
                            elif is_youtube:
                                href = f"https://www.youtube.com{href}"
                            elif is_tiktok:
                                href = f"https://www.tiktok.com{href}"
                            else:
                                href = f"https://www.facebook.com{href}"
                        
                        should_save = False
                        if is_instagram and ('/reel/' in href or '/p/' in href):
                            should_save = True
                        elif is_youtube and '/shorts/' in href:
                            should_save = True
                        elif is_tiktok and '/video/' in href:
                            should_save = True
                        elif not is_instagram and not is_youtube and not is_tiktok and ('/reel/' in href or '/videos/' in href):
                            should_save = True
                        
                        if should_save:
                            clean_url = href.split('?')[0].split('#')[0]
                            try:
                                cursor.execute("INSERT INTO Reels (url, added_date, source_id) VALUES (?, ?, ?)", 
                                             (clean_url, datetime.now().isoformat(), source_id))
                                conn.commit()
                                total_saved += 1
                                print(f"✓ Saved: {clean_url} (Total: {total_saved})")
                            except sqlite3.IntegrityError:
                                pass  # URL already exists
                
                scroll_count += 1
                
                if total_saved >= url_limit:
                    print(f"🏁 Reached {url_limit} URLs limit")
                    break
                
                # Check if new URLs were saved
                if total_saved > previous_total:
                    no_new_content_count = 0
                    previous_total = total_saved
                else:
                    no_new_content_count += 1
                
                if scroll_count % 10 == 0:
                    print(f"📊 Scrolled {scroll_count} times, saved {total_saved} URLs")
                
                # Exit if no new content for configured scrolls
                if no_new_content_count >= int(os.getenv('MAX_CONSECUTIVE_SCROLLS', '5')):
                    print(f"🏁 No new URLs found after {no_new_content_count} scrolls. Ending.")
                    break
            
            print(f"\n🎉 Scraping complete! Saved {total_saved} URLs to database")
            
        finally:
            browser.close()
            conn.close()

def main():
    ensure_db_exists()
    install_playwright()
    
    print("🔐 Reel URL Collector & Scraper")
    print("=" * 70)
    
    url = input("Enter page URL (Facebook/Instagram/TikTok/YouTube): ").strip()
    if not url:
        print("❌ URL is required")
        return
    
    # Get categories from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM Category ORDER BY name")
    categories = cursor.fetchall()
    conn.close()
    
    if not categories:
        print("❌ No categories found in database. Please add categories first.")
        return
    
    # Ask for category using pyfzf
    print("\nSelect category:")
    category_names = [cat[1] for cat in categories]
    try:
        from pyfzf.pyfzf import FzfPrompt
        fzf = FzfPrompt()
        selected_category = fzf.prompt(category_names, fzf_options='--no-info')[0]
    except ImportError:
        print("Installing pyfzf...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyfzf'])
        from pyfzf.pyfzf import FzfPrompt
        fzf = FzfPrompt()
        selected_category = fzf.prompt(category_names, fzf_options='--no-info')[0]
    except IndexError:
        selected_category = category_names[0] if category_names else None
    
    if not selected_category:
        print("❌ Category is required")
        return
    
    # Get category_id
    category_id = next(cat[0] for cat in categories if cat[1] == selected_category)
    print(f"Selected category: {selected_category}")
    
    # Ask for author
    author = input("\nEnter author name: ").strip()
    if not author:
        author = "Unknown"
    
    print(f"Author: {author}")
    
    url_limit = int(os.getenv('MAX_URL', '500'))
    
    profile_path = "/home/nizar/Clone-Chrome-profile/User Data"
    
    get_reel_links(url, profile_path, url_limit=url_limit, category_id=category_id, author=author, parent_url=url)

if __name__ == "__main__":
    main()
