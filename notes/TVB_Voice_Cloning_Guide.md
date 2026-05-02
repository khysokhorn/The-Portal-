# TVB Voice Cloning Guide (Khmer)

This guide explains how to use the extracted references to clone the iconic TVB Khmer dubbing style using **VoxCPM**.

## 🎙️ Reference Files

The following clean reference clips are available in `references/extracted/`:

- `female_tvb_1.wav`: Young/sweet female lead style.
- `female_tvb_2.wav`: Dramatic/serious female style.
- `female_tvb_3.wav`: Sharp/argumentative female style (includes SRT transcript).

## 🎭 Style Prompts

Use these "Control Prompts" to enhance the theatrical feel of the TVB style:

### For Female Leads
>
> **Prompt:** *"A young female voice with a high-pitched, sweet, and crystal-clear tone. Very expressive and emotional, classic 90s TVB dubbing style."*

### For Male Leads
>
> **Prompt:** *"A heroic and mature male voice, deep and resonant. High energy and expressive, slightly theatrical martial arts dubbing style."*

## 🛠️ Commands for VoxCPM

### Basic Cloning (Zero-Shot)

```bash
voxcpm design \
  --text "សួស្តី! ថ្ងៃនេះខ្ញុំពិតជាសប្បាយចិត្តណាស់។" \
  --control "A young female voice, high-pitched and sweet, TVB style." \
  --output result.wav
```

### Ultimate Cloning (Audio + Transcript)

For the best results with `female_tvb_3.wav`, use the transcript:

```bash
voxcpm clone \
  --audio "references/extracted/female_tvb_3.wav" \
  --transcript "តួលេខតែងតែបង្ហាញនូវការកុហក បើមានខ្សែរយៈខ្ញុំក៏មិនបាច់ឈឺក្បាលទេ គ្រាន់តែឲ្យពួកគេរំលាយរឿងអាស្រូវ លោកគ្រូនឹងបានចេញពីគុក។" \
  --text "Your new Khmer dialogue here..." \
  --output tvb_clone_result.wav
```

## ⚙️ Using the Engine

If you find new YouTube clips, use the scripts in the `engine/` folder:

1. **Detect Gender:** `python3 engine/gender_detect.py new_audio.wav`
2. **Clean Vocals:** `python3 engine/vocal_sep.py noisy_clip.wav clean_voice.wav`
