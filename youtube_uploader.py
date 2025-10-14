#!/usr/bin/env python3
"""
YouTube Video Uploader
Minimal script to upload videos to YouTube
"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required Google API packages"""
    packages = ['google-api-python-client', 'google-auth-httplib2', 'google-auth-oauthlib']
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        except subprocess.CalledProcessError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', package])

def upload_video(video_path, title="Uploaded Video", description="", privacy="private", credentials_path='credentials.json'):
    """Upload video to YouTube"""
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.http import MediaFileUpload
        
        SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        creds = None
        if os.path.exists('youtube_token.json'):
            creds = Credentials.from_authorized_user_file('youtube_token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    print(f"❌ {credentials_path} not found")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=8080)
            
            with open('youtube_token.json', 'w') as token:
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
        print(f"✓ Uploaded: {os.path.basename(video_path)} (https://youtube.com/watch?v={video_id})")
        return True
        
    except Exception as e:
        if 'youtubeSignupRequired' in str(e):
            print("❌ YouTube channel verification required")
            print("Create/verify your YouTube channel at: https://www.youtube.com/verify")
        else:
            print(f"❌ Upload failed: {e}")
        return False

def main():
    USER = os.getenv('USER', 'user')
    default_video = f"/mnt/c/Users/{USER}/DOCS/PERSO/scrap/combined_reels.mp4"
    
    if len(sys.argv) < 2:
        confirm = input(f"Upload {default_video}? (Y/n): ").lower().strip()
        if confirm == 'n':
            video_path = input("Enter video path: ").strip()
        else:
            video_path = default_video
        title = Path(video_path).stem
        privacy = "private"
    else:
        video_path = sys.argv[1]
        title = sys.argv[2] if len(sys.argv) > 2 else Path(video_path).stem
        privacy = sys.argv[3] if len(sys.argv) > 3 else "private"
    
    if not Path(video_path).exists():
        print(f"❌ Video not found: {video_path}")
        sys.exit(1)
    
    print("Installing dependencies...")
    install_dependencies()
    
    print(f"Uploading {video_path} to YouTube...")
    upload_video(video_path, title, "", privacy)

if __name__ == "__main__":
    main()
