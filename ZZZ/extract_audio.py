#!/usr/bin/env python3
import subprocess
import sys
import os

def extract_audio(video_path, output_path=None, bitrate='192k'):
    """Extract MP3 audio from video file"""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return None
    
    if output_path is None:
        output_path = os.path.splitext(video_path)[0] + '.mp3'
    
    print(f"Extracting audio from: {video_path}")
    
    cmd = ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'mp3', '-ab', bitrate, '-y', output_path]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ MP3 audio saved as: {output_path}")
        return output_path
    else:
        print(f"❌ Failed to extract MP3: {result.stderr}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_audio.py <video_file> [output_file] [bitrate]")
        sys.exit(1)
    
    video = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    bitrate = sys.argv[3] if len(sys.argv) > 3 else '192k'
    
    extract_audio(video, output, bitrate)
