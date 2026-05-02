import whisper
import librosa
import os
import sys

def retranscribe_folder(folder_path, model_size="base"):
    print(f"🧠 Loading Whisper model ({model_size})...")
    model = whisper.load_model(model_size)
    
    print(f"📂 Scanning folder: {folder_path}")
    
    # Get all WAV files
    wav_files = [f for f in os.listdir(folder_path) if f.endswith(".wav")]
    wav_files.sort()
    
    total = len(wav_files)
    for i, wav_name in enumerate(wav_files):
        wav_path = os.path.join(folder_path, wav_name)
        txt_path = wav_path.replace(".wav", ".txt")
        
        print(f"[{i+1}/{total}] Transcribing: {wav_name}...")
        
        try:
            # Load audio using librosa (more robust than whisper's internal ffmpeg call)
            audio, sr = librosa.load(wav_path, sr=16000) # Whisper expects 16kHz
            
            # Transcribe in Khmer
            result = model.transcribe(audio, language="km")
            correct_text = result["text"].strip()
            
            # Overwrite the text file with the "truth"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(correct_text)
        except Exception as e:
            print(f"⚠️ Error transcribing {wav_name}: {e}")
            
    print(f"\n✨ DONE! All transcripts in {folder_path} have been corrected by AI.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 engine/dataset/whisper_transcriber.py <folder_or_file> [model_size]")
        sys.exit(1)
        
    input_path = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"
    
    if os.path.isdir(input_path):
        retranscribe_folder(input_path, model_size)
    else:
        # Single file mode
        print(f"🧠 Loading Whisper model ({model_size})...")
        model = whisper.load_model(model_size)
        print(f"🎬 Transcribing file: {input_path}")
        
        audio, sr = librosa.load(input_path, sr=16000)
        result = model.transcribe(audio, language="km")
        
        txt_path = input_path.replace(".wav", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result["text"].strip())
            
        print(f"✨ DONE! Transcript saved to: {txt_path}")
