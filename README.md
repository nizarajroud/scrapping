# Facebook Reels Scraper & Multi-Platform Uploader

## Main Features

- **Scrape Facebook Reels**: Automatically extracts reel URLs from Facebook pages using Selenium
- **Download Videos**: Downloads reels using yt-dlp with quality selection
- **Combine Videos**: Merges multiple reels into a single video file using FFmpeg
- **Multi-Platform Upload**: Uploads combined videos to:
  - Google Drive
  - YouTube (with metadata)

## Usage

```bash
python3 scrap-dowload-combine-upload-fb-reels.py
```

## Requirements

- Facebook credentials in `~/.my-secrets` file
- Chrome browser
- FFmpeg installed
- Google API credentials for Drive/YouTube upload

## Workflow

1. Enter Facebook reels page URL
2. Provide name for combined video
3. Choose output directory
4. Script automatically:
   - Logs into Facebook
   - Scrapes reel URLs
   - Downloads videos
   - Combines them into one file
   - Uploads to Google Drive and YouTube
