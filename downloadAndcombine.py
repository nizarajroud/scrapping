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
    """Install yt-dlp"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'yt-dlp'])
        print("✓ Installed yt-dlp")
    except subprocess.CalledProcessError:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'yt-dlp'])
            print("✓ Installed yt-dlp with --user flag")
        except subprocess.CalledProcessError:
            print("✗ Failed to install yt-dlp")
            return False
    return True



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
    # Read URLs from output.txt first
    try:
        with open("output.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ output.txt not found. Please run the scraper first.")
        return
    
    # Ask user to confirm output directory
    USER = os.getenv('USER', 'user')
    output_dir = f"/mnt/c/Users/{USER}/DOCS/PERSO/scrap"
    confirm = input(f"Save files to {output_dir}? (Y/n): ").lower().strip()
    if confirm and confirm != 'y':
        output_dir = input("Enter output directory: ").strip()
    
    # Create output directory and change to it
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    os.chdir(output_dir)
    
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
        print(f"\nNormalizing and combining {len(video_files)} videos...")
        output_file = "combined_reels.mp4"
        
        # Step 1: Normalize each video quickly
        normalized_files = []
        for i, video in enumerate(video_files):
            norm_file = f"norm_{i}.mp4"
            cmd = [
                'ffmpeg', '-i', video,
                '-vf', 'scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2',
                '-r', '25', '-c:v', 'libx264', '-preset', 'ultrafast',
                '-c:a', 'aac', '-ar', '44100',
                '-y', norm_file
            ]
            subprocess.run(cmd, capture_output=True)
            normalized_files.append(norm_file)
        
        # Step 2: Simple concat
        filelist_path = "temp_filelist.txt"
        with open(filelist_path, 'w') as f:
            for norm_file in normalized_files:
                f.write(f"file '{os.path.abspath(norm_file)}'\n")
        
        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', filelist_path, '-c', 'copy', '-y', output_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Cleanup
        os.remove(filelist_path)
        for norm_file in normalized_files:
            os.remove(norm_file)
        
        if result.returncode == 0:
            print(f"✓ Combined video saved as: {output_file}")
            if Path(output_file).exists():
                file_size = Path(output_file).stat().st_size / (1024*1024)
                print(f"File size: {file_size:.1f} MB")
                
                # Extract MP3 audio
                print("Extracting MP3 audio...")
                mp3_file = "combined_reels.mp3"
                mp3_cmd = [
                    'ffmpeg',
                    '-i', output_file,
                    '-vn',  # No video
                    '-acodec', 'mp3',
                    '-ab', '192k',  # Audio bitrate
                    '-y',
                    mp3_file
                ]
                
                mp3_result = subprocess.run(mp3_cmd, capture_output=True, text=True)
                if mp3_result.returncode == 0:
                    print(f"✓ MP3 audio saved as: {mp3_file}")
                else:
                    print(f"Failed to extract MP3: {mp3_result.stderr}")
        else:
            print(f"FFmpeg error: {result.stderr}")
    else:
        print(f"Need at least 2 videos to combine, only got {len(video_files)}")
    
    # Optional: Clean up individual files
    cleanup = input("\nDelete individual video files? (Y/n): ").lower().strip()
    if cleanup != 'n':
        for file in video_files:
            try:
                Path(file).unlink()
                print(f"Deleted: {file}")
            except Exception as e:
                print(f"Could not delete {file}: {e}")

if __name__ == "__main__":
    main()
