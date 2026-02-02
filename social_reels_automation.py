#!/usr/bin/env python3
"""
Facebook Reels Scraper, Downloader, Combiner, Google Drive & YouTube Uploader - Playwright Version
"""

import subprocess
import sys
import time
import random
import os
import shutil
from datetime import datetime
from pathlib import Path

def install_playwright():
    """Install Playwright"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'playwright'])
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])
        print("✓ Installed Playwright")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install Playwright")
        return False

def install_ytdlp():
    """Install/update yt-dlp and dependencies"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'])
        print("✓ Updated yt-dlp")
    except subprocess.CalledProcessError:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', '--user', 'yt-dlp'])
            print("✓ Updated yt-dlp with --user flag")
        except subprocess.CalledProcessError:
            print("✗ Failed to update yt-dlp")
            return False
    
    # Install curl_cffi for TikTok impersonation
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'curl_cffi'])
        print("✓ Installed curl_cffi for TikTok support")
    except subprocess.CalledProcessError:
        print("⚠ curl_cffi installation failed (TikTok may not work)")
    
    return True

def install_google_dependencies():
    """Install required Google API packages"""
    packages = ['google-api-python-client', 'google-auth-httplib2', 'google-auth-oauthlib']
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        except subprocess.CalledProcessError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', package])

def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_reel_links(page_url, profile_path, max_scrolls=1000, delay=2, no_new_content_limit=10, url_limit=100, headless=None):
    from playwright.sync_api import sync_playwright
    
    if headless is None:
        headless_env = os.getenv('HEADLESS')
        if headless_env == '1':
            headless = True
        else:
            from pyfzf.pyfzf import FzfPrompt
            fzf = FzfPrompt()
            options = ["Visible (you can see the browser)", "Headless (background, faster)"]
            choice = fzf.prompt(options, "--prompt='Select browser mode: '")
            headless = choice and "Headless" in choice[0]
    
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
            
            all_reel_urls = set()
            scroll_count = 0
            no_new_content_count = 0
            
            print("🔄 Starting infinite scroll reel collection...")
            
            while scroll_count < max_scrolls:
                previous_count = len(all_reel_urls)
                
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(random.randint(2000, 4000))
                
                # Get all links
                try:
                    links = page.query_selector_all("a[href]")
                    for link in links:
                        href = link.get_attribute("href")
                        if href:
                            # Make relative URLs absolute
                            if href.startswith('/'):
                                if is_instagram:
                                    href = f"https://www.instagram.com{href}"
                                elif is_youtube:
                                    href = f"https://www.youtube.com{href}"
                                elif is_tiktok:
                                    href = f"https://www.tiktok.com{href}"
                                else:
                                    href = f"https://www.facebook.com{href}"
                            
                            if is_instagram and ('/reel/' in href or '/p/' in href) and 'instagram.com' in href:
                                clean_url = href.split('?')[0].split('#')[0]
                                all_reel_urls.add(clean_url)
                            elif is_youtube and '/shorts/' in href and 'youtube.com' in href:
                                clean_url = href.split('?')[0].split('#')[0]
                                all_reel_urls.add(clean_url)
                            elif is_tiktok and '/video/' in href and 'tiktok.com' in href:
                                clean_url = href.split('?')[0].split('#')[0]
                                all_reel_urls.add(clean_url)
                            elif not is_instagram and not is_youtube and not is_tiktok and ('/reel/' in href or '/videos/' in href) and 'facebook.com' in href:
                                clean_url = href.split('?')[0].split('#')[0]
                                all_reel_urls.add(clean_url)
                except:
                    continue
                
                # Also check data-href attributes
                try:
                    elements_with_data = page.query_selector_all("[data-href]")
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
                
                if no_new_content_count >= no_new_content_limit or current_count >= url_limit:
                    if current_count >= url_limit:
                        print(f"🏁 Reached {url_limit} URLs limit")
                    else:
                        print("🏁 Reached end - no new content loading")
                    break
                
                if scroll_count % 50 == 0:
                    print("🔄 Refreshing page to load more content...")
                    page.reload()
                    page.wait_for_timeout(5000)
            
            print(f"📊 Completed after {scroll_count} scrolls")
            
            filtered_urls = [url for url in all_reel_urls if '/reel/' in url or '/videos/' in url or '/shorts/' in url or '/video/' in url]
            return filtered_urls
            
        except Exception as e:
            print(f"❌ Error during scraping: {str(e)}")
            return []
        finally:
            browser.close()

