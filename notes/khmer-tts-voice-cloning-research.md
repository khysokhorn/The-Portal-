# Khmer Text-to-Speech (TTS) & Voice Cloning Research (2026)

This document outlines the state of Text-to-Speech (TTS) and voice cloning models with support for the Khmer language as of 2026. The landscape is currently divided between highly specialized commercial platforms that guarantee Khmer pronunciation and intonation accuracy, and powerful multilingual open-source frameworks capable of cross-lingual zero-shot cloning.

## 1. Commercial Platforms

Commercial options are best for production environments requiring immediate high accuracy, managed APIs, and minimal setup.

### **FineVoice**

- **Capabilities:** High-accuracy (~99%) Khmer pronunciation, capturing natural tone and emotion. Wait-time to clone is just 30 seconds using only a 10-second reference audio sample.
- **Key Feature:** Allows users to upload custom open-source `.pth` models trained via RVC (Retrieval-based Voice Conversion) V1 or V2 directly to their platform.
- **Best For:** Creators and developers looking to mix rapid zero-shot cloning with managed custom RVC model deployment.

### **Camb.ai (MARS8)**

- **Capabilities:** Powered by the new MARS8 speech model, Camb.ai is designed specifically for natural emotion and production-level audio.
- **Key Feature:** Offers strong zero-shot cross-lingual voice cloning right out of the box with dedicated Khmer support.
- **Best For:** High-end production use cases where emotional range and tone are paramount.

### **Verbatik AI**

- **Capabilities:** Provides standard Khmer text-to-speech base voices (male and female) alongside cross-lingual voice cloning.
- **Key Feature:** Specifically tailored for scaling localized content into the Cambodian market (e.g., long-form audiobooks).
- **Best For:** Long-form audio content and large-scale localization projects.

## 2. Open-Source Models (Commercial-Friendly Licenses)

For developers avoiding API costs and preferring self-hosted infrastructure, 2026 has introduced highly capable models. While not exclusively trained on Khmer, their zero-shot and cross-lingual capabilities allow them to handle low-resource languages effectively.

### **Chatterbox**

- **License:** MIT
- **Capabilities:** The premier open-source voice cloning model of 2026. Matches or exceeds commercial giants in blind preference tests.
- **Key Feature:** Fully free for commercial deployment with state-of-the-art zero-shot voice cloning.
- **Best For:** Enterprise-grade self-hosted voice cloning.

### **Qwen3-TTS**

- **License:** Apache 2.0 (Released early 2026)
- **Capabilities:** Delivers advanced, localized voice cloning logic with high cross-lingual fidelity.
- **Best For:** Integrating deeply into modern AI agent pipelines requiring robust voice synthesis.

### **Fish Audio S2 / S2 Pro**

- **License:** Open weights (Check specific terms per commercial usage)
- **Capabilities:** Trained on over 10 million hours of audio. Native speech synthesis across 80+ languages.
- **Key Feature:** Exceptional cross-lingual generalization allowing an English voice sample to natively synthesize Khmer text.

### **Kokoro (v1.0)**

- **License:** Apache 2.0
- **Capabilities:** An incredibly lightweight model (82M parameters).
- **Key Feature:** Runs efficiently on basic CPUs or edge devices.
- **Best For:** Local, edge, mobile deployment, or offline applications in bandwidth-constrained areas. (Note: Relies mostly on direct TTS rather than fast-cloning pipelines).

### **XTTS-v2**

- **License:** Open-source (Community maintaned)
- **Capabilities:** 6-second cross-lingual voice cloning.
- **Key Feature:** Though the original parent company shut down, the GitHub community has fully embraced and maintained the project.

## 3. Summary Recommendations

- **For pure ease of use and guaranteed Khmer accuracy:** Use **FineVoice** or **Camb.ai**. FineVoice is ideal if mixing zero-shot with uploaded RVC models, while Camb.ai is excellent for emotional depth.
- **For a free, commercial-ready open-source pipeline:** Deploy **Chatterbox** or **Qwen3-TTS**. Both offer commercial-tier cloning quality completely for free.
- **For local Edge or Mobile deployment (e.g., local apps deployed in Cambodia):** Integrate **Kokoro (v1.0)** due to its unmatched efficiency and low resource requirements.
