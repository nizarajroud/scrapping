#!/usr/bin/env python3
"""
Simple Facebook Reel Video Combiner using FFmpeg
Only requires yt-dlp and FFmpeg (no moviepy needed)
"""

import subprocess
import sys
import os
from pathlib import Path

def install_ytdlp():
    """Install yt-dlp only"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'yt-dlp'])
        print("✓ Installed yt-dlp")
        return True
    except subprocess.CalledProcessError:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'yt-dlp'])
            print("✓ Installed yt-dlp with --user flag")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install yt-dlp. Please install manually: pip install yt-dlp")
            return False

def check_ffmpeg():
    """Check if FFmpeg is available"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def download_facebook_reel(url, output_name):
    """Download Facebook reel using yt-dlp"""
    try:
        cmd = [
            'yt-dlp',
            '--no-check-certificate',
            '--format', 'best[ext=mp4]',
            '--output', f'{output_name}.%(ext)s',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f'{output_name}.mp4'
        else:
            print(f"yt-dlp error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def combine_videos_ffmpeg(video1_path, video2_path, output_path):
    """Combine two videos using FFmpeg"""
    try:
        # Create a temporary file list for FFmpeg concat
        filelist_path = "temp_filelist.txt"
        with open(filelist_path, 'w') as f:
            f.write(f"file '{os.path.abspath(video1_path)}'\n")
            f.write(f"file '{os.path.abspath(video2_path)}'\n")
        
        # Run FFmpeg concat
        cmd = [
            'ffmpeg', 
            '-f', 'concat',
            '-safe', '0',
            '-i', filelist_path,
            '-c', 'copy',
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temp file
        if os.path.exists(filelist_path):
            os.remove(filelist_path)
        
        if result.returncode == 0:
            print(f"✓ Combined video saved as: {output_path}")
            return True
        else:
            print(f"FFmpeg error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error combining videos: {e}")
        return False

def main():
    # Read URLs from output.txt
    try:
        with open("output.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ output.txt not found. Please run the scraper first.")
        return
    
    if not urls:
        print("❌ No URLs found in output.txt")
        return
    
    print("Facebook Reel Video Combiner")
    print("=" * 40)
    print(f"Found {len(urls)} URLs in output.txt")
    
    # Check FFmpeg first
    print("Checking for FFmpeg...")
    if not check_ffmpeg():
        print("✗ FFmpeg not found!")
        print("Please install FFmpeg:")
        print("- Windows: Download from https://ffmpeg.org/download.html")
        print("- Mac: brew install ffmpeg")
        print("- Ubuntu/Debian: sudo apt install ffmpeg")
        print("- CentOS/RHEL: sudo yum install ffmpeg")
        return
    else:
        print("✓ FFmpeg found")
    
    # Install yt-dlp
    print("Installing yt-dlp...")
    if not install_ytdlp():
        return
    
    # Download videos
    print("\nDownloading videos...")
    video_files = []
    for i, url in enumerate(urls, 1):
        print(f"Downloading reel {i}/{len(urls)}...")
        filename = download_facebook_reel(url, f"reel_{i}")
        if filename and Path(filename).exists():
            video_files.append(filename)
            print(f"✓ Downloaded: {filename}")
        else:
            print(f"✗ Failed to download reel {i} - continuing with others...")
    
    # Combine videos
    if len(video_files) >= 2:
        print(f"\nCombining {len(video_files)} videos with FFmpeg...")
        output_file = "combined_reels.mp4"
        
        # Create filelist for all videos
        filelist_path = "temp_filelist.txt"
        with open(filelist_path, 'w') as f:
            for video in video_files:
                f.write(f"file '{os.path.abspath(video)}'\n")
        
        # Run FFmpeg concat
        cmd = [
            'ffmpeg', 
            '-f', 'concat',
            '-safe', '0',
            '-i', filelist_path,
            '-c', 'copy',
            '-y',
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temp file
        if os.path.exists(filelist_path):
            os.remove(filelist_path)
        
        if result.returncode == 0:
            print(f"✓ Combined video saved as: {output_file}")
            if Path(output_file).exists():
                file_size = Path(output_file).stat().st_size / (1024*1024)
                print(f"File size: {file_size:.1f} MB")
        else:
            print(f"FFmpeg error: {result.stderr}")
    else:
        print(f"Need at least 2 videos to combine, only got {len(video_files)}")
    
    # Optional: Clean up individual files
    cleanup = input("\nDelete individual video files? (y/n): ").lower().strip()
    if cleanup == 'y':
        for file in video_files:
            try:
                Path(file).unlink()
                print(f"Deleted: {file}")
            except Exception as e:
                print(f"Could not delete {file}: {e}")

if __name__ == "__main__":
    main()