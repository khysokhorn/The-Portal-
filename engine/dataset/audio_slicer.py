import librosa
import soundfile as sf
import os
import sys

def slice_audio(input_file, output_dir, top_db=30, min_duration=2.0, max_duration=15.0):
    print(f"Loading {input_file}...")
    y, sr = librosa.load(input_file, sr=None)
    
    print("Detecting non-silent intervals...")
    # top_db: the threshold (in decibels) below reference to consider as silence
    intervals = librosa.effects.split(y, top_db=top_db)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    count = 0
    for start, end in intervals:
        duration = (end - start) / sr
        
        if duration >= min_duration and duration <= max_duration:
            clip = y[start:end]
            output_path = os.path.join(output_dir, f"clip_{count:04d}.wav")
            sf.write(output_path, clip, sr)
            count += 1
            if count % 10 == 0:
                print(f"Exported {count} clips...")
                
    print(f"Done! Created {count} clips in {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 engine/audio_slicer.py <input_file> <output_dir>")
        sys.exit(1)
        
    input_wav = sys.argv[1]
    out_dir = sys.argv[2]
    slice_audio(input_wav, out_dir)
