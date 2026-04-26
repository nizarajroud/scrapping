#!/usr/bin/env python3
"""
Upload files to Google Drive and YouTube
"""

import sys
import os
import subprocess
from pathlib import Path

def install_google_dependencies():
    """Install required Google API packages"""
    packages = ['google-api-python-client', 'google-auth-httplib2', 'google-auth-oauthlib']
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        except subprocess.CalledProcessError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', package])

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
    if len(sys.argv) < 2:
        print("Usage: python3 upload-to-platforms.py <file_path>")
        print("Example: python3 upload-to-platforms.py /path/to/video.mp4")
        exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        exit(1)
    
    print(f"📁 File to upload: {file_path}")
    file_dir = os.path.dirname(file_path)
    file_name = Path(file_path).stem
    
    # Install Google API dependencies
    print("Installing Google API dependencies...")
    install_google_dependencies()
    
    # YouTube upload
    youtube_choice = input(f"\nUpload {file_path} to YouTube? (y/N): ").strip().lower()
    if youtube_choice == 'y':
        youtube_creds = input("Enter YouTube credentials path (default: /home/nizar/my-secrets-files/nizar-youtube-creds.json): ").strip()
        if not youtube_creds:
            youtube_creds = '/home/nizar/my-secrets-files/nizar-youtube-creds.json'
        
        youtube_title = input(f"Enter YouTube title (default: {file_name}): ").strip()
        if not youtube_title:
            youtube_title = file_name
        
        privacy = input("Enter privacy setting (private/public/unlisted, default: private): ").strip().lower()
        if privacy not in ['private', 'public', 'unlisted']:
            privacy = 'private'
        
        youtube_token = os.path.join(file_dir, 'youtube_token.json')
        
        print(f"Uploading {file_path} to YouTube...")
        upload_to_youtube(file_path, youtube_title, "", privacy, youtube_creds, youtube_token)
    
    # Google Drive upload
    gdrive_choice = input(f"\nUpload {file_path} to Google Drive? (y/N): ").strip().lower()
    if gdrive_choice == 'y':
        gdrive_creds = input("Enter Google Drive credentials path (default: /home/nizar/my-secrets-files/nizar-gdrive-creds.json): ").strip()
        if not gdrive_creds:
            gdrive_creds = '/home/nizar/my-secrets-files/nizar-gdrive-creds.json'
        
        gdrive_token = os.path.join(file_dir, 'gdrive_token.json')
        
        print(f"Uploading {file_path} to Google Drive...")
        upload_to_gdrive(file_path, gdrive_creds, gdrive_token)

if __name__ == "__main__":
    main()
