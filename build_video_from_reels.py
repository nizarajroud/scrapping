#!/usr/bin/env python3
"""
Build Video from Reels - Downloads and combines reels from database
"""

import subprocess
import sys
import os
import sqlite3
import random
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_PATH = "scrapping.db"

def ensure_db_exists():
    """Ensure database and tables exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Source (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            parent_url TEXT NOT NULL,
            author TEXT NOT NULL,
            UNIQUE(category_id, parent_url, author),
            FOREIGN KEY (category_id) REFERENCES Category(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ParentVideo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            theme TEXT NOT NULL,
            created_date TEXT NOT NULL,
            output_path TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            added_date TEXT NOT NULL,
            processed INTEGER DEFAULT 0,
            source_id INTEGER NOT NULL,
            parent_video_id INTEGER,
            FOREIGN KEY (source_id) REFERENCES Source(id),
            FOREIGN KEY (parent_video_id) REFERENCES ParentVideo(id)
        )
    """)
    conn.commit()
    conn.close()

def install_ytdlp():
    """Install yt-dlp if needed"""
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing yt-dlp...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'yt-dlp'])

def install_whisper():
    """Install openai-whisper if needed"""
    try:
        import whisper
    except ImportError:
        print("Installing openai-whisper...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openai-whisper'])

def install_notion():
    """Install notion-client if needed"""
    try:
        from notion_client import Client
    except ImportError:
        print("Installing notion-client...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'notion-client'])

def install_boto3():
    """Install boto3 if needed"""
    try:
        import boto3
    except ImportError:
        print("Installing boto3...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'boto3'])

def download_reel(url, output_path):
    """Download a single reel"""
    try:
        subprocess.run([
            'yt-dlp',
            '-f', 'best',
            '-o', output_path,
            url
        ], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def combine_videos(video_files, output_file, speed=1.0, repetitions=1):
    """Combine multiple videos into one using ffmpeg with normalization and speed adjustment"""
    import tempfile
    
    output_dir = os.path.dirname(output_file)
    
    # Normalize and repeat each video
    print("  Normalizing and repeating videos...")
    processed_files = []
    for i, video in enumerate(video_files):
        norm_file = os.path.join(output_dir, f"norm_{i}.mp4")
        
        # Apply speed adjustment if needed
        if speed != 1.0:
            speed_filter = f"setpts={1/speed}*PTS"
            audio_speed = f"atempo={speed}" if speed <= 2.0 else f"atempo=2.0,atempo={speed/2.0}"
            vf_filter = f"scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,{speed_filter}"
        else:
            vf_filter = 'scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2'
            audio_speed = None
        
        cmd = [
            'ffmpeg', '-i', video,
            '-vf', vf_filter,
            '-r', '25', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k', '-ar', '44100'
        ]
        
        if audio_speed:
            cmd.extend(['-af', audio_speed])
        
        cmd.extend(['-y', norm_file])
        
        subprocess.run(cmd, capture_output=True)
        
        # Repeat this video if needed
        if repetitions > 1:
            repeated_file = os.path.join(output_dir, f"repeated_{i}.mp4")
            
            # Create concat file for this video
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for _ in range(repetitions):
                    f.write(f"file '{os.path.abspath(norm_file)}'\n")
                repeat_list = f.name
            
            # Concatenate repetitions
            subprocess.run([
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', repeat_list,
                '-c', 'copy',
                '-y',
                repeated_file
            ], capture_output=True)
            
            os.unlink(repeat_list)
            os.remove(norm_file)
            processed_files.append(repeated_file)
        else:
            processed_files.append(norm_file)
        
        print(f"  ✓ Processed {i+1}/{len(video_files)} (x{repetitions} repetitions)")
    
    # Create concat file list for all processed videos
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for proc_file in processed_files:
            f.write(f"file '{os.path.abspath(proc_file)}'\n")
        list_file = f.name
    
    # Concatenate all videos
    print("  Concatenating all videos...")
    try:
        subprocess.run([
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            '-y',
            output_file
        ], check=True, capture_output=True)
        
        # Cleanup
        os.unlink(list_file)
        for proc_file in processed_files:
            os.remove(proc_file)
        
        return True
    except subprocess.CalledProcessError:
        os.unlink(list_file)
        for proc_file in processed_files:
            if os.path.exists(proc_file):
                os.remove(proc_file)
        return False

def generate_transcript(video_file):
    """Generate transcript using Whisper"""
    import whisper
    import torch
    
    print(f"  🎤 Generating transcript for: {os.path.basename(video_file)}")
    
    try:
        # Force CPU to avoid CUDA NaN issues
        device = "cpu"
        model = whisper.load_model("base", device=device)
        result = model.transcribe(video_file, fp16=False)
        return result["text"]
    except Exception as e:
        print(f"  ⚠ Failed to generate transcript: {e}")
        return None

def format_transcript_with_bedrock(transcript):
    """Format transcript using AWS Bedrock"""
    import boto3
    import json
    
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    bedrock_model_id = os.getenv('MOEDL_INFERENCE_ID') or os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
    
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=aws_region)
        
        prompt = f"""Please analyze this transcript and provide:

1. A short descriptive title (5-8 words max) that captures the main topic or situation
2. The formatted dialogue with vocabulary highlighted

Requirements for the dialogue:
- Each line should start with a dash (-)
- Do NOT add speaker labels like "Server:" or "Customer:" in the dialogue lines
- Highlight in **bold** ONLY vocabulary words, phrasal verbs, and idioms that are appropriate for B2 English learners (upper-intermediate level)
- Include phrasal verbs (e.g., "look up", "give up") and idioms (e.g., "piece of cake", "break the ice")
- No empty lines between dialogue lines
- First line should start with the main participants in parentheses (e.g., "(server, customer)"), followed by a colon, then list the key vocabulary words, phrasal verbs, and idioms in bold, separated by commas

Format your response EXACTLY like this:
TITLE: [Your title here]
DIALOGUE:
- (participant1, participant2): **word1**, **word2**, **word3**, etc.
- First dialogue line with **vocabulary** highlighted
- Second dialogue line
- And so on...

Example:
TITLE: At the Restaurant
DIALOGUE:
- (server, customer): **vegetarian**, **prepare**, **dressing**, **look forward to**, **piece of cake**
- Good evening. Here's the menu. Would you like to start with a drink?
- Thank you. Do you have any **vegetarian** pasta dishes?
- We can **prepare** pasta with vegetables. That's a **piece of cake** for our chef.

Transcript:
{transcript}"""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
        
        response = bedrock.invoke_model(
            modelId=bedrock_model_id,
            body=body
        )
        
        response_body = json.loads(response['body'].read())
        formatted_text = response_body['content'][0]['text']
        
        # Parse title and dialogue
        lines = formatted_text.split('\n')
        title = None
        dialogue_lines = []
        in_dialogue = False
        
        for line in lines:
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
            elif line.startswith('DIALOGUE:'):
                in_dialogue = True
            elif in_dialogue and line.strip():
                dialogue_lines.append(line.strip())
        
        dialogue = '\n'.join(dialogue_lines)
        
        return title, dialogue
    except Exception as e:
        print(f"  ⚠ Failed to format with Bedrock: {e}")
        return None, transcript

def send_to_notion_table(vocabulary_entries, toggle_title):
    """Send all vocabulary entries to Notion page as a single table in a toggle"""
    from notion_client import Client
    
    notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
    notion_page_id = os.getenv('NOTION_PAGE_ID')
    
    if not notion_token or not notion_page_id:
        print("  ⚠ NOTION_API_KEY or NOTION_PAGE_ID not found in .env")
        return False
    
    try:
        notion = Client(auth=notion_token)
        
        # Build table rows
        table_rows = [
            # Header row
            {
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [{"type": "text", "text": {"content": "Title"}}],
                        [{"type": "text", "text": {"content": "Participants"}}],
                        [{"type": "text", "text": {"content": "Vocabulary"}}]
                    ]
                }
            }
        ]
        
        # Add data rows
        for entry in vocabulary_entries:
            # Format vocabulary with spaces: word1 ; word2 ; word3
            vocab_formatted = entry['vocabulary'].replace(',', ' ;')
            
            table_rows.append({
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [{"type": "text", "text": {"content": entry['title']}}],
                        [{"type": "text", "text": {"content": entry['participants']}}],
                        [{"type": "text", "text": {"content": vocab_formatted}, "annotations": {"bold": True}}]
                    ]
                }
            })
        
        # Create toggle with table inside
        notion.blocks.children.append(
            block_id=notion_page_id,
            children=[
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": toggle_title}}],
                        "children": [
                            {
                                "object": "block",
                                "type": "table",
                                "table": {
                                    "table_width": 3,
                                    "has_column_header": True,
                                    "has_row_header": False,
                                    "children": table_rows
                                }
                            }
                        ]
                    }
                }
            ]
        )
        print(f"  ✓ Vocabulary table with {len(vocabulary_entries)} entries sent to Notion")
        return True
    except Exception as e:
        print(f"  ⚠ Failed to send to Notion: {e}")
        return False

