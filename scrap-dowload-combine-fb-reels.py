#!/usr/bin/env python3
"""
Facebook Reels Scraper, Downloader and Combiner
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
import sys
import time
import random
import os
from datetime import datetime
from pathlib import Path

def install_ytdlp():
    """Install yt-dlp"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'yt-dlp'])
        print("✓ Installed yt-dlp")
    except subprocess.CalledProcessError:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'yt-dlp'])
            print("✓ Installed yt-dlp with --user flag")
        except subprocess.CalledProcessError:
            print("✗ Failed to install yt-dlp")
            return False
    return True

def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def load_credentials():
    """Load Facebook credentials from .my-secrets file"""
    secrets_file = os.path.expanduser("~/.my-secrets")
    full_path = os.path.abspath(secrets_file)
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
            
        return fb_email, fb_password, full_path
        
    except FileNotFoundError:
        print(f"❌ Secrets file not found: {full_path}")
        return None, None, full_path
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return None, None, full_path

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
    
    close_popups(driver)

    email_box = driver.find_element(By.ID, "email")
    password_box = driver.find_element(By.ID, "pass")

    email_box.send_keys(email)
    password_box.send_keys(password)
    password_box.send_keys(Keys.RETURN)

    time.sleep(5)
    close_popups(driver)

def get_reel_links(page_url, email, password, max_scrolls=1000, delay=2, no_new_content_limit=10):
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        facebook_login(driver, email, password)

        print(f"🌐 Navigating to: {page_url}")
        driver.get(page_url)
        time.sleep(5)
        
        close_popups(driver)

        all_reel_urls = set()
        scroll_count = 0
        no_new_content_count = 0
        consecutive_no_change = 0
        
        print("🔄 Starting infinite scroll reel collection...")
        
        while scroll_count < max_scrolls:
            if scroll_count % 5 == 0:
                close_popups(driver)
            
            previous_count = len(all_reel_urls)
            previous_height = driver.execute_script("return document.body.scrollHeight;")
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            
            new_height = driver.execute_script("return document.body.scrollHeight;")
            if new_height > previous_height:
                print(f"📈 Page height increased: {previous_height} → {new_height}")
                consecutive_no_change = 0
                time.sleep(random.uniform(1, 2))
            else:
                consecutive_no_change += 1
            
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
            
            if current_count > previous_count:
                no_new_content_count = 0
                print(f"✅ Found {current_count} total URLs (+{current_count - previous_count} new)")
            else:
                no_new_content_count += 1
                print(f"⚠️ No new URLs found ({no_new_content_count}/{no_new_content_limit})")
            
            at_bottom = driver.execute_script("return (window.innerHeight + window.scrollY) >= document.body.scrollHeight - 100;")
            
            if (no_new_content_count >= no_new_content_limit and 
                consecutive_no_change >= 5 and at_bottom):
                print("🏁 Reached end - no new content loading")
                break
            
            if scroll_count % 50 == 0:
                print("🔄 Refreshing page to load more content...")
                driver.refresh()
                time.sleep(5)
                close_popups(driver)
        
        print(f"📊 Completed after {scroll_count} scrolls")
        
        filtered_urls = [url for url in all_reel_urls if '/reel/' in url or '/videos/' in url]
        return filtered_urls
        
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        return []
    finally:
        driver.quit()

