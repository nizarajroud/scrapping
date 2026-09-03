#!/bin/bash

# Universal Video Downloader Setup and Interactive Script for WSL Ubuntu 22 with ZSH
# This script handles installation, setup, and provides fuzzy selection for YouTube and Facebook video downloads



set -e  # Exit on any error

# Load specific variables from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
    RUNNING_TODO_PATH=$(grep -E '^RUNNING_TODO_PATH=' "$SCRIPT_DIR/.env" | cut -d= -f2- | tr -d '"')
    DAILY_PATH=$(grep -E '^DAILY_PATH=' "$SCRIPT_DIR/.env" | cut -d= -f2- | tr -d '"')
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

# Convert Windows path to WSL path if needed (e.g. D:\ZZZ -> /mnt/d/ZZZ)
win_to_wsl_path() {
    local path="$1"
    if [[ "$path" =~ ^([A-Za-z]):[/\\] ]]; then
        local drive="${BASH_REMATCH[1]}"
        drive=$(echo "$drive" | tr '[:upper:]' '[:lower:]')
        path="/mnt/$drive/${path:3}"
        path="${path//\\//}"
    fi
    echo "$path"
}

download_custom_dir() {
    local url="$1"
    local cookies="$2"
    
    local location=$(printf "Running Backlog\nDaily\nOther location" | fzf --prompt="Save location: " --height=~100% --border)
    
    local custom_dir
    case "$location" in
        "Running")
            custom_dir="${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING}"
            ;;
        "Daily")
            custom_dir="${DAILY_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/DAILY}"
            ;;
        "Other location")
            echo -n "Enter download directory: "
            read -r custom_dir
            if [[ -z "$custom_dir" ]]; then
                log_warning "No directory provided, using Running"
                custom_dir="${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING}"
            else
                custom_dir=$(win_to_wsl_path "$custom_dir")
            fi
            ;;
        *)
            log_warning "No selection, using Running"
            custom_dir="${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING}"
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