def download_facebook_reel(url, output_name):
    """Download reel using yt-dlp with platform-specific options"""
    try:
        # Use python module to ensure updated version
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            '--no-check-certificate',
            '-f', 'bv*+ba/b',
            '--output', f'{output_name}.%(ext)s',
        ]
        
        # Add platform-specific options
        if 'tiktok.com' in url:
            # Use cookies from Chrome profile for TikTok
            cookies_path = os.path.expanduser('~/Clone-Chrome-profile/User Data/Default/Cookies')
            if os.path.exists(cookies_path):
                cmd.extend(['--cookies-from-browser', 'chrome'])
        else:
            cmd.extend(['--extractor-args', 'youtube:player_client=android'])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f'{output_name}.mp4'
        else:
            print(f"yt-dlp error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def upload_to_gdrive(file_path, credentials_path, token_path):
    """Upload file to Google Drive"""
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.http import MediaFileUpload
        
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    print(f"❌ {credentials_path} not found")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=8080)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': os.path.basename(file_path)}
        media = MediaFileUpload(file_path, resumable=True)
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"✓ Uploaded to Google Drive: {os.path.basename(file_path)} (ID: {file.get('id')})")
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def upload_to_youtube(video_path, title, description="", privacy="private", credentials_path='credentials.json', token_path='youtube_token.json'):
    """Upload video to YouTube"""
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.http import MediaFileUpload
        
        SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    print(f"❌ {credentials_path} not found")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=8080)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        youtube = build('youtube', 'v3', credentials=creds)
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': privacy
            }
        }
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        response = request.execute()
        
        video_id = response['id']
        print(f"✓ Uploaded to YouTube: {os.path.basename(video_path)} (https://youtube.com/watch?v={video_id})")
        return True
        
    except Exception as e:
        if 'youtubeSignupRequired' in str(e):
            print("❌ YouTube channel verification required")
            print("Create/verify your YouTube channel at: https://www.youtube.com/verify")
        else:
            print(f"❌ YouTube upload failed: {e}")
        return False