def send_to_notion(transcript, toggle_title, content_title):
    """Send transcript to Notion page as table row in a toggle"""
    from notion_client import Client
    
    notion_token = os.getenv('NOTION_API_KEY') or os.getenv('NOTION_TOKEN')
    notion_page_id = os.getenv('NOTION_PAGE_ID')
    
    if not notion_token or not notion_page_id:
        print("  ⚠ NOTION_API_KEY or NOTION_PAGE_ID not found in .env")
        return False
    
    try:
        notion = Client(auth=notion_token)
        
        # Split transcript into lines and get only the first line (vocabulary)
        lines = [line.strip() for line in transcript.split('\n') if line.strip()]
        
        if not lines:
            return False
        
        # Get only the first line (vocabulary line)
        vocab_line = lines[0].lstrip('- ').strip()
        
        # Parse participants and vocabulary
        # Format: (participant1, participant2): **word1**, **word2**, etc.
        if ':' in vocab_line:
            parts_section, vocab_section = vocab_line.split(':', 1)
            participants = parts_section.strip('() ')
            # Remove bold markers and clean vocabulary
            vocabulary = vocab_section.replace('**', '').strip()
        else:
            participants = ""
            vocabulary = vocab_line.replace('**', '').strip()
        
        # Create toggle with table inside
        notion.blocks.children.append(
            block_id=notion_page_id,
            children=[
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": toggle_title}}],
                        "children": [
                            {
                                "object": "block",
                                "type": "table",
                                "table": {
                                    "table_width": 3,
                                    "has_column_header": True,
                                    "has_row_header": False,
                                    "children": [
                                        {
                                            "type": "table_row",
                                            "table_row": {
                                                "cells": [
                                                    [{"type": "text", "text": {"content": "Title"}}],
                                                    [{"type": "text", "text": {"content": "Participants"}}],
                                                    [{"type": "text", "text": {"content": "Vocabulary"}}]
                                                ]
                                            }
                                        },
                                        {
                                            "type": "table_row",
                                            "table_row": {
                                                "cells": [
                                                    [{"type": "text", "text": {"content": content_title or ""}}],
                                                    [{"type": "text", "text": {"content": participants}}],
                                                    [{"type": "text", "text": {"content": vocabulary}}]
                                                ]
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ]
        )
        print(f"  ✓ Vocabulary table sent to Notion")
        return True
    except Exception as e:
        print(f"  ⚠ Failed to send to Notion: {e}")
        return False

def main():
    ensure_db_exists()
    install_ytdlp()
    
    print("🎬 Build Video from Reels")
    print("=" * 70)
    
    # Get categories from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, transcript, speed, repetitions FROM Category ORDER BY name")
    categories = cursor.fetchall()
    
    if not categories:
        print("❌ No categories found in database. Please add categories first.")
        conn.close()
        return
    
    # Ask for category
    print("\nSelect category:")
    category_names = [cat[1] for cat in categories]
    try:
        from pyfzf.pyfzf import FzfPrompt
        fzf = FzfPrompt()
        selected_category = fzf.prompt(category_names, fzf_options='--no-info')[0]
    except ImportError:
        print("Installing pyfzf...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyfzf'])
        from pyfzf.pyfzf import FzfPrompt
        fzf = FzfPrompt()
        selected_category = fzf.prompt(category_names, fzf_options='--no-info')[0]
    except IndexError:
        selected_category = category_names[0] if category_names else None
    
    if not selected_category:
        print("❌ Category is required")
        conn.close()
        return
    
    # Get category_id
    category_id = next(cat[0] for cat in categories if cat[1] == selected_category)
    needs_transcript = next(cat[2] for cat in categories if cat[1] == selected_category)
    video_speed = next(cat[3] for cat in categories if cat[1] == selected_category)
    video_repetitions = next(cat[4] for cat in categories if cat[1] == selected_category)
    theme = selected_category
    print(f"Selected category: {theme}")
    print(f"  Speed: {video_speed}x, Repetitions: {video_repetitions}")
    
    # Install transcript dependencies if needed
    if needs_transcript:
        print("📝 Transcript enabled for this category")
        install_whisper()
        install_boto3()
        install_notion()
    
    # Find the highest number for this theme
    cursor.execute("""
        SELECT name FROM ParentVideo 
        WHERE name LIKE ? 
        ORDER BY CAST(SUBSTR(name, LENGTH(?) + 2) AS INTEGER) DESC 
        LIMIT 1
    """, (f"{theme}-%", theme))
    result = cursor.fetchone()
    
    if result and result[0]:
        # Extract number from last parent video (e.g., "Relg-3" -> 3)
        try:
            last_num = int(result[0].split('-')[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1
    
    parent_video_base = f"{theme}-{next_num}"
    print(f"Parent video: {parent_video_base}")
    
    # Create ParentVideo record (or get existing)
    cursor.execute(
        "INSERT OR IGNORE INTO ParentVideo (name, theme, created_date) VALUES (?, ?, datetime('now'))",
        (parent_video_base, theme)
    )
    cursor.execute("SELECT id FROM ParentVideo WHERE name = ?", (parent_video_base,))
    parent_video_id = cursor.fetchone()[0]
    conn.commit()
    
    # Get max reels to process
    max_reels = int(os.getenv('DEFAULT_COMBINED_REELS', '200'))
    
    # Get all authors for this category
    cursor.execute("""
        SELECT DISTINCT s.author 
        FROM Source s
        INNER JOIN Reels r ON r.source_id = s.id
        WHERE s.category_id = ? AND r.processed = 0
    """, (category_id,))
    authors = [row[0] for row in cursor.fetchall()]
    
    if not authors:
        print(f"❌ No unprocessed reels found for category: {theme}")
        conn.close()
        return
    
    print(f"\n📊 Found {len(authors)} author(s) for category {theme}")
    
    # Ask user: single author or multiple authors
    print("\nSelect mode:")
    try:
        mode = fzf.prompt(['Multiple authors', 'Single author'], fzf_options='--no-info')[0]
    except IndexError:
        mode = 'Multiple authors'
    
    selected_author = None
    if mode == 'Single author':
        print("\nSelect author:")
        try:
            selected_author = fzf.prompt(authors, fzf_options='--no-info')[0]
            print(f"Selected author: {selected_author}")
        except IndexError:
            print("No author selected, using multiple authors mode")
    
    # Collect URLs
    urls_to_process = []
    primary_author = None
    
    if selected_author:
        # Single author mode: get all reels for selected author
        primary_author = selected_author
        cursor.execute("""
            SELECT r.id, r.url 
            FROM Reels r
            INNER JOIN Source s ON r.source_id = s.id
            WHERE s.category_id = ? AND s.author = ? AND r.processed = 0
        """, (category_id, selected_author))
        all_reels = cursor.fetchall()
        random.shuffle(all_reels)
        urls_to_process = all_reels[:max_reels]
        print(f"  {selected_author}: {len(urls_to_process)} reels (randomly selected)")
    elif len(authors) == 1:
        # Single author available: select randomly
        author = authors[0]
        primary_author = author
        cursor.execute("""
            SELECT r.id, r.url 
            FROM Reels r
            INNER JOIN Source s ON r.source_id = s.id
            WHERE s.category_id = ? AND s.author = ? AND r.processed = 0
        """, (category_id, author))
        all_reels = cursor.fetchall()
        random.shuffle(all_reels)
        urls_to_process = all_reels[:max_reels]
        print(f"  {author}: {len(urls_to_process)} reels (randomly selected)")
    else:
        # Multiple authors: distribute evenly and alternate
        # Use first author as primary
        primary_author = authors[0]
        author_reels = {}
        for author in authors:
            cursor.execute("""
                SELECT r.id, r.url 
                FROM Reels r
                INNER JOIN Source s ON r.source_id = s.id
                WHERE s.category_id = ? AND s.author = ? AND r.processed = 0
            """, (category_id, author))
            author_reels[author] = cursor.fetchall()
            print(f"  {author}: {len(author_reels[author])} reels available")
        
        # Randomly select reels alternating between authors
        author_list = list(authors)
        random.shuffle(author_list)
        
        while len(urls_to_process) < max_reels:
            added = False
            for author in author_list:
                if author_reels[author]:
                    urls_to_process.append(author_reels[author].pop(0))
                    added = True
                    if len(urls_to_process) >= max_reels:
                        break
            if not added:  # No more reels available
                break
    
    print(f"\n🎯 Processing {len(urls_to_process)} reels total")
    
    # Update parent_video name to include author
    theme_short = theme[:3] if len(theme) >= 3 else theme
    parent_video = f"{theme_short}-{next_num}-{primary_author}"
    print(f"Updated parent video name: {parent_video}")
    
    # Create output directory
    processing_path = os.getenv('DEFAULT_PROCESSING_PATH', '/mnt/d/PERSONAL/scrap')
    output_dir = os.path.join(processing_path, parent_video)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    
    # Download reels
    downloaded = 0
    downloaded_files = []
    vocabulary_entries = []  # Collect all vocabulary entries
    
    for reel_id, url in urls_to_process:
        output_file = os.path.join(output_dir, f"reel_{reel_id}.mp4")
        print(f"\n⬇️  Downloading: {url}")
        
        if download_reel(url, output_file):
            downloaded += 1
            downloaded_files.append(output_file)
            print(f"✓ Downloaded ({downloaded}/{len(urls_to_process)})")
            
            # Generate transcript if needed
            if needs_transcript:
                transcript = generate_transcript(output_file)
                if transcript:
                    print("  🤖 Formatting transcript with Bedrock...")
                    title, formatted_transcript = format_transcript_with_bedrock(transcript)
                    
                    # Parse vocabulary line
                    lines = [line.strip() for line in formatted_transcript.split('\n') if line.strip()]
                    if lines:
                        vocab_line = lines[0].lstrip('- ').strip()
                        
                        # Parse participants and vocabulary
                        if ':' in vocab_line:
                            parts_section, vocab_section = vocab_line.split(':', 1)
                            participants = parts_section.strip('() ')
                            vocabulary = vocab_section.replace('**', '').strip()
                        else:
                            participants = ""
                            vocabulary = vocab_line.replace('**', '').strip()
                        
                        # Add to vocabulary entries
                        vocabulary_entries.append({
                            'title': title or f"Reel {reel_id}",
                            'participants': participants,
                            'vocabulary': vocabulary
                        })
        else:
            print(f"❌ Failed to download")
        
        # Update database regardless of success/failure
        cursor.execute(
            "UPDATE Reels SET processed=1, parent_video_id=? WHERE id=?",
            (parent_video_id, reel_id)
        )
        conn.commit()
    
    # Send all vocabulary entries to Notion at once
    if vocabulary_entries and needs_transcript:
        print(f"\n📝 Sending {len(vocabulary_entries)} vocabulary entries to Notion...")
        send_to_notion_table(vocabulary_entries, parent_video)
    
    if not downloaded_files:
        conn.close()
        print("\n❌ No reels downloaded")
        return
    
    print(f"\n🎬 Combining {len(downloaded_files)} videos...")
    combined_video = os.path.join(processing_path, f"{parent_video}.mp4")
    
    if combine_videos(downloaded_files, combined_video, speed=video_speed, repetitions=video_repetitions):
        print(f"✓ Combined video created: {combined_video}")
        
        # Mount G: drive if not already mounted
        mount_point = "/mnt/g"
        if not os.path.ismount(mount_point):
            print(f"📂 Mounting G: drive...")
            try:
                subprocess.run(['sudo', 'mount', '-t', 'drvfs', 'G:', mount_point], check=True)
                print(f"✓ Mounted G: drive")
            except subprocess.CalledProcessError:
                print(f"⚠ Failed to mount G: drive, keeping video at {combined_video}")
        
        # Move to resulting path
        resulting_path = os.getenv('DEFAULT_RESULTING_PATH', '/mnt/g/Mon Drive/FORMATIONS/SoftSkills/Infuse').strip('"')
        os.makedirs(resulting_path, exist_ok=True)
        final_video = os.path.join(resulting_path, os.path.basename(combined_video))
        
        import shutil
        # Use copyfile to avoid permission issues on mounted drives
        shutil.copyfile(combined_video, final_video)
        os.remove(combined_video)
        print(f"✓ Moved to: {final_video}")
        
        # Update ParentVideo with output path
        cursor.execute(
            "UPDATE ParentVideo SET output_path=? WHERE id=?",
            (final_video, parent_video_id)
        )
        conn.commit()
        conn.close()
        
        # Remove temporary directory with individual reels
        print(f"\n🗑️  Removing temporary directory: {output_dir}")
        try:
            shutil.rmtree(output_dir)
            print("✓ Cleanup complete")
        except Exception as e:
            print(f"⚠ Cleanup warning: {e}")
        
        print(f"\n🎉 Process complete! Final video: {final_video}")
    else:
        conn.close()
        print("\n❌ Failed to combine videos")

if __name__ == "__main__":
    main()
