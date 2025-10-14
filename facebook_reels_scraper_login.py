from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import os

def load_credentials():
    """Load Facebook credentials from .my-secrets file"""
    secrets_file = os.path.expanduser("~/.my-secrets")
    credentials = {}
    
    try:
        with open(secrets_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()
        
        fb_email = credentials.get('FCB_LOGIN')
        fb_password = credentials.get('FCB_PWD')
        
        if not fb_email or not fb_password:
            raise ValueError("FCB_LOGIN or FCB_PWD not found in secrets file")
            
        return fb_email, fb_password
        
    except FileNotFoundError:
        print(f"❌ Secrets file not found: {secrets_file}")
        return None, None
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return None, None

def human_like_scroll(driver, scroll_type="smooth"):
    """Simulate human-like scrolling patterns"""
    
    if scroll_type == "smooth":
        # Smooth gradual scrolling like a human
        current_position = driver.execute_script("return window.pageYOffset;")
        viewport_height = driver.execute_script("return window.innerHeight;")
        
        # Scroll in small increments
        scroll_distance = random.randint(300, 600)
        steps = random.randint(3, 6)
        step_size = scroll_distance // steps
        
        for i in range(steps):
            driver.execute_script(f"window.scrollBy(0, {step_size});")
            time.sleep(random.uniform(0.1, 0.3))
            
    elif scroll_type == "viewport":
        # Scroll by viewport height (common human behavior)
        viewport_height = driver.execute_script("return window.innerHeight;")
        scroll_amount = random.randint(int(viewport_height * 0.7), int(viewport_height * 1.2))
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        
    elif scroll_type == "fast":
        # Quick scroll to bottom then back up a bit (human checking behavior)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(0.5, 1.0))
        back_scroll = random.randint(200, 500)
        driver.execute_script(f"window.scrollBy(0, -{back_scroll});")

def wait_for_content_load(driver, timeout=10):
    """Wait for new content to load by monitoring DOM changes"""
    initial_height = driver.execute_script("return document.body.scrollHeight;")
    
    for _ in range(timeout):
        time.sleep(1)
        current_height = driver.execute_script("return document.body.scrollHeight;")
        if current_height > initial_height:
            return True
    return False

def simulate_human_behavior(driver):
    """Simulate random human behaviors that might trigger content loading"""
    behaviors = [
        lambda: driver.execute_script("window.focus();"),  # Focus window
        lambda: time.sleep(random.uniform(0.5, 2.0)),      # Random pause
        lambda: driver.execute_script("window.scrollBy(0, -50); setTimeout(() => window.scrollBy(0, 50), 100);"),  # Small scroll back and forth
    ]
    
    random.choice(behaviors)()

def close_popups(driver):
    """Close any popups that might appear"""
    popup_selectors = [
        "//div[@role='dialog']//div[@aria-label='Close']",
        "//div[@role='dialog']//button[contains(@aria-label, 'Close')]",
        "//div[@role='dialog']//button[contains(@aria-label, 'Dismiss')]",
        "//button[contains(@aria-label, 'Close')]",
        "//button[contains(text(), 'Not Now')]",
        "//button[contains(text(), 'Skip')]",
        "//div[contains(@aria-label, 'Close')]",
        "//span[text()='×']/..",
        "//div[@data-testid='cookie-policy-manage-dialog']//button",
    ]
    
    for selector in popup_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed():
                    element.click()
                    time.sleep(0.5)
                    return True
        except:
            continue
    return False

def facebook_login(driver, email, password):
    """Logs into Facebook using the provided credentials"""
    driver.get("https://www.facebook.com/login")
    time.sleep(3)
    
    # Close any initial popups
    close_popups(driver)

    email_box = driver.find_element(By.ID, "email")
    password_box = driver.find_element(By.ID, "pass")

    email_box.send_keys(email)
    password_box.send_keys(password)
    password_box.send_keys(Keys.RETURN)

    time.sleep(5)  # wait for login to complete
    
    # Close any post-login popups
    close_popups(driver)

def get_reel_links(page_url, email, password, max_scrolls=1000, delay=2, no_new_content_limit=10):
    # Setup Chrome with more realistic settings
    options = Options()
    # Comment this line if you want to see the browser
    # options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Execute script to hide webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        # Login first
        facebook_login(driver, email, password)

        # Open reels page
        print(f"🌐 Navigating to: {page_url}")
        driver.get(page_url)
        time.sleep(5)  # Wait longer for initial load
        
        # Close any initial popups on the reels page
        close_popups(driver)

        # Initialize tracking variables
        all_reel_urls = set()
        scroll_count = 0
        no_new_content_count = 0
        consecutive_no_change = 0
        
        print("🔄 Starting infinite scroll reel collection...")
        
        while scroll_count < max_scrolls:
            # Close popups before each scroll attempt
            if scroll_count % 5 == 0:  # Check every 5 scrolls
                close_popups(driver)
            
            # Get current count and height before scrolling
            previous_count = len(all_reel_urls)
            previous_height = driver.execute_script("return document.body.scrollHeight;")
            
            # Scroll to bottom to trigger infinite scroll
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(random.uniform(2, 4))
            
            # Check if new content loaded by monitoring height changes
            new_height = driver.execute_script("return document.body.scrollHeight;")
            if new_height > previous_height:
                print(f"📈 Page height increased: {previous_height} → {new_height}")
                consecutive_no_change = 0
                # Wait a bit more for content to fully load
                time.sleep(random.uniform(1, 2))
            else:
                consecutive_no_change += 1
            
            # Extract reel links using multiple selectors
            selectors = [
                "//a[contains(@href, '/reel/')]",
                "//a[contains(@href, 'reel')]",
                "//a[contains(@href, '/videos/')]",
                "//div[@role='article']//a[contains(@href, 'facebook.com')]",
            ]
            
            for selector in selectors:
                try:
                    links = driver.find_elements(By.XPATH, selector)
                    for link in links:
                        href = link.get_attribute("href")
                        if href and ('/reel/' in href or '/videos/' in href):
                            clean_url = href.split('?')[0].split('#')[0]
                            if 'facebook.com' in clean_url:
                                all_reel_urls.add(clean_url)
                except:
                    continue
            
            # Also check data attributes
            try:
                elements_with_data = driver.find_elements(By.XPATH, "//*[@data-href]")
                for element in elements_with_data:
                    data_href = element.get_attribute("data-href")
                    if data_href and ('/reel/' in data_href or '/videos/' in data_href):
                        clean_url = data_href.split('?')[0].split('#')[0]
                        if 'facebook.com' in clean_url:
                            all_reel_urls.add(clean_url)
            except:
                pass
            
            scroll_count += 1
            current_count = len(all_reel_urls)
            
            # Check progress
            if current_count > previous_count:
                no_new_content_count = 0
                print(f"✅ Found {current_count} total URLs (+{current_count - previous_count} new)")
            else:
                no_new_content_count += 1
                print(f"⚠️ No new URLs found ({no_new_content_count}/{no_new_content_limit})")
            
            # Check if we should stop
            at_bottom = driver.execute_script("return (window.innerHeight + window.scrollY) >= document.body.scrollHeight - 100;")
            
            # Stop if no new content for extended period and we're at bottom
            if (no_new_content_count >= no_new_content_limit and 
                consecutive_no_change >= 5 and at_bottom):
                print("🏁 Reached end - no new content loading")
                break
            
            # Refresh strategy every 50 scrolls
            if scroll_count % 50 == 0:
                print("🔄 Refreshing page to load more content...")
                driver.refresh()
                time.sleep(5)
                close_popups(driver)
        
        # Final status
        print(f"📊 Completed after {scroll_count} scrolls")
        
        # Filter results
        filtered_urls = [url for url in all_reel_urls if '/reel/' in url or '/videos/' in url]
        return filtered_urls
        
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        return []
    finally:
        driver.quit()


if __name__ == "__main__":
    print("🔐 Facebook Reels Scraper")
    print("=" * 30)
    
    # Load Facebook credentials from secrets file
    FB_EMAIL, FB_PASS = load_credentials()
    
    if not FB_EMAIL or not FB_PASS:
        print("❌ Could not load Facebook credentials from ~/.my-secrets")
        print("💡 Make sure FCB_LOGIN and FCB_PWD are set in the file")
        exit(1)
    
    print(f"✅ Loaded credentials for: {FB_EMAIL}")
    
    # Get target URL
    default_url = "https://www.facebook.com/M.Elkotby2002/reels/"
    url = input(f"Enter Facebook reels page URL (or press Enter for default): ").strip()
    if not url:
        url = default_url
    
    # Ask if user wants to see browser (for debugging)
    show_browser = input("Show browser window for debugging? (y/N): ").strip().lower()
    
    print(f"\n🚀 Starting aggressive scraper for: {url}")
    print("⏳ This will continue until all reels are found...")
    print("💡 Note: This may take several minutes for pages with many reels")
    
    try:
        # Temporarily disable headless if user wants to see browser
        if show_browser == 'y':
            print("🖥️ Browser window will be visible for debugging")
        
        reels = get_reel_links(url, FB_EMAIL, FB_PASS, max_scrolls=1000, delay=2)
        
        print(f"\n🎉 Successfully found {len(reels)} unique reels!")
        print("=" * 60)
        
        # Save URLs to output.txt
        with open("output.txt", "w", encoding="utf-8") as f:
            for url in reels:
                f.write(url + "\n")
        
        if reels:
            print(f"📁 URLs saved to output.txt")
            for i, r in enumerate(reels, 1):
                print(f"{i:3d}. {r}")
        else:
            print("❌ No reels found. This could be due to:")
            print("   • Page requires login and credentials are incorrect")
            print("   • Page structure has changed")
            print("   • Facebook is blocking automated access")
            print("   • The page URL is incorrect or has no reels")
            
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        print("💡 Try checking your credentials or the target URL")
