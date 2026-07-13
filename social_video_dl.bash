#!/bin/bash

# Universal Video Downloader Setup and Interactive Script for WSL Ubuntu 22 with ZSH
# This script handles installation, setup, and provides fuzzy selection for YouTube and Facebook video downloads



set -e  # Exit on any error

# Load specific variables from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
    RUNNING_TODO_PATH=$(grep -E '^RUNNING_TODO_PATH=' "$SCRIPT_DIR/.env" | cut -d= -f2- | tr -d '"')
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_note() {
    echo -e "${PURPLE}[NOTE]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if running in WSL
check_wsl() {
    if grep -qE "(Microsoft|WSL)" /proc/version 2>/dev/null; then
        log_success "Running in WSL environment"
        return 0
    else
        log_warning "Not running in WSL, but continuing anyway"
        return 1
    fi
}

# Step 1: Update system
update_system() {
    log_info "Step 1: Updating system packages..."
    if sudo apt update && sudo apt upgrade -y; then
        log_success "System updated successfully"
        return 0
    else
        log_error "Failed to update system"
        return 1
    fi
}

# Step 2: Install Python and pip
install_python() {
    log_info "Step 2: Installing Python and pip..."
    
    if command_exists python3 && command_exists pip3; then
        log_success "Python3 and pip3 already installed"
        python3 --version
        pip3 --version
        return 0
    fi
    
    if sudo apt install python3 python3-pip -y; then
        log_success "Python3 and pip3 installed successfully"
        python3 --version
        pip3 --version
        return 0
    else
        log_error "Failed to install Python3 and pip3"
        return 1
    fi
}

# Step 3: Install yt-dlp
install_ytdlp() {
    log_info "Step 3: Installing yt-dlp..."
    
    if command_exists yt-dlp; then
        log_success "yt-dlp already installed"
        yt-dlp --version
        return 0
    fi
    
    # Try pip3 installation first
    if pip3 install --user yt-dlp; then
        log_success "yt-dlp installed via pip3"
        # Add ~/.local/bin to PATH if not already there
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
            export PATH="$HOME/.local/bin:$PATH"
            log_info "Added ~/.local/bin to PATH"
        fi
        yt-dlp --version
        return 0
    else
        # Fallback to apt installation
        log_warning "pip3 installation failed, trying apt..."
        if sudo apt install yt-dlp -y; then
            log_success "yt-dlp installed via apt"
            yt-dlp --version
            return 0
        else
            log_error "Failed to install yt-dlp"
            return 1
        fi
    fi
}

# Step 4: Install ffmpeg
install_ffmpeg() {
    log_info "Step 4: Installing ffmpeg..."
    
    if command_exists ffmpeg; then
        log_success "ffmpeg already installed"
        ffmpeg -version | head -1
        return 0
    fi
    
    if sudo apt install ffmpeg -y; then
        log_success "ffmpeg installed successfully"
        ffmpeg -version | head -1
        return 0
    else
        log_error "Failed to install ffmpeg"
        return 1
    fi
}

# Step 5: Install fzf for fuzzy selection
install_fzf() {
    log_info "Step 5: Installing fzf for fuzzy selection..."
    
    if command_exists fzf; then
        log_success "fzf already installed"
        return 0
    fi
    
    if sudo apt install fzf -y; then
        log_success "fzf installed successfully"
        return 0
    else
        log_error "Failed to install fzf"
        return 1
    fi
}

# Step 6: Install additional dependencies for Facebook and other platforms
install_additional_deps() {
    log_info "Step 6: Installing additional dependencies for Facebook and other platforms..."
    
    # Install Python packages for better Facebook support
    if pip3 install --user requests beautifulsoup4 lxml selenium gallery-dl; then
        log_success "Additional Python packages installed"
        return 0
    else
        log_warning "Some additional packages failed to install, continuing anyway"
        return 0
    fi
}

# Step 7: Setup aliases
setup_alias() {
    log_info "Step 7: Setting up convenient aliases..."
    
    # Setup yt-dlp alias
    if grep -q "alias ytdl=" ~/.zshrc 2>/dev/null; then
        log_success "ytdl alias already exists in ~/.zshrc"
    else
        echo 'alias ytdl="yt-dlp"' >> ~/.zshrc
        log_success "Added ytdl alias to ~/.zshrc"
    fi
    
    # Setup gallery-dl alias for social media
    if grep -q "alias gdl=" ~/.zshrc 2>/dev/null; then
        log_success "gdl alias already exists in ~/.zshrc"
    else
        echo 'alias gdl="gallery-dl"' >> ~/.zshrc
        log_success "Added gdl alias to ~/.zshrc"
    fi
    
    # Create aliases for current session
    alias ytdl="yt-dlp"
    alias gdl="gallery-dl"
}

# Enhanced URL validation for multiple platforms
validate_url() {
    local url="$1"
    if [[ $url =~ ^https?://(www\.)?(youtube\.com|youtu\.be) ]]; then
        echo "youtube"
        return 0
    elif [[ $url =~ ^https?://(www\.|m\.)?(facebook\.com|fb\.watch) ]]; then
        echo "facebook"
        return 0
    elif [[ $url =~ ^https?://(www\.)?(instagram\.com|twitter\.com|tiktok\.com) ]]; then
        echo "social"
        return 0
    else
        echo "unknown"
        return 1
    fi
}

# Get video info with platform detection
get_video_info() {
    local url="$1"
    local platform="$2"
    
    log_info "Getting video information for $platform..."
    
    case $platform in
        "youtube")
            yt-dlp --get-title --get-duration --get-filename "$url" 2>/dev/null || {
                log_error "Failed to get YouTube video information"
                return 1
            }
            ;;
        "facebook")
            log_note "Facebook videos may require authentication for full info"
            yt-dlp --get-title "$url" 2>/dev/null || {
                log_warning "Limited info available - may need cookies for private content"
                echo "Facebook Video (title unavailable without auth)"
            }
            ;;
        "social"|*)
            yt-dlp --get-title "$url" 2>/dev/null || {
                log_warning "Limited info available for this platform"
                echo "Video from $(echo "$url" | cut -d'/' -f3)"
            }
            ;;
    esac
}

# Download menu with FZF
download_menu() {
    local url="$1"
    local platform="$2"
    local options=()
    
    options+=(
        "best_quality:Download best quality video"
        "720p:Download 720p video"
        "480p:Download 480p video"
        "audio_mp3:Download audio as MP3"
        "audio_best:Download best quality audio"
        "list_formats:List available formats"
    )
    
    case $platform in
        "youtube")
            options+=(
                "playlist:Download entire playlist"
                "browser_cookies:Download with browser cookies (private playlists)"
                "browser_cookies_audio:Playlist audio MP3 (with browser cookies)"
                "subtitles:Download with subtitles"
                "thumbnail:Download with thumbnail"
            )
            ;;
        "facebook")
            options+=(
                "with_cookies:Download using cookies (for private content)"
                "thumbnail:Download with thumbnail"
                "metadata:Download with metadata"
                "gallery_dl:Use gallery-dl instead of yt-dlp"
            )
            ;;
        "social"|*)
            options+=(
                "with_cookies:Download using cookies"
                "gallery_dl:Use gallery-dl (better for social media)"
                "thumbnail:Download with thumbnail"
            )
            ;;
    esac
    
    local labels=()
    for option in "${options[@]}"; do
        labels+=("${option#*:}")
    done
    
    local selected_label=$(printf "%s\n" "${labels[@]}" | fzf --prompt="Download option ($platform): " --height=$((${#labels[@]} + 3)) --border)
    [[ -z "$selected_label" ]] && return
    
    for option in "${options[@]}"; do
        if [[ "${option#*:}" == "$selected_label" ]]; then
            echo "${option%%:*}"
            return
        fi
    done
}

download_menu_interactive() {
    local url="$1"
    local platform="$2"
    
    local choice=$(download_menu "$url" "$platform")
    if [[ -n "$choice" ]]; then
        perform_download "$url" "$choice" "$platform"
    else
        log_warning "No option selected"
    fi
}

# Cookie management functions
setup_cookies() {
    local platform="$1"
    local cookie_file="$HOME/.config/${platform}_cookies.txt"
    
    log_info "Setting up cookies for $platform..."
    log_note "To download private content, you need to export cookies from your browser:"
    log_note "1. Install 'Get cookies.txt LOCALLY' browser extension"
    log_note "2. Visit $platform and login"
    log_note "3. Export cookies and save as: $cookie_file"
    
    if [[ -f "$cookie_file" ]]; then
        log_success "Cookie file found: $cookie_file"
        echo "$cookie_file"
        return 0
    else
        log_warning "No cookie file found. Create one for private content access."
        echo ""
        return 1
    fi
}

# Enhanced download functions
download_best_quality() {
    local url="$1"
    local cookies="$2"
    log_info "Downloading best quality video..."
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" "$url"
    else
        yt-dlp "$url"
    fi
}

download_720p() {
    local url="$1"
    local cookies="$2"
    log_info "Downloading 720p video..."
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" -f "best[height<=720]" "$url"
    else
        yt-dlp -f "best[height<=720]" "$url"
    fi
}

download_480p() {
    local url="$1"
    local cookies="$2"
    log_info "Downloading 480p video..."
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" -f "best[height<=480]" "$url"
    else
        yt-dlp -f "best[height<=480]" "$url"
    fi
}

download_audio_mp3() {
    local url="$1"
    local cookies="$2"
    log_info "Downloading audio as MP3..."
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" -x --audio-format mp3 "$url"
    else
        yt-dlp -x --audio-format mp3 "$url"
    fi
}

download_audio_best() {
    local url="$1"
    local cookies="$2"
    log_info "Downloading best quality audio..."
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" -x "$url"
    else
        yt-dlp -x "$url"
    fi
}

download_playlist() {
    local url="$1"
    local cookies="$2"
    log_info "Downloading entire playlist..."
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" "$url"
    else
        yt-dlp "$url"
    fi
}

download_with_subtitles() {
    local url="$1"
    local cookies="$2"
    log_info "Downloading with subtitles..."
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" --write-subs --sub-lang en "$url"
    else
        yt-dlp --write-subs --sub-lang en "$url"
    fi
}

download_with_thumbnail() {
    local url="$1"
    local cookies="$2"
    log_info "Downloading with thumbnail..."
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" --write-thumbnail "$url"
    else
        yt-dlp --write-thumbnail "$url"
    fi
}

download_with_metadata() {
    local url="$1"
    local cookies="$2"
    log_info "Downloading with metadata..."
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" --write-info-json --write-description "$url"
    else
        yt-dlp --write-info-json --write-description "$url"
    fi
}

download_with_cookies() {
    local url="$1"
    local platform="$2"
    local cookie_file
    
    cookie_file=$(setup_cookies "$platform")
    if [[ -n "$cookie_file" && -f "$cookie_file" ]]; then
        log_info "Downloading with cookies..."
        yt-dlp --cookies "$cookie_file" "$url"
    else
        log_error "Cookie file not found. Please set up cookies first."
        return 1
    fi
}

download_gallery_dl() {
    local url="$1"
    log_info "Using gallery-dl for download..."
    if command_exists gallery-dl; then
        gallery-dl "$url"
    else
        log_error "gallery-dl not installed"
        return 1
    fi
}

download_custom_dir() {
    local url="$1"
    local cookies="$2"
    
    local location=$(printf "Backlog\nOther location" | fzf --prompt="Save location: " --height=~100% --border)
    
    local custom_dir
    case "$location" in
        "Running Backlog")
            custom_dir="${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING/1-BACKLOG}"
            ;;
        "Other location")
            echo -n "Enter download directory: "
            read -r custom_dir
            if [[ -z "$custom_dir" ]]; then
                log_warning "No directory provided, using Running Backlog"
                custom_dir="${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING/1-BACKLOG}"
            fi
            ;;
        *)
            log_warning "No selection, using Running Backlog"
            custom_dir="${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING/1-BACKLOG}"
            ;;
    esac
    
    mkdir -p "$custom_dir"
    
    log_info "Downloading to $custom_dir..."
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" -o "$custom_dir/%(title)s.%(ext)s" "$url"
    else
        yt-dlp -o "$custom_dir/%(title)s.%(ext)s" "$url"
    fi
}

list_formats() {
    local url="$1"
    local cookies="$2"
    log_info "Available formats:"
    if [[ -n "$cookies" && -f "$cookies" ]]; then
        yt-dlp --cookies "$cookies" -F "$url"
    else
        yt-dlp -F "$url"
    fi
}

# Enhanced download performer
perform_download() {
    local url="$1"
    local choice="$2"
    local platform="$3"
    local cookies=""
    
    # Set up cookies if needed
    local cookie_file="$HOME/.config/${platform}_cookies.txt"
    if [[ -f "$cookie_file" ]]; then
        cookies="$cookie_file"
    fi
    
    # Choose download location (skip for non-download actions)
    local dl_dir=""
    if [[ "$choice" != "list_formats" ]]; then
        local location=$(printf "Backlog\nOther location" | fzf --prompt="Save location: " --height=~100% --border)
        case "$location" in
            "Running Backlog")
                dl_dir="${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING/1-BACKLOG}"
                ;;
            "Other location")
                echo -n "Enter download directory: "
                read -r dl_dir
                ;;
        esac
        dl_dir="${dl_dir:-${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING/1-BACKLOG}}"
        mkdir -p "$dl_dir"
        log_info "Downloading to $dl_dir..."
    fi
    
    # Build output and cookie args
    local -a out_args=(--remote-components ejs:github --no-warnings)
    [[ -n "$dl_dir" ]] && out_args+=(-o "$dl_dir/%(title)s.%(ext)s")
    [[ -n "$cookies" && -f "$cookies" ]] && out_args+=(--cookies "$cookies")
    
    case $choice in
        "best_quality") yt-dlp "${out_args[@]}" "$url" ;;
        "720p") yt-dlp "${out_args[@]}" -f "best[height<=720]" "$url" ;;
        "480p") yt-dlp "${out_args[@]}" -f "best[height<=480]" "$url" ;;
        "audio_mp3") yt-dlp "${out_args[@]}" -x --audio-format mp3 "$url" ;;
        "audio_best") yt-dlp "${out_args[@]}" -x "$url" ;;
        "playlist") yt-dlp "${out_args[@]}" "$url" ;;
        "browser_cookies") yt-dlp "${out_args[@]}" --cookies-from-browser chrome "$url" ;;
        "browser_cookies_audio") yt-dlp "${out_args[@]}" --cookies-from-browser chrome -x --audio-format mp3 "$url" ;;
        "subtitles") yt-dlp "${out_args[@]}" --write-subs --sub-lang en "$url" ;;
        "thumbnail") yt-dlp "${out_args[@]}" --write-thumbnail "$url" ;;
        "metadata") yt-dlp "${out_args[@]}" --write-info-json --write-description "$url" ;;
        "with_cookies") download_with_cookies "$url" "$platform" ;;
        "gallery_dl") download_gallery_dl "$url" ;;
        "list_formats") list_formats "$url" "$cookies" ;;
        *) log_error "Invalid choice" ;;
    esac
}

