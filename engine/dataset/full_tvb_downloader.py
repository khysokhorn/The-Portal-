import subprocess
import os
import sys
import pysrt
import re

# Import cleaning logic
def clean_srt_text(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'^>>\s*', '', text, flags=re.MULTILINE)
    allowed_pattern = r'[^\u1780-\u17FF\u19E0-\u19FF0-9០-៩\s.,!?:;"\(\)-]'
    text = re.sub(allowed_pattern, '', text)
    return text.strip()

def process_srt_file(file_path):
    print(f"🧹 Auto-cleaning: {file_path}")
    subs = pysrt.open(file_path)
    cleaned_subs = pysrt.SubRipFile()
    for sub in subs:
        cleaned_text = clean_srt_text(sub.text)
        if cleaned_text:
            sub.text = cleaned_text
            cleaned_subs.append(sub)
    cleaned_subs.clean_indexes()
    cleaned_subs.save(file_path, encoding='utf-8')

def full_workflow(video_file, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"🚀 Starting Full TVB Download & Clean Workflow...")
    
    # 1. Download WAV and SRT using yt-dlp
    # We use --write-auto-subs and --convert-subs srt
    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "wav",
        "--write-auto-subs", "--sub-langs", "km.*",
        "--convert-subs", "srt",
        "--ffmpeg-location", "/opt/homebrew/bin/",
        "-a", video_file,
        "-o", os.path.join(output_dir, "%(id)s.%(ext)s")
    ]
    
    subprocess.run(cmd)

    # 2. Find and Clean SRT files
    for file in os.listdir(output_dir):
        if file.endswith(".srt"):
            srt_path = os.path.join(output_dir, file)
            # If there are km-orig and km files, they are same. Keep one and rename to simple .srt
            if "km-orig" in file:
                os.remove(srt_path) # Delete original to avoid duplicates
                continue
                
            process_srt_file(srt_path)
            # Rename to simple ID.srt
            new_name = file.split(".")[0] + ".srt"
            os.rename(srt_path, os.path.join(output_dir, new_name))

    print(f"\n✨ Workflow Complete! Only clean WAV and SRT files remain in {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 engine/dataset/full_tvb_downloader.py <video_list_txt> <output_dir>")
        sys.exit(1)
    
    full_workflow(sys.argv[1], sys.argv[2])
