import pysrt
import re
import os
import sys

def clean_srt_text(text):
    # 1. Remove markers like [Music], [តន្ត្រី], etc.
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    
    # 2. Remove speaker markers like >>
    text = re.sub(r'^>>\s*', '', text, flags=re.MULTILINE)
    
    # 3. Keep ONLY Khmer characters, Khmer/Arabic numbers, and basic punctuation
    # Khmer Unicode: \u1780-\u17FF
    # Khmer Symbols: \u19E0-\u19FF
    # Latin Punctuation: .,!?:; "()
    allowed_pattern = r'[^\u1780-\u17FF\u19E0-\u19FF0-9០-៩\s.,!?:;"\(\)-]'
    text = re.sub(allowed_pattern, '', text)
    
    # 4. Trim whitespace and newlines
    text = text.strip()
    
    return text

def process_srt(input_path, output_path):
    print(f"🧹 Cleaning SRT: {input_path}")
    subs = pysrt.open(input_path)
    cleaned_subs = pysrt.SubRipFile()
    
    for sub in subs:
        cleaned_text = clean_srt_text(sub.text)
        
        # Only keep segments that have actual text after cleaning
        if cleaned_text:
            sub.text = cleaned_text
            cleaned_subs.append(sub)
            
    # Re-index the subtitles
    cleaned_subs.clean_indexes()
    cleaned_subs.save(output_path, encoding='utf-8')
    print(f"✨ Saved clean SRT to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 engine/dataset/srt_cleaner.py <input_srt_or_dir> <output_dir>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    out_dir = sys.argv[2]
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    if os.path.isdir(input_path):
        for file in os.listdir(input_path):
            if file.endswith(".srt"):
                process_srt(os.path.join(input_path, file), os.path.join(out_dir, file))
    else:
        file_name = os.path.basename(input_path)
        process_srt(input_path, os.path.join(out_dir, file_name))
