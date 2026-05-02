import librosa
import numpy as np
import json
import sys

def detect_gender_segments(audio_path, threshold=160):
    y, sr = librosa.load(audio_path)
    # Estimate pitch (F0)
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
    
    times = librosa.times_like(f0)
    
    segments = []
    current_gender = None
    start_time = 0
    
    for i in range(len(f0)):
        if not voiced_flag[i]:
            gender = 'silence'
        else:
            gender = 'female' if f0[i] > threshold else 'male'
            
        if gender != current_gender:
            if current_gender and current_gender != 'silence':
                segments.append({
                    'gender': current_gender,
                    'start': start_time,
                    'end': times[i]
                })
            start_time = times[i]
            current_gender = gender
            
    # Add last segment
    if current_gender and current_gender != 'silence':
        segments.append({
            'gender': current_gender,
            'start': start_time,
            'end': times[-1]
        })
        
    # Merge short segments and group by gender
    merged = []
    if not segments: return []
    
    curr = segments[0]
    for i in range(1, len(segments)):
        if segments[i]['gender'] == curr['gender'] and (segments[i]['start'] - curr['end'] < 0.5):
            curr['end'] = segments[i]['end']
        else:
            if curr['end'] - curr['start'] > 1.0: # Only keep segments > 1s
                merged.append(curr)
            curr = segments[i]
    if curr['end'] - curr['start'] > 1.0:
        merged.append(curr)
        
    return merged

if __name__ == "__main__":
    audio_file = sys.argv[1]
    res = detect_gender_segments(audio_file)
    print(json.dumps(res, indent=2))