# Main setup function
setup_environment() {
    log_info "Starting Universal Video Downloader setup..."
    
    check_wsl
    
    # Run setup steps
    update_system || { log_error "Setup failed at system update"; exit 1; }
    install_python || { log_error "Setup failed at Python installation"; exit 1; }
    install_ytdlp || { log_error "Setup failed at yt-dlp installation"; exit 1; }
    install_ffmpeg || { log_error "Setup failed at ffmpeg installation"; exit 1; }
    install_fzf || { log_error "Setup failed at fzf installation"; exit 1; }
    install_additional_deps || log_warning "Some additional dependencies failed to install"
    setup_alias
    
    # Create config directory for cookies
    mkdir -p "$HOME/.config"
    
    log_success "All components installed successfully!"
    log_info "Please run 'source ~/.zshrc' or restart your terminal to use the aliases"
    log_note "For Facebook/private content: Set up cookies using browser extensions"
}

combine_audio_files() {
    echo -n "Enter folder containing audio files (or press Enter for Running Backlog): "
    read -r src_dir
    src_dir="${src_dir:-${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING/1-BACKLOG}}"
    
    if [ ! -d "$src_dir" ]; then
        log_error "Directory not found: $src_dir"
        return 1
    fi
    
    local count=$(find "$src_dir" -maxdepth 1 -name "*.mp3" | wc -l)
    if [ "$count" -eq 0 ]; then
        log_error "No MP3 files found in $src_dir"
        return 1
    fi
    
    log_info "Found $count MP3 files in $src_dir"
    
    echo -n "Output filename (without extension): "
    read -r output_name
    output_name="${output_name:-combined}"
    local output_file="$src_dir/${output_name}.mp3"
    
    # Create concat list
    local list_file=$(mktemp)
    find "$src_dir" -maxdepth 1 -name "*.mp3" -print0 | sort -z | while IFS= read -r -d '' f; do
        echo "file '$(realpath "$f")'" >> "$list_file"
    done
    
    log_info "Combining into: $output_file"
    if ffmpeg -f concat -safe 0 -i "$list_file" -c copy -y "$output_file" 2>/dev/null; then
        log_success "Combined $count files into: $output_file"
    else
        log_error "Failed to combine files"
    fi
    rm -f "$list_file"
}

