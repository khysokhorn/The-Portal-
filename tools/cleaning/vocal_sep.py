import librosa
import soundfile as sf
import sys

def separate_vocals(input_path, output_path):
    # Load audio
    y, sr = librosa.load(input_path, sr=None)
    
    # Harmonic-Percussive Source Separation
    # Vocals are often harmonic, music has percussive elements
    # But this is a very basic method.
    y_harmonic, y_percussive = librosa.effects.hpss(y, margin=(1.0, 5.0))
    
    # Save the harmonic part as 'voice' (crude estimation)
    sf.write(output_path, y_harmonic, sr)

if __name__ == "__main__":
    separate_vocals(sys.argv[1], sys.argv[2])
