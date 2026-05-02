import os
import subprocess
import pysrt
from pydub import AudioSegment
import torch

# Configuration for M3 Mac
AudioSegment.converter = "/opt/homebrew/bin/ffmpeg"
FFPROBE_PATH = "/opt/homebrew/bin/ffprobe"
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

def generate_single_audio(srt_path, output_path, reference_audio=None):
    if not os.path.exists(srt_path):
        print(f"❌ Error: {srt_path} not found.")
        return

    subs = pysrt.open(srt_path)
    # Start with a silent track
    combined_audio = AudioSegment.silent(duration=0)
    
    print(f"🎙️ Starting VoxCPM generation for {len(subs)} segments on {DEVICE}...")

    for i, sub in enumerate(subs):
        # Calculate start time in milliseconds
        start_ms = (sub.start.hours * 3600000) + (sub.start.minutes * 60000) + (sub.start.seconds * 1000) + sub.start.milliseconds
        temp_wav = f"temp_segment_{i}.wav"
        
        print(f"  [{i+1}/{len(subs)}] Generating: {sub.text[:30]}...")
        
        # Path to the voxcpm binary in our local venv
        voxcpm_bin = os.path.join(os.path.dirname(__file__), ".venv", "bin", "voxcpm")
        
        # Fallback if venv not found (e.g. global install)
        if not os.path.exists(voxcpm_bin):
            voxcpm_bin = "voxcpm"

        # Call VoxCPM command-line
        if reference_audio:
            cmd = [
                voxcpm_bin, "clone",
                "--reference-audio", reference_audio,
                "--text", sub.text,
                "--output", temp_wav
            ]
        else:
            cmd = [
                voxcpm_bin, "design",
                "--text", sub.text,
                "--control", "A young female voice, high-pitched and sweet, TVB style.",
                "--output", temp_wav
            ]
        
        try:
            # Running without capture_output so you can see the progress bars
            subprocess.run(cmd, check=True)
            
            # Load and overlay
            segment_audio = AudioSegment.from_wav(temp_wav)
            
            # Pad combined audio if necessary
            if len(combined_audio) < start_ms:
                silence_padding = AudioSegment.silent(duration=(start_ms - len(combined_audio)))
                combined_audio += silence_padding
                
            combined_audio = combined_audio.overlay(segment_audio, position=start_ms)
            
            # Cleanup
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error generating segment {i}. Check the terminal output above for details.")
            continue

    # Export final result
    combined_audio.export(output_path, format="mp3")
    print(f"✅ Success! Single audio saved to: {output_path}")

if __name__ == "__main__":
    # Using your trimmed audio as the reference voice
    reference = "IoSZbIq0VhY_trimmed.mp3"
    
    # Ensure translated.srt is used
    generate_single_audio("translated.srt", "voxcpm_final_khmer.mp3", reference_audio=reference)