# Combine all downloaded playlist items (Ep-XX.*) into a single file
# named after the playlist. On success, deletes the individual Ep-XX files.
combine_playlist_items() {
    local dl_dir="$1"
    local url="$2"

    log_info "Combining playlist items into a single file..."

    # Collect the downloaded Ep-XX files in numeric order
    local -a items=()
    while IFS= read -r f; do
        items+=("$f")
    done < <(find "$dl_dir" -maxdepth 1 -type f -name 'Ep-*' | sort -V)

    if [[ ${#items[@]} -eq 0 ]]; then
        log_error "No 'Ep-*' items found in $dl_dir — nothing to combine."
        return 1
    fi
    if [[ ${#items[@]} -eq 1 ]]; then
        log_warning "Only one item found — skipping combination."
        return 0
    fi

    log_info "Found ${#items[@]} items to combine (in order):"
    for f in "${items[@]}"; do log_note "  $(basename "$f")"; done

    # Resolve the playlist title for the output filename
    local playlist_title
    playlist_title=$(yt-dlp --no-warnings --flat-playlist --playlist-items 1 \
        --print "%(playlist_title)s" "$url" 2>/dev/null | head -n1)
    # Sanitize (strip filesystem-unfriendly characters); fallback if empty
    playlist_title=$(printf '%s' "$playlist_title" | tr -d '/\\:*?"<>|' | sed 's/[[:space:]]\+/ /g;s/^ //;s/ $//')
    [[ -z "$playlist_title" ]] && playlist_title="combined-$(date +%Y%m%d-%H%M%S)"

    # Derive output extension from the first item
    local ext="${items[0]##*.}"
    local output="$dl_dir/$playlist_title.$ext"

    # Build a concat-demuxer list file
    local list_file
    list_file=$(mktemp)
    for f in "${items[@]}"; do
        # Escape single quotes for ffmpeg concat syntax
        printf "file '%s'\n" "${f//\'/\'\\\'\'}" >> "$list_file"
    done

    # Fast path: stream copy (no re-encode) — works when all items share codecs
    log_info "Merging into: $(basename "$output") (stream copy)..."
    if ffmpeg -y -f concat -safe 0 -i "$list_file" -c copy "$output" >/dev/null 2>&1 && [[ -s "$output" ]]; then
        log_success "Combined file created: $output"
    else
        # Fallback: normalize & re-encode (robust for mixed AV1/VP9, 720p/1080p)
        log_warning "Stream copy failed — normalizing & re-encoding to .mp4 (slower)..."
        rm -f "$output"
        output="$dl_dir/$playlist_title.mp4"
        if _combine_reencode "$output" "true" "${items[@]}"; then
            :
        else
            log_error "ffmpeg failed to combine items. Individual files kept."
            rm -f "$list_file"
            return 1
        fi
    fi
    rm -f "$list_file"

    # Verify output is non-empty before deleting sources
    if [[ -s "$output" ]]; then
        log_info "Removing individual items..."
        for f in "${items[@]}"; do rm -f "$f"; done
        log_success "Done — kept only: $(basename "$output")"
    else
        log_error "Output file is empty — individual files kept for safety."
        return 1
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
    local filename_template="%(title)s.%(ext)s"
    local combine="no"
    if [[ "$choice" != "list_formats" ]]; then
        local location=$(printf "Running Backlog\nDaily\nOther location" | fzf --prompt="Save location: " --height=~100% --border)
        case "$location" in
            "Running")
                dl_dir="${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING}"
                ;;
            "Daily")
                dl_dir="${DAILY_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/DAILY}"
                ;;
            "Other location")
                echo -n "Enter download directory: "
                read -r dl_dir
                dl_dir=$(win_to_wsl_path "$dl_dir")
                ;;
        esac
        dl_dir="${dl_dir:-${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING}}"
        mkdir -p "$dl_dir"

        # For playlist modes: ask whether to combine all items into one file.
        # If yes, we force Ep-XX numbering (needed for correct concat order)
        # and skip the filename-format question entirely.
        if [[ "$choice" == "playlist" || "$choice" == "browser_cookies" ]]; then
            local combine_choice=$(printf "No\nYes" | fzf --prompt="Combine all items into one file after download? " --height=~100% --border)
            if [[ "$combine_choice" == "Yes" ]]; then
                combine="yes"
                filename_template="Ep-%(playlist_index)02d.%(ext)s"
                log_note "Combine mode ON — items will be merged into a single file named after the playlist."
            fi
        fi

        # Choose filename format (skipped when combine mode is on — Ep-XX is forced)
        if [[ "$combine" != "yes" ]]; then
            local name_format=$(printf "Original title\nEp-X (auto numbering)" | fzf --prompt="Filename format: " --height=~100% --border)
            if [[ "$name_format" == "Ep-X (auto numbering)" ]]; then
                filename_template="Ep-%(playlist_index)02d.%(ext)s"
            fi
        fi

        log_info "Downloading to $dl_dir..."
    fi
    
    # Build output and cookie args
    local -a out_args=(--remote-components ejs:github --no-warnings)
    [[ -n "$dl_dir" ]] && out_args+=(-o "$dl_dir/$filename_template")
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
    local dl_status=$?

    # If combine mode was requested, merge all downloaded items into one file
    if [[ "$combine" == "yes" && $dl_status -eq 0 ]]; then
        combine_playlist_items "$dl_dir" "$url"
    fi
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

combine_files() {
    echo -n "Enter folder containing files (or press Enter for Running Backlog): "
    read -r src_dir
    src_dir="${src_dir:-${RUNNING_TODO_PATH:-/mnt/g/Mon Drive/SOFTSKILLS/RUNNING/1-BACKLOG}}"
    src_dir=$(win_to_wsl_path "$src_dir")
    
    if [ ! -d "$src_dir" ]; then
        log_error "Directory not found: $src_dir"
        return 1
    fi
    
    # Detect media files
    local -a media_files=()
    while IFS= read -r -d '' f; do
        media_files+=("$f")
    done < <(find "$src_dir" -maxdepth 1 -type f \( -iname "*.mp3" -o -iname "*.mp4" -o -iname "*.webm" -o -iname "*.m4a" -o -iname "*.ogg" -o -iname "*.flac" -o -iname "*.wav" -o -iname "*.mkv" -o -iname "*.avi" -o -iname "*.mov" \) -print0 | sort -z)
    
    local count=${#media_files[@]}
    if [ "$count" -eq 0 ]; then
        log_error "No media files found in $src_dir"
        return 1
    fi
    
    # Detect if all files share same extension
    local -A ext_count=()
    for f in "${media_files[@]}"; do
        local ext="${f##*.}"
        ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
        ext_count[$ext]=$(( ${ext_count[$ext]:-0} + 1 ))
    done
    
    local extensions="${!ext_count[*]}"
    local num_extensions=$(echo "$extensions" | wc -w)
    
    # Determine if audio-only or has video
    local has_video=false
    for ext in $extensions; do
        case "$ext" in
            mp4|webm|mkv|avi|mov) has_video=true ;;
        esac
    done
    
    log_info "Found $count media files ($extensions)"
    # For video files: probe ACTUAL codecs/resolutions (extension alone lies —
    # two .webm can be AV1/VP9 and 720p/1080p, which breaks stream-copy concat).
    local homogeneous=true
    if $has_video; then
        local ref_sig="" sig=""
        for f in "${media_files[@]}"; do
            sig=$(ffprobe -v error -select_streams v:0 \
                -show_entries stream=codec_name,width,height -of csv=p=0 "$f" 2>/dev/null)
            if [[ -z "$ref_sig" ]]; then
                ref_sig="$sig"
            elif [[ "$sig" != "$ref_sig" ]]; then
                homogeneous=false
                break
            fi
        done
    fi

    # Choose output format
    local output_ext
    if $has_video; then
        if [ "$num_extensions" -eq 1 ] && $homogeneous; then
            output_ext="$extensions"
            log_info "All files share codec/resolution ($ref_sig) — fast concat (no re-encoding)"
        else
            # Mixed codecs/resolutions → must re-encode. mp4/H.264 is the safe default.
            output_ext="mp4"
            $homogeneous || log_warning "Files have mixed codecs/resolutions — will normalize & re-encode to .mp4"
            [ "$num_extensions" -eq 1 ] || log_info "Mixed extensions — re-encoding to .mp4"
        fi
    else
        # Audio-only
        if [ "$num_extensions" -eq 1 ]; then
            output_ext="$extensions"
            log_info "All files are .$output_ext — will use fast concat (no re-encoding)"
        else
            output_ext=$(printf "mp3\nm4a\nflac" | fzf --prompt="Output format: " --height=~100% --border)
            output_ext="${output_ext:-mp3}"
            log_info "Mixed formats — will re-encode to .$output_ext"
        fi
    fi

    echo -n "Output filename (without extension): "
    read -r output_name
    output_name="${output_name:-combined}"
    local output_file="$src_dir/${output_name}.${output_ext}"

    log_info "Combining $count files into: $output_file"

    # Decide path: fast concat (homogeneous, single ext) vs filter re-encode (mixed)
    if $homogeneous && [ "$num_extensions" -eq 1 ]; then
        # Same codec/resolution/container → fast stream-copy concat
        local list_file=$(mktemp)
        for f in "${media_files[@]}"; do
            echo "file '$(realpath "$f")'" >> "$list_file"
        done
        if ffmpeg -f concat -safe 0 -i "$list_file" -c copy -y "$output_file" 2>/dev/null; then
            log_success "Combined $count files into: $output_file"
        else
            log_error "Fast concat failed — falling back to normalize & re-encode..."
            rm -f "$list_file"
            _combine_reencode "$output_file" "$has_video" "${media_files[@]}"
        fi
        rm -f "$list_file"
    else
        # Mixed codecs/resolutions/extensions → concat filter with normalization
        _combine_reencode "$output_file" "$has_video" "${media_files[@]}"
    fi
}

# Helper: concat via filter_complex, normalizing every clip to a common
# resolution/fps (video) so mixed AV1/VP9 and 720p/1080p sources merge cleanly.
_combine_reencode() {
    local output_file="$1"; shift
    local has_video="$1"; shift
    local -a files=("$@")
    local n=${#files[@]}

    local -a inputs=()
    local filter=""
    local concat_inputs=""
    for i in "${!files[@]}"; do
        inputs+=(-i "${files[$i]}")
        if [[ "$has_video" == "true" ]]; then
            # Scale to fit 1920x1080, pad to exact size, fix SAR and fps for concat
            filter+="[$i:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1,setsar=1,fps=30[v$i];"
            concat_inputs+="[v$i][$i:a]"
        else
            concat_inputs+="[$i:a]"
        fi
    done

    if [[ "$has_video" == "true" ]]; then
        filter+="${concat_inputs}concat=n=$n:v=1:a=1[outv][outa]"
        log_info "Re-encoding $n clips (H.264/AAC, 1080p) — this can take a while..."
        if ffmpeg "${inputs[@]}" -filter_complex "$filter" \
            -map "[outv]" -map "[outa]" \
            -c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 192k \
            -y "$output_file" 2>/dev/null; then
            log_success "Combined $n files into: $output_file (re-encoded)"
        else
            log_error "Failed to combine files"
            return 1
        fi
    else
        filter+="${concat_inputs}concat=n=$n:v=0:a=1[outa]"
        if ffmpeg "${inputs[@]}" -filter_complex "$filter" -map "[outa]" -y "$output_file" 2>/dev/null; then
            log_success "Combined $n files into: $output_file"
        else
            log_error "Failed to combine files"
            return 1
        fi
    fi
}

interactive_mode() {
    echo
    local main_choice=$(printf "Download from URL\nCombine files\nCheck installation status\nUpdate yt-dlp and gallery-dl\nSetup cookies for platform\nExit" | fzf --prompt="Video Downloader: " --height=~100% --border)
    
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
        "Combine files")
            combine_files
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
