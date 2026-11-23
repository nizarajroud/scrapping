#!/usr/bin/env python3

import sqlite3
import subprocess
import sys
import os
import random
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrapping.db")

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

def _href_to_reel_url(href, page_url):
    """Return the cleaned reel/video URL if href is one, else None (same rules as the Playwright path)."""
    if not href:
        return None
    low = page_url.lower()
    is_instagram = "instagram.com" in low
    is_youtube = "youtube.com" in low
    is_tiktok = "tiktok.com" in low
    if href.startswith('/'):
        if is_instagram:
            href = f"https://www.instagram.com{href}"
        elif is_youtube:
            href = f"https://www.youtube.com{href}"
        elif is_tiktok:
            href = f"https://www.tiktok.com{href}"
        else:
            href = f"https://www.facebook.com{href}"
    if is_instagram:
        ok = '/reel/' in href or '/p/' in href
    elif is_youtube:
        ok = '/shorts/' in href
    elif is_tiktok:
        ok = '/video/' in href
    else:
        ok = '/reel/' in href or '/videos/' in href
    return href.split('?')[0].split('#')[0] if ok else None


def get_reel_links_cdp(page_url, max_scrolls=1000, url_limit=50, category_id=None, author=None, parent_url=None):
    """Same job as get_reel_links, but drives the dedicated Chrome debug instance (CDP, port 9222)
    that already holds the user's logged-in sessions. No password is read or typed."""
    import json, urllib.request, websocket

    host = subprocess.run("ip route show default | awk '{print $3}' | head -1", shell=True,
                          capture_output=True, text=True).stdout.strip() or "127.0.0.1"
    base = f"http://{host}:9222"
    try:
        urllib.request.urlopen(f"{base}/json/version", timeout=5).read()
    except Exception as e:
        print(f"❌ Chrome debug injoignable sur {base} ({e}). Lance: chrome-agent-ctl.py ensure")
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO Source (category_id, parent_url, author) VALUES (?, ?, ?)",
                   (category_id, parent_url, author))
    conn.commit()
    cursor.execute("SELECT id FROM Source WHERE category_id=? AND parent_url=? AND author=?",
                   (category_id, parent_url, author))
    source_id = cursor.fetchone()[0]

    # Dedicated tab (never touch the user's tabs); closed at the end
    req = urllib.request.Request(f"{base}/json/new?about:blank", method="PUT")
    tab = json.load(urllib.request.urlopen(req, timeout=10))
    ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=30)
    _id = [0]

    def cmd(method, params=None):
        _id[0] += 1
        ws.send(json.dumps({"id": _id[0], "method": method, "params": params or {}}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == _id[0]:
                return r

    def ev(expr):
        r = cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    total_saved = 0
    try:
        cmd("Page.enable")
        cmd("Runtime.enable")
        print(f"🌐 (Chrome debug) Navigating to: {page_url}")
        cmd("Page.navigate", {"url": page_url})
        time.sleep(6)

        if ev("!!document.querySelector('input[name=\"pass\"]') || document.body.innerText.includes('Informations de compte oubliées') || document.body.innerText.includes('Forgotten account')"):
            print("❌ La page demande une connexion: connecte-toi à la main dans la fenêtre Chrome debug, puis relance.")
            return 0

        scroll_count = 0
        no_new = 0
        previous_total = 0
        max_no_new = int(os.getenv('MAX_CONSECUTIVE_SCROLLS', '5'))
        print("🔄 Starting reel collection and saving to database...")
        while scroll_count < max_scrolls:
            ev("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(random.uniform(2, 4))
            hrefs = ev("Array.from(document.querySelectorAll('a[href]')).map(a => a.getAttribute('href'))") or []
            for href in hrefs:
                clean_url = _href_to_reel_url(href, page_url)
                if not clean_url:
                    continue
                try:
                    cursor.execute("INSERT INTO Reels (url, added_date, source_id) VALUES (?, ?, ?)",
                                   (clean_url, datetime.now().isoformat(), source_id))
                    conn.commit()
                    total_saved += 1
                    print(f"✓ Saved: {clean_url} (Total: {total_saved})")
                except sqlite3.IntegrityError:
                    pass
                if total_saved >= url_limit:
                    break
            scroll_count += 1
            if total_saved >= url_limit:
                print(f"🏁 Reached {url_limit} URLs limit")
                break
            if total_saved > previous_total:
                no_new = 0
                previous_total = total_saved
            else:
                no_new += 1
            if scroll_count % 10 == 0:
                print(f"📊 Scrolled {scroll_count} times, saved {total_saved} URLs")
            if no_new >= max_no_new:
                print(f"🏁 No new URLs found after {no_new} scrolls. Ending.")
                break
        print(f"\n🎉 Scraping complete! Saved {total_saved} URLs to database")
    finally:
        try:
            ws.close()
            urllib.request.urlopen(f"{base}/json/close/{tab['id']}", timeout=5).read()
        except Exception:
            pass
        conn.close()
    return total_saved


def main():
    ap = argparse.ArgumentParser(description="Reel URL collector (Chrome debug by default)")
    ap.add_argument("--limit", type=int, default=None, help="max URLs to save (overrides MAX_URL)")
    ap.add_argument("--playwright", action="store_true", help="use the old Playwright engine instead of Chrome debug")
    ap.add_argument("--url", default=None, help="page URL (skips the prompt)")
    ap.add_argument("--category", default=None, help="category name (skips the menu)")
    ap.add_argument("--author", default=None, help="author name (skips the prompt)")
    args = ap.parse_args()

    ensure_db_exists()
    if args.playwright:
        install_playwright()

    print("🔐 Reel URL Collector & Scraper")
    print("=" * 70)

    url = (args.url or input("Enter page URL (Facebook/Instagram/TikTok/YouTube): ")).strip()
    if not url:
        print("❌ URL is required")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM Category ORDER BY name")
    categories = cursor.fetchall()
    conn.close()
    if not categories:
        print("❌ No categories found in database. Please add categories first.")
        return

    category_names = [cat[1] for cat in categories]
    if args.category:
        if args.category not in category_names:
            print(f"❌ Unknown category: {args.category} (available: {', '.join(category_names)})")
            return
        selected_category = args.category
    else:
        print("\nSelect category:")
        try:
            from pyfzf.pyfzf import FzfPrompt
        except ImportError:
            print("Installing pyfzf...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyfzf'])
            from pyfzf.pyfzf import FzfPrompt
        try:
            selected_category = FzfPrompt().prompt(category_names, fzf_options='--no-info')[0]
        except IndexError:
            selected_category = None
    if not selected_category:
        print("❌ Category is required")
        return

    category_id = next(cat[0] for cat in categories if cat[1] == selected_category)
    print(f"Selected category: {selected_category}")

    author = (args.author or input("\nEnter author name: ")).strip() or "Unknown"
    print(f"Author: {author}")

    url_limit = args.limit if args.limit else int(os.getenv('MAX_URL', '500'))

    if args.playwright:
        profile_path = "/home/nizar/Clone-Chrome-profile/User Data"
        get_reel_links(url, profile_path, url_limit=url_limit, category_id=category_id, author=author, parent_url=url)
    else:
        get_reel_links_cdp(url, url_limit=url_limit, category_id=category_id, author=author, parent_url=url)

if __name__ == "__main__":
    main()
