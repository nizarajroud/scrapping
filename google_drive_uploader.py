#!/usr/bin/env python3
"""
Google Drive File Uploader
Minimal script to upload files to Google Drive
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

def upload_file(file_path, credentials_path='credentials.json', token_path='token.json'):
    """Upload file to Google Drive"""
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.http import MediaFileUpload
        
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        
        # Use OAuth flow only
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    print(f"❌ {credentials_path} not found")
                    print("Please create OAuth 2.0 credentials (not service account) from Google Cloud Console")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=8080)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': os.path.basename(file_path)}
        media = MediaFileUpload(file_path, resumable=True)
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"✓ Uploaded: {os.path.basename(file_path)} (ID: {file.get('id')})")
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def main():
    default_file = "/mnt/c/Users/ben0711b/DOCS/PERSO/scrap/combined_reels.mp3"
    
    if len(sys.argv) < 2:
        confirm = input(f"Upload {default_file}? (Y/n): ").lower().strip()
        if confirm == 'n':
            file_path = input("Enter file path: ").strip()
        else:
            file_path = default_file
        credentials_path = '/home/nizar/my-secrets-files/nizar-ajroud-gdrive-creds.json'
    else:
        file_path = sys.argv[1]
        credentials_path = sys.argv[2] if len(sys.argv) > 2 else '/home/nizar/my-secrets-files/nizar-ajroud-gdrive-creds.json'
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    print("Installing dependencies...")
    install_dependencies()
    
    print(f"Uploading {file_path} to Google Drive...")
    upload_file(file_path, credentials_path)

if __name__ == "__main__":
    main()