interactive_mode() {
    echo
    local main_choice=$(printf "Download from URL\nCombine audio files\nCheck installation status\nUpdate yt-dlp and gallery-dl\nSetup cookies for platform\nExit" | fzf --prompt="Video Downloader: " --height=~100% --border)
    
    case "$main_choice" in
        "Download from URL")
            echo -n "Enter video URL: "
            read -r url
            
            platform=$(validate_url "$url")
            if [[ $? -eq 0 ]]; then
                log_success "Valid $platform URL detected"
                get_video_info "$url" "$platform"
                echo
                download_menu_interactive "$url" "$platform"
            else
                log_error "Invalid or unsupported URL"
            fi
            ;;
        "Combine audio files")
            combine_audio_files
            ;;
        "Check installation status")
            log_info "Checking installation status..."
            command_exists yt-dlp && log_success "yt-dlp: $(yt-dlp --version)" || log_error "yt-dlp: Not installed"
            command_exists ffmpeg && log_success "ffmpeg: Installed" || log_error "ffmpeg: Not installed"
            command_exists fzf && log_success "fzf: Installed" || log_error "fzf: Not installed"
            command_exists gallery-dl && log_success "gallery-dl: Installed" || log_warning "gallery-dl: Not installed"
            ;;
        "Update yt-dlp and gallery-dl")
            log_info "Updating video downloaders..."
            pip3 install --upgrade yt-dlp gallery-dl --user && log_success "Downloaders updated" || log_error "Failed to update"
            ;;
        "Setup cookies for platform")
            local platform=$(printf "facebook\ninstagram\ntwitter\ntiktok" | fzf --prompt="Select platform: " --height=~100% --border)
            [[ -n "$platform" ]] && setup_cookies "$platform"
            ;;
        "Exit"|"")
            log_info "Goodbye!"
            ;;
    esac
}

# Main script logic
main() {
    # Check if setup is needed
    if ! command_exists yt-dlp || ! command_exists ffmpeg || ! command_exists fzf; then
        log_warning "Some components are missing. Running setup..."
        setup_environment
        echo
        log_info "Setup complete! Starting interactive mode..."
        echo
    fi
    
    # If URL provided as argument, use it directly
    if [[ $# -gt 0 ]]; then
        url="$1"
        platform=$(validate_url "$url")
        if [[ $? -eq 0 ]]; then
            get_video_info "$url" "$platform"
            choice=$(download_menu "$url" "$platform")
            [[ -n "$choice" ]] && perform_download "$url" "$choice" "$platform"
        else
            log_error "Invalid or unsupported URL provided"
            exit 1
        fi
    else
        # Run interactive mode
        interactive_mode
    fi
}

# Run main function with all arguments
main "$@"
