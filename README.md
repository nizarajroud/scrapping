# Google Drive File Uploader

Simple Python script to upload files to Google Drive using the Google Drive API.

## Setup

### 1. Get Google Drive API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Drive API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Choose "Desktop application"
6. Download the JSON file and rename it to `credentials.json`
7. Place `credentials.json` in the same directory as the script

### 2. Install Dependencies

The script will automatically install required packages:
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib

## Usage

```bash
# Basic usage
python google_drive_uploader.py <file_path>

# With custom credentials file
python google_drive_uploader.py <file_path> <credentials_path>
```

### Examples

```bash
# Upload a single file
python google_drive_uploader.py combined_reels.mp3

# Upload with custom credentials location
python google_drive_uploader.py video.mp4 /path/to/credentials.json
```

## First Run

On first run, the script will:
1. Open your browser for Google authentication
2. Create a `token.json` file for future runs
3. Upload your file

## Notes

- Files are uploaded to the root of your Google Drive
- The script requires internet connection
- Authentication token is saved locally for subsequent runs
# scrapping
