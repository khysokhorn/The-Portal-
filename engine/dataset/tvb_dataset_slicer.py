import librosa
import soundfile as sf
import os
import sys

def tvb_slice_workflow(input_file, output_dir):
    # Configuration based on the guide
    MIN_DUR = 3.0
    MAX_DUR = 10.0
    TOP_DB = 25  # Slightly more sensitive for TVB dubbing
    
    print(f"🚀 Starting TVB Dataset Slicer for: {input_file}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Load audio
    y, sr = librosa.load(input_file, sr=None)
    
    # Split based on silence
    intervals = librosa.effects.split(y, top_db=TOP_DB)
    
    count = 0
    for start, end in intervals:
        duration = (end - start) / sr
        
        # Check if duration is within the 3-10 second range
        if duration >= MIN_DUR and duration <= MAX_DUR:
            clip = y[start:end]
            
            # Save the clip
            filename = f"tvb_clip_{count:04d}.wav"
            output_path = os.path.join(output_dir, filename)
            sf.write(output_path, clip, sr)
            count += 1
            
            if count % 20 == 0:
                print(f"✅ Extracted {count} clips...")

    print(f"\n✨ Workflow Complete!")
    print(f"📁 Folder: {output_dir}")
    print(f"🎵 Total clips optimized for training: {count}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 engine/dataset/tvb_dataset_slicer.py <input_file_or_dir> <output_dir>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    out_dir = sys.argv[2]
    
    if os.path.isdir(input_path):
        print(f"📂 Processing all WAV files in directory: {input_path}")
        for file in os.listdir(input_path):
            if file.endswith(".wav"):
                input_file = os.path.join(input_path, file)
                # Create a subfolder for each original file to avoid overwriting clips
                sub_out_dir = os.path.join(out_dir, os.path.splitext(file)[0])
                tvb_slice_workflow(input_file, sub_out_dir)
    else:
        tvb_slice_workflow(input_path, out_dir)
