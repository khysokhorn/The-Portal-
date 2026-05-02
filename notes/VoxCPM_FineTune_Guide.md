# 🚀 Beginner's Guide: Fine-Tuning VoxCPM for TVB Voices

Fine-tuning is the process of taking a "pre-trained" model (like VoxCPM) and teaching it a specific style (like the unique theatrical Khmer dubbing of TVB).

For an absolute beginner, the secret to success is **90% data preparation** and **10% training**.

---

## 🏗️ Phase 1: Preparing Your TVB Dataset

The model learns by looking at "pairs" of audio and text. You need about **30 minutes to 2 hours** of high-quality audio for a great result.

### 1. Source Separation (CRITICAL)

TVB movies have constant background music. **VoxCPM cannot learn a voice properly if there is music in the background.**

- **Tool:** Use [Ultimate Vocal Remover (UVR5)](https://ultimatevocalremover.com/).
- **Model:** Select `MDX-Net: Kim_Vocal_2` for the best result.
- **Goal:** You want a folder full of `.wav` files that contain **only** the voice.

### 2. Audio Trimming & Slicing

Large 10-minute files won't work. You must slice your audio into short clips:

- **Duration:** 3 to 10 seconds per clip.
- **Silence:** Trim any silence at the beginning or end (keep it under 0.5s).
- **Tool:** You can use **Audacity** (manual) or a script to auto-slice on silences.

### 3. Transcription (STT)

Each audio clip needs an exact transcript of what is being said in Khmer.

- **Tool:** Use [OpenAI Whisper](https://github.com/openai/whisper). It is very accurate for Khmer.
- **Result:** You should have a list where `audio_1.wav` matches `"សួស្តីបងប្អូន..."`.

---

## 📂 Phase 2: Organizing the Data

VoxCPM expects your data in a specific format called **JSONL**. Each line in a text file looks like this:

```json
{"audio": "path/to/tvb_clip_1.wav", "text": "អត្ថបទក្នុងឃ្លីបទី១..."}
{"audio": "path/to/tvb_clip_2.wav", "text": "អត្ថបទក្នុងឃ្លីបទី២..."}
```

---

## 💻 Phase 3: Hardware & Environment

Fine-tuning requires a powerful computer (specifically a **GPU**).

- **Minimum VRAM:** 24GB (An NVIDIA RTX 3090 or 4090 is perfect).
- **Cloud Option:** If you don't have a GPU, use **Google Colab** or **RunPod**.

### Setup Steps

1. **Install VoxCPM:** Clone the GitHub repo.
2. **Install Requirements:** Run `pip install -r requirements.txt`.
3. **LoRA vs Full:** For beginners, use **LoRA** (Low-Rank Adaptation). It is faster and uses less memory.

---

## ⚡ Phase 4: Running the Training

Once your data is ready, you run a command similar to this:

```bash
python scripts/train_voxcpm_finetune.py \
    --model_name "OpenBMB/VoxCPM-2B" \
    --data_path "your_tvb_data.jsonl" \
    --output_dir "./tvb_finetuned_model" \
    --batch_size 4 \
    --epochs 2 \
    --lr 1e-4
```

---

## 🏁 Phase 5: Testing Your Model

After training (which might take 1–3 hours), you will have a "Checkpoint".

1. Load this checkpoint in your VoxCPM interface.
2. Generate speech using your new TVB model.
3. You will notice it captures the **emotion** and **tone** much better than the base model!

---

## 💡 Pro Tips for TVB Style

- **Diversity:** Include clips of the character being happy, angry, and sad.
- **Clarity:** Avoid clips where two people are talking at the same time.
- **Consistency:** If you are training a "Male Hero" model, only include clips of that specific dubbing artist.

**Would you like me to help you write a script to auto-generate the JSONL file once you have your audio and text ready?**
