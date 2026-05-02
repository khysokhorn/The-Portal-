import pysrt
import librosa
import soundfile as sf
import os
import sys

def srt_slicer(audio_file, srt_file, output_dir):
    # Configuration
    MIN_DUR = 3.0
    MAX_DUR = 10.0
    LIMIT_SEC = 900.0 # 15 minutes limit for verification
    
    print(f"🎬 Processing (First 15mn): {os.path.basename(audio_file)}")
    
    # Load the audio file
    y, sr = librosa.load(audio_file, sr=None)
    
    # Load the SRT file
    subs = pysrt.open(srt_file)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    count = 0
    for sub in subs:
        # Convert SRT time to seconds
        start_sec = (sub.start.hours * 3600) + (sub.start.minutes * 60) + sub.start.seconds + (sub.start.milliseconds / 1000.0)
        
        # STOP if we reached the 15 minute mark
        if start_sec > LIMIT_SEC:
            break
            
        end_sec = (sub.end.hours * 3600) + (sub.end.minutes * 60) + sub.end.seconds + (sub.end.milliseconds / 1000.0)
        
        duration = end_sec - start_sec
        
        # Only extract if it fits our 3-10s training window
        if duration >= MIN_DUR and duration <= MAX_DUR:
            start_sample = int(start_sec * sr)
            end_sample = int(end_sec * sr)
            
            # Extract the audio clip
            clip = y[start_sample:end_sample]
            
            # Create a unique name for the clip
            base_name = os.path.splitext(os.path.basename(audio_file))[0]
            clip_name = f"{base_name}_clip_{count:04d}"
            
            # Save Audio (.wav)
            sf.write(os.path.join(output_dir, f"{clip_name}.wav"), clip, sr)
            
            # Save Transcript (.txt)
            with open(os.path.join(output_dir, f"{clip_name}.txt"), "w", encoding="utf-8") as f:
                f.write(sub.text)
                
            count += 1

    print(f"✅ Extracted {count} high-quality clips to {output_dir}")

def run_bulk_srt_slicer(input_dir, output_root):
    print(f"🔍 Validating folder: {input_dir}")
    
    # Get all WAV files
    wav_files = [f for f in os.listdir(input_dir) if f.endswith(".wav")]
    
    for wav_name in wav_files:
        wav_path = os.path.join(input_dir, wav_name)
        srt_name = wav_name.replace(".wav", ".srt")
        srt_path = os.path.join(input_dir, srt_name)
        
        # ERROR CHECK: Both must exist
        if not os.path.exists(srt_path):
            print(f"❌ ERROR: Missing SRT for {wav_name}. Please clean your transcripts first!")
            continue
            
        # Run the slicer
        sub_output_dir = os.path.join(output_root, wav_name.replace(".wav", ""))
        srt_slicer(wav_path, srt_path, sub_output_dir)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 engine/dataset/srt_based_slicer.py <audio_dir_or_file> <output_dir>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    out_dir = sys.argv[2]
    
    if os.path.isdir(input_path):
        run_bulk_srt_slicer(input_path, out_dir)
    else:
        # Single file mode
        audio_file = input_path
        srt_file = audio_file.replace(".wav", ".srt")
        if os.path.exists(srt_file):
            srt_slicer(audio_file, srt_file, out_dir)
        else:
            print(f"❌ ERROR: Missing matching SRT file for {audio_file}")