def download_facebook_reel(url, output_name):
    """Download Facebook reel using yt-dlp"""
    try:
        cmd = [
            'yt-dlp',
            '--no-check-certificate',
            '--format', 'best[ext=mp4]',
            '--output', f'{output_name}.%(ext)s',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f'{output_name}.mp4'
        else:
            print(f"yt-dlp error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def main():
    print("🔐 Facebook Reels Scraper, Downloader & Combiner")
    print("=" * 50)
    
    # Get target URL first
    url = input("Enter Facebook reels page URL: ").strip()
    if not url:
        print("❌ URL is required. Exiting.")
        exit(1)
    
    # Ask for name
    reel_name = input("Enter name for combined reels: ").strip()
    if not reel_name:
        reel_name = "combined_reels"
    
    # Generate default path with date and random number
    now = datetime.now()
    day_name = now.strftime("%A")
    date_str = now.strftime("%d-%m")
    random_num = random.randint(10, 99)
    default_path = f"/mnt/d/PERSONAL/scrap/{day_name}-{date_str}-{random_num}"
    
    # Get output path
    output_path = input(f"Enter output directory (or press Enter for default {default_path}): ").strip()
    if not output_path:
        output_path = default_path
    
    output_file = os.path.join(output_path, "scrapped-urls.txt")
    print(f"📁 Output file: {output_file}")
    print()
    
    # Load Facebook credentials from secrets file
    FB_EMAIL, FB_PASS, credentials_path = load_credentials()
    
    if not FB_EMAIL or not FB_PASS:
        print("❌ Could not load Facebook credentials from ~/.my-secrets")
        print("💡 Make sure FCB_LOGIN and FCB_PWD are set in the file")
        exit(1)
    
    print(f"✅ Loaded credentials for: {FB_EMAIL} from {credentials_path}")
    
    print(f"\n🚀 Starting scraper for: {url}")
    print("⏳ This will continue until all reels are found...")
    
    try:
        reels = get_reel_links(url, FB_EMAIL, FB_PASS, max_scrolls=1000, delay=2)
        
        print(f"\n🎉 Successfully found {len(reels)} unique reels!")
        print("=" * 60)
        
        # Save URLs to scrapped-urls.txt
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            for url in reels:
                f.write(url + "\n")
        
        if reels:
            print(f"📁 URLs saved to {output_file}")
            
            # Ask if user wants to download and combine
            download_choice = input("\nDownload and combine videos? (Y/n): ").strip().lower()
            if download_choice != 'n':
                # Check FFmpeg
                print("Checking for FFmpeg...")
                if not check_ffmpeg():
                    print("✗ FFmpeg not found! Please install FFmpeg first.")
                    return
                else:
                    print("✓ FFmpeg found")
                
                # Install yt-dlp
                print("Installing yt-dlp...")
                if not install_ytdlp():
                    return
                
                # Create and change to output directory
                Path(output_path).mkdir(parents=True, exist_ok=True)
                os.chdir(output_path)
                
                # Download videos
                print(f"\nDownloading {len(reels)} videos...")
                video_files = []
                for i, reel_url in enumerate(reels, 1):
                    print(f"Downloading reel {i}/{len(reels)}...")
                    filename = download_facebook_reel(reel_url, f"reel_{i}")
                    if filename and Path(filename).exists():
                        video_files.append(filename)
                        print(f"✓ Downloaded: {filename}")
                    else:
                        print(f"✗ Failed to download reel {i}")
                
                # Combine videos
                if len(video_files) >= 2:
                    print(f"\nCombining {len(video_files)} videos...")
                    
                    # Generate filename with date
                    date_str = now.strftime("%d-%m-%y")
                    output_video = f"{reel_name}-{date_str}.mp4"
                    
                    # Normalize each video
                    normalized_files = []
                    for i, video in enumerate(video_files):
                        norm_file = f"norm_{i}.mp4"
                        cmd = [
                            'ffmpeg', '-i', video,
                            '-vf', 'scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2',
                            '-r', '25', '-c:v', 'libx264', '-preset', 'ultrafast',
                            '-c:a', 'aac', '-ar', '44100',
                            '-y', norm_file
                        ]
                        subprocess.run(cmd, capture_output=True)
                        normalized_files.append(norm_file)
                    
                    # Concat videos
                    filelist_path = "temp_filelist.txt"
                    with open(filelist_path, 'w') as f:
                        for norm_file in normalized_files:
                            f.write(f"file '{os.path.abspath(norm_file)}'\n")
                    
                    cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', filelist_path, '-c', 'copy', '-y', output_video]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    # Cleanup
                    os.remove(filelist_path)
                    for norm_file in normalized_files:
                        os.remove(norm_file)
                    
                    if result.returncode == 0:
                        print(f"✓ Combined video saved as: {output_video}")
                        
                        # Extract MP3 audio
                        print("Extracting MP3 audio...")
                        mp3_file = f"{reel_name}-{date_str}.mp3"
                        mp3_cmd = [
                            'ffmpeg', '-i', output_video,
                            '-vn', '-acodec', 'mp3', '-ab', '192k', '-y', mp3_file
                        ]
                        
                        mp3_result = subprocess.run(mp3_cmd, capture_output=True, text=True)
                        if mp3_result.returncode == 0:
                            print(f"✓ MP3 audio saved as: {mp3_file}")
                        
                        # Clean up individual files
                        cleanup = input("\nDelete individual video files? (Y/n): ").lower().strip()
                        if cleanup != 'n':
                            for file in video_files:
                                try:
                                    Path(file).unlink()
                                    print(f"Deleted: {file}")
                                except Exception as e:
                                    print(f"Could not delete {file}: {e}")
                    else:
                        print(f"FFmpeg error: {result.stderr}")
                else:
                    print(f"Need at least 2 videos to combine, only got {len(video_files)}")
        else:
            print("❌ No reels found.")
            
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    main()
