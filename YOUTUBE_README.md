# YouTube Video Uploader

Simple Python script to upload videos to YouTube using the YouTube Data API.

## Setup

### 1. Get YouTube API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the YouTube Data API v3
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Choose "Desktop application"
6. Download the JSON file and rename it to `credentials.json`
7. Place `credentials.json` in the same directory as the script

### 2. YouTube Channel Setup

- You need a verified YouTube channel
- For testing: Add your email as a test user in OAuth consent screen
- For production: Publish the app (requires Google verification)

### 3. Install Dependencies

The script will automatically install required packages:
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib

## Usage

```bash
# Basic usage (private upload)
python youtube_uploader.py <video_path>

# With custom title
python youtube_uploader.py video.mp4 "My Video Title"

# With privacy setting
python youtube_uploader.py video.mp4 "My Video" public
```

### Privacy Options

- `private` - Only you can see (default)
- `public` - Everyone can see
- `unlisted` - Only people with link can see

### Examples

```bash
# Upload as private video
python youtube_uploader.py combined_reels.mp4

# Upload with custom title and make public
python youtube_uploader.py my_video.mp4 "Amazing Content" public

# Upload as unlisted
python youtube_uploader.py presentation.mp4 "My Presentation" unlisted
```

## First Run

On first run, the script will:
1. Open your browser for Google authentication
2. Create a `youtube_token.json` file for future runs
3. Upload your video

## Notes

- Videos are uploaded to your YouTube channel
- Default category is "People & Blogs"
- Authentication token is saved locally for subsequent runs
- Requires internet connection
- Large videos may take time to upload and process