def main():
    print("🔐 Facebook Reels Scraper, Downloader, Combiner & Multi-Platform Uploader (Playwright)")
    print("=" * 70)
    
    # Install Playwright if needed
    try:
        import playwright
    except ImportError:
        print("Installing Playwright...")
        if not install_playwright():
            exit(1)
    
    # Get target URL first
    url = input("Enter Facebook/Instagram/TikTok/YouTube page URL: ").strip()
    if not url:
        print("❌ URL is required. Exiting.")
        exit(1)
    
    # Ask for category using pyfzf
    print("Category of combined-reels:")
    categories = os.getenv('CATEGORIES', 'Relg,Soft,Kids,Misc,English').split(',')
    try:
        from pyfzf.pyfzf import FzfPrompt
        fzf = FzfPrompt()
        category = fzf.prompt(categories, fzf_options='--no-info')[0]
    except ImportError:
        print("Installing pyfzf...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyfzf'])
        from pyfzf.pyfzf import FzfPrompt
        fzf = FzfPrompt()
        category = fzf.prompt(categories, fzf_options='--no-info')[0]
    except IndexError:
        category = "Relg"  # Default if cancelled
    
    print(f"Selected category: {category}")
    
    # Ask for duplication count
    dup_count = input("\nEnter duplication count for each video (default: 1, no duplication): ").strip()
    try:
        dup_count = int(dup_count) if dup_count else 1
        dup_count = max(1, dup_count)
    except ValueError:
        dup_count = 1
    
    if dup_count > 1:
        print(f"✓ Each video will be duplicated {dup_count} times")
    
    # Ask for name
    reel_name = input("\nEnter name for combined reels: ").strip()
    if not reel_name:
        reel_name = "combined_reels"
    
    # Add category prefix
    reel_name = f"{category}-{reel_name}"
    
    # Replace spaces with dashes
    reel_name = reel_name.replace(" ", "-")
    
    # Generate default path with date and random number
    now = datetime.now()
    day_name = now.strftime("%A")
    date_str = now.strftime("%d-%m")
    random_num = random.randint(10, 99)
    default_base_path = f"/mnt/d/PERSONAL/scrap/{day_name}-{date_str}-{random_num}"
    
    # Get base output path
    base_path = input(f"Enter base directory (or press Enter for default {default_base_path}): ").strip()
    if not base_path:
        base_path = default_base_path
    
    # Create folder with reel name
    output_path = os.path.join(base_path, reel_name)
    os.makedirs(output_path, exist_ok=True)
    
    output_file = os.path.join(output_path, "scrapped-urls.txt")
    print(f"📁 Output file: {output_file}")
    print()
    
    # Ask for URL limit
    url_limit = input("Enter maximum number of URLs to scrape (default: 100): ").strip()
    try:
        url_limit = int(url_limit) if url_limit else 100
    except ValueError:
        url_limit = 100
    
    print(f"URL limit set to: {url_limit}")
    
    # Chrome profile path
    profile_path = "/home/nizar/Clone-Chrome-profile/User Data"
    
    print(f"✅ Using Chrome profile: {profile_path}")
    
    print(f"\n🚀 Starting scraper for: {url}")
    print("⏳ This will continue until all reels are found...")
    
    try:
        reels = get_reel_links(url, profile_path, max_scrolls=1000, delay=2, url_limit=url_limit)
        
        print(f"\n🎉 Successfully found {len(reels)} unique reels!")
        print("=" * 60)
        
        # Save URLs to scrapped-urls.txt
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            for url in reels:
                f.write(url + "\n")
        
        if reels:
            print(f"📁 URLs saved to {output_file}")
            
            # Automatically download and combine videos
            print("\n🚀 Starting download and combine process...")
            if True:
                # Re-read URLs from file in case it was manually edited
                try:
                    with open(output_file, "r", encoding="utf-8") as f:
                        all_urls = [line.strip() for line in f if line.strip()]
                    
                    # Filter to keep only video URLs
                    reels = [url for url in all_urls if '/video/' in url or '/reel/' in url or '/shorts/' in url or '/videos/' in url]
                    
                    print(f"📖 Re-read {len(all_urls)} URLs, filtered to {len(reels)} video URLs")
                except Exception as e:
                    print(f"❌ Error re-reading URLs: {e}")
                    return
                
                # Check FFmpeg
                print("Checking for FFmpeg...")
                if not check_ffmpeg():
                    print("✗ FFmpeg not found! Please install FFmpeg first.")
                    return
                else:
                    print("✓ FFmpeg found")
                
                # Install yt-dlp
                print("Installing/updating yt-dlp...")
                if not install_ytdlp():
                    return
                
                # Create and change to output directory
                Path(output_path).mkdir(parents=True, exist_ok=True)
                os.chdir(output_path)
                
                # Download videos (limited by user input)
                print(f"\nDownloading up to {url_limit} videos...")
                video_files = []
                download_count = 0
                for i, reel_url in enumerate(reels, 1):
                    if download_count >= url_limit:
                        print(f"Reached download limit of {url_limit} videos")
                        break
                    
                    print(f"Downloading reel {download_count + 1}/{min(len(reels), url_limit)}...")
                    filename = download_facebook_reel(reel_url, f"reel_{i}")
                    if filename and Path(filename).exists():
                        video_files.append(filename)
                        download_count += 1
                        print(f"✓ Downloaded: {filename}")
                    else:
                        print(f"✗ Failed to download reel {i}")
                
                # Combine videos
                if len(video_files) >= 2:
                    print(f"\nCombining {len(video_files)} videos...")
                    
                    # Generate filename with date
                    date_str = now.strftime("%d-%m-%y")
                    output_video = os.path.join(output_path, f"{reel_name}-{date_str}.mp4")
                    
                    # Normalize each video
                    normalized_files = []
                    for i, video in enumerate(video_files):
                        norm_file = os.path.join(output_path, f"norm_{i}.mp4")
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
                    filelist_path = os.path.join(output_path, "temp_filelist.txt")
                    with open(filelist_path, 'w') as f:
                        for norm_file in normalized_files:
                            for _ in range(dup_count):
                                f.write(f"file '{os.path.abspath(norm_file)}'\n")
                    
                    cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', filelist_path, '-c', 'copy', '-y', output_video]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    # Cleanup
                    os.remove(filelist_path)
                    for norm_file in normalized_files:
                        os.remove(norm_file)
                    
                    if result.returncode == 0:
                        print(f"✓ Combined video saved as: {output_video}")
                        
                        # Move to target directory
                        target_dir = "/mnt/g/Mon Drive/FORMATIONS/SoftSkills/Infuse"
                        os.makedirs(target_dir, exist_ok=True)
                        target_path = os.path.join(target_dir, os.path.basename(output_video))
                        shutil.move(output_video, target_path)
                        print(f"✓ Moved to: {target_path}")
                        output_video = target_path
                        
                        # Extract MP3 audio only if requested
                        
                        # Clean up individual files
                        print("\n🗑️ Cleaning up individual video files...")
                        for file in video_files:
                            try:
                                Path(file).unlink()
                                print(f"Deleted: {file}")
                            except Exception as e:
                                print(f"Could not delete {file}: {e}")
                        
                        print(f"\n✅ Process completed!")
                        print(f"📹 Video: {output_video}")
                        print(f"\n💡 To extract audio: python3 extract_audio.py {output_video}")
                        print(f"💡 To upload files: python3 upload-to-platforms.py <file_path>")
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