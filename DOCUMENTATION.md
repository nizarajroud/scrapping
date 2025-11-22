# Facebook Reels Scraper & Multi-Platform Uploader - Complete Documentation

## Project Overview

This project is a comprehensive automation tool for scraping Facebook Reels, downloading videos, combining them, and uploading to multiple platforms (Google Drive and YouTube). It uses modern web automation with Playwright and provides both interactive and batch processing capabilities.

## Architecture

```
scrapping/
├── Core Scripts
│   ├── scrap-dowload-combine-upload-fb-reels-playwright.py  # Main automation script
│   ├── upload-to-platforms.py                              # Standalone uploader
│   └── setup_chrome_user_data_dir.py                      # Chrome profile setup
├── Utilities
│   ├── download-youtube-fb-tiktk-etc-videos.bash          # Universal video downloader
│   └── setup_gcloud_drive.sh                              # Google Cloud setup
├── Configuration
│   ├── .env                                               # Environment variables
│   └── .gitignore                                         # Git ignore rules
└── Documentation
    ├── readme.md                                          # Basic usage guide
    └── DOCUMENTATION.md                                   # This comprehensive guide
```

## Core Components

### 1. Main Automation Script (`scrap-dowload-combine-upload-fb-reels-playwright.py`)

**Purpose**: Complete end-to-end automation for Facebook Reels processing

**Key Functions**:
- `install_playwright()`: Installs Playwright browser automation
- `install_ytdlp()`: Installs yt-dlp video downloader
- `install_google_dependencies()`: Installs Google API packages
- `check_ffmpeg()`: Verifies FFmpeg installation
- `get_reel_links()`: Scrapes Facebook page for reel URLs using Playwright
- `download_facebook_reel()`: Downloads individual reels using yt-dlp
- `upload_to_gdrive()`: Uploads files to Google Drive
- `upload_to_youtube()`: Uploads videos to YouTube with metadata
- `main()`: Orchestrates the complete workflow

**Workflow**:
1. Dependency installation and verification
2. User input collection (Facebook URL, video name, output directory)
3. Facebook login and reel URL extraction
4. Batch video downloading
5. Video combination using FFmpeg
6. Multi-platform upload (Google Drive + YouTube)

### 2. Platform Uploader (`upload-to-platforms.py`)

**Purpose**: Standalone utility for uploading existing videos to platforms

**Key Functions**:
- `install_google_dependencies()`: Google API setup
- `upload_to_gdrive()`: Google Drive upload with OAuth2
- `upload_to_youtube()`: YouTube upload with metadata and privacy settings
- `main()`: Command-line interface for file uploads

**Usage**:
```bash
python3 upload-to-platforms.py /path/to/video.mp4
```

### 3. Chrome Profile Setup (`setup_chrome_user_data_dir.py`)

**Purpose**: Creates persistent Chrome user data directory for authenticated sessions

**Features**:
- Uses NovaAct framework
- Maintains login sessions across runs
- Supports manual website authentication

**Usage**:
```bash
python setup_chrome_user_data_dir.py --user_data_dir <directory>
```

### 4. Universal Video Downloader (`download-youtube-fb-tiktk-etc-videos.bash`)

**Purpose**: Comprehensive bash script for downloading videos from multiple platforms

**Features**:
- WSL Ubuntu 22 with ZSH support
- Interactive fuzzy selection interface
- Multi-platform support (YouTube, Facebook, TikTok, etc.)
- Automatic dependency installation
- Color-coded logging system

**Key Functions**:
- `command_exists()`: Checks command availability
- `check_wsl()`: WSL environment detection
- `log_*()`: Colored logging functions
- Dependency management for yt-dlp, ffmpeg, fzf

### 5. Google Cloud Setup (`setup_gcloud_drive.sh`)

**Purpose**: Automated Google Cloud project setup for Drive API access

**Features**:
- Creates Google Cloud project
- Enables Drive API
- Sets up OAuth2 credentials
- Opens browser for manual credential creation

**Usage**:
```bash
./setup_gcloud_drive.sh "Project Name" "email@example.com"
```

## Dependencies

### Python Packages
- `playwright`: Web automation
- `yt-dlp`: Video downloading
- `google-api-python-client`: Google APIs
- `google-auth-httplib2`: Google authentication
- `google-auth-oauthlib`: OAuth2 flow
- `fire`: Command-line interface (for Chrome setup)
- `python-dotenv`: Environment variable management

### System Requirements
- **FFmpeg**: Video processing and combination
- **Chrome/Chromium**: Web automation browser
- **Python 3.7+**: Runtime environment
- **Google Cloud CLI**: For API setup

### Platform-Specific
- **WSL Ubuntu 22**: Recommended environment
- **ZSH**: Shell support in bash script
- **fzf**: Fuzzy finder for interactive selection

## Configuration

### Environment Variables (`.env`)
```bash
USER_DATA_DIR=/home/nizar/Clone-Chrome-profile/User Data
```

### Secrets Management
- Facebook credentials: `~/.my-secrets` file
- Google credentials: JSON files in `~/my-secrets-files/`
- OAuth tokens: `token.json`, `youtube_token.json`

### Git Ignore (`.gitignore`)
```
token.json
youtube_token.json
credentials.json
*.json
versions
zzz
```

## Installation & Setup

### 1. System Dependencies
```bash
# Install FFmpeg
sudo apt update
sudo apt install ffmpeg

# Install Chrome (if not present)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install google-chrome-stable
```

### 2. Python Environment
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies (handled automatically by scripts)
python3 scrap-dowload-combine-upload-fb-reels-playwright.py
```

### 3. Google API Setup
```bash
# Run Google Cloud setup
./setup_gcloud_drive.sh "My Project" "your-email@gmail.com"

# Follow manual steps for OAuth2 credential creation
```

### 4. Facebook Credentials
Create `~/.my-secrets` file with Facebook login credentials:
```
username:your-facebook-email
password:your-facebook-password
```

## Usage Examples

### Complete Workflow
```bash
# Run main automation script
python3 scrap-dowload-combine-upload-fb-reels-playwright.py

# Follow interactive prompts:
# 1. Enter Facebook reels page URL
# 2. Provide combined video name
# 3. Choose output directory
# 4. Wait for automated processing
```

### Standalone Upload
```bash
# Upload existing video
python3 upload-to-platforms.py /path/to/my-video.mp4
```

### Universal Video Download
```bash
# Interactive video downloader
./download-youtube-fb-tiktk-etc-videos.bash
```

### Chrome Profile Setup
```bash
# Set up persistent Chrome profile
python setup_chrome_user_data_dir.py --user_data_dir /path/to/profile
```

## Features

### Web Scraping
- **Playwright Integration**: Modern, reliable web automation
- **Dynamic Content Handling**: Scrolling and lazy-loading support
- **Rate Limiting**: Configurable delays and scroll limits
- **Error Recovery**: Robust error handling and retries

### Video Processing
- **Multi-Format Support**: Handles various video formats
- **Quality Selection**: Configurable download quality
- **Batch Processing**: Multiple video handling
- **FFmpeg Integration**: Professional video combination

### Platform Integration
- **Google Drive**: Automated file upload with OAuth2
- **YouTube**: Video upload with metadata and privacy settings
- **Multi-Platform**: Simultaneous uploads to multiple services

### User Experience
- **Interactive Interface**: User-friendly prompts and feedback
- **Progress Tracking**: Real-time operation status
- **Error Reporting**: Detailed error messages and recovery suggestions
- **Logging**: Comprehensive operation logging

## Security Considerations

### Credential Management
- Credentials stored in separate files outside project directory
- OAuth2 tokens with proper scoping
- Git ignore for sensitive files

### Web Automation
- User data directory isolation
- Rate limiting to avoid detection
- Proper session management

### API Security
- Scoped Google API permissions
- Token refresh handling
- Secure credential storage

## Troubleshooting

### Common Issues

**1. Playwright Installation Fails**
```bash
# Manual installation
pip install playwright
playwright install chromium
```

**2. FFmpeg Not Found**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Check installation
ffmpeg -version
```

**3. Google API Authentication Errors**
- Verify credentials.json file exists
- Check OAuth2 consent screen configuration
- Ensure proper API scopes

**4. Facebook Login Issues**
- Update credentials in ~/.my-secrets
- Clear browser cache/cookies
- Check for CAPTCHA requirements

### Debug Mode
Enable verbose logging by modifying scripts to include debug output.

## Performance Optimization

### Scraping Efficiency
- Adjust scroll delays based on network speed
- Limit maximum scrolls for large pages
- Use headless mode when possible

### Download Optimization
- Parallel downloads for multiple videos
- Quality selection based on requirements
- Resume capability for interrupted downloads

### Upload Optimization
- Chunked uploads for large files
- Retry logic for network issues
- Progress tracking and resumption

## Extension Points

### Adding New Platforms
1. Create platform-specific upload function
2. Add authentication handling
3. Integrate into main workflow
4. Update configuration options

### Custom Video Processing
1. Extend FFmpeg command generation
2. Add custom filters and effects
3. Support additional output formats
4. Implement quality optimization

### Enhanced Scraping
1. Support additional social media platforms
2. Add content filtering options
3. Implement advanced selectors
4. Add metadata extraction

## Maintenance

### Regular Updates
- Keep dependencies updated
- Monitor API changes
- Update browser automation selectors
- Refresh authentication tokens

### Monitoring
- Log file analysis
- Error rate tracking
- Performance metrics
- Success rate monitoring

## License & Legal

### Usage Compliance
- Respect platform terms of service
- Follow rate limiting guidelines
- Obtain proper permissions for content
- Comply with copyright regulations

### Data Privacy
- Handle user credentials securely
- Minimize data collection
- Implement proper data retention
- Follow privacy best practices

---

*Last Updated: November 22, 2025*
*Version: 1.0*
