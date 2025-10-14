from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import getpass

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

def facebook_login(driver, email, password):
    """Logs into Facebook using the provided credentials"""
    driver.get("https://www.facebook.com/login")
    time.sleep(3)

    email_box = driver.find_element(By.ID, "email")
    password_box = driver.find_element(By.ID, "pass")

    email_box.send_keys(email)
    password_box.send_keys(password)
    password_box.send_keys(Keys.RETURN)

    time.sleep(5)  # wait for login to complete

def get_reel_links(page_url, email, password, max_scrolls=500, delay=2, no_new_content_limit=15):
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

        # Initialize tracking variables
        all_reel_urls = set()
        scroll_count = 0
        no_new_content_count = 0
        last_height = 0
        
        print("🔄 Starting aggressive reel collection...")
        
        while scroll_count < max_scrolls:
            # Get current count before scrolling
            previous_count = len(all_reel_urls)
            previous_height = driver.execute_script("return document.body.scrollHeight;")
            
            # Human-like scrolling patterns
            scroll_patterns = ["smooth", "viewport", "fast"]
            scroll_type = random.choice(scroll_patterns)
            
            print(f"🖱️ Scroll {scroll_count + 1}: Using {scroll_type} scroll pattern...")
            
            # Perform human-like scroll
            human_like_scroll(driver, scroll_type)
            
            # Random human behavior
            if random.random() < 0.3:  # 30% chance
                simulate_human_behavior(driver)
            
            # Wait for content with realistic timing
            wait_time = random.uniform(2, 4)
            print(f"⏳ Waiting {wait_time:.1f}s for content to load...")
            time.sleep(wait_time)
            
            # Additional wait if content is still loading
            if wait_for_content_load(driver, timeout=5):
                print("📈 New content detected, waiting a bit more...")
                time.sleep(random.uniform(1, 2))
            
            # Try multiple selectors to find reel links
            selectors = [
                "//a[contains(@href, '/reel/')]",
                "//a[contains(@href, 'reel')]",
                "//a[contains(@aria-label, 'reel') or contains(@aria-label, 'Reel')]",
                "//div[@role='article']//a[contains(@href, 'facebook.com')]",
                "//a[contains(@href, '/videos/')]",
                "//a[@role='link'][contains(@href, 'facebook.com')]"
            ]
            
            # Extract reel links using multiple selectors
            for selector in selectors:
                try:
                    links = driver.find_elements(By.XPATH, selector)
                    for link in links:
                        href = link.get_attribute("href")
                        if href and ('/reel/' in href or '/videos/' in href):
                            # Clean URL (remove query parameters)
                            clean_url = href.split('?')[0].split('#')[0]
                            if 'facebook.com' in clean_url:
                                all_reel_urls.add(clean_url)
                except Exception as e:
                    continue
            
            # Also try to find links in data attributes
            try:
                elements_with_data = driver.find_elements(By.XPATH, "//*[@data-href]")
                for element in elements_with_data:
                    data_href = element.get_attribute("data-href")
                    if data_href and ('/reel/' in data_href or '/videos/' in data_href):
                        clean_url = data_href.split('?')[0].split('#')[0]
                        if 'facebook.com' in clean_url:
                            all_reel_urls.add(clean_url)
            except Exception as e:
                pass
            
            scroll_count += 1
            current_count = len(all_reel_urls)
            current_height = driver.execute_script("return document.body.scrollHeight;")
            
            # Check if we found new content
            if current_count > previous_count:
                no_new_content_count = 0  # Reset counter
                print(f"✅ Found {current_count} total URLs (+{current_count - previous_count} new)")
            else:
                no_new_content_count += 1
                print(f"⚠️ No new URLs found ({no_new_content_count}/{no_new_content_limit})")
            
            # Check if page height changed (another indicator of new content)
            if current_height == previous_height and current_count == previous_count:
                no_new_content_count += 1
                print(f"📏 Page height unchanged: {current_height}")
            else:
                no_new_content_count = 0  # Reset if height changed
                print(f"📏 Page height: {previous_height} → {current_height}")
            
            # Break if no new content for extended period and at bottom
            at_bottom = driver.execute_script("return (window.innerHeight + window.scrollY) >= document.body.scrollHeight - 100;")
            if no_new_content_count >= no_new_content_limit and at_bottom:
                print("🏁 Reached bottom with no new content - stopping")
                break
            
            # Occasionally do more aggressive content refresh
            if scroll_count % 20 == 0:
                print("🔄 Performing content refresh...")
                # Scroll up significantly then back down
                driver.execute_script("window.scrollBy(0, -3000);")
                time.sleep(random.uniform(1, 2))
                driver.execute_script("window.scrollBy(0, 3000);")
                time.sleep(random.uniform(2, 3))
                
            # Break if we've reached the bottom and no new content for a while
            if (current_height == previous_height and 
                no_new_content_count >= 3 and 
                driver.execute_script("return (window.innerHeight + window.scrollY) >= document.body.scrollHeight;")):
                print("🏁 Reached bottom of page with no new content")
                break
        
        # Final status
        if no_new_content_count >= no_new_content_limit:
            print(f"✅ Stopped: No new content found after {no_new_content_limit} consecutive attempts")
        elif scroll_count >= max_scrolls:
            print(f"⚠️ Stopped: Reached maximum scroll limit ({max_scrolls})")
        
        # Filter and clean results
        filtered_urls = []
        for url in all_reel_urls:
            if '/reel/' in url or '/videos/' in url:
                filtered_urls.append(url)
        
        return filtered_urls
        
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        return []
    finally:
        driver.quit()


if __name__ == "__main__":
    print("🔐 Facebook Reels Scraper")
    print("=" * 30)
    
    # Prompt for Facebook credentials
    FB_EMAIL = input("Enter your Facebook email: ").strip()
    FB_PASS = getpass.getpass("Enter your Facebook password: ")
    
    # Validate inputs
    if not FB_EMAIL or not FB_PASS:
        print("❌ Email and password are required!")
        exit(1)
    
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
        
        reels = get_reel_links(url, FB_EMAIL, FB_PASS, max_scrolls=500, delay=2)
        
        print(f"\n🎉 Successfully found {len(reels)} unique reels!")
        print("=" * 60)
        
        if reels:
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
