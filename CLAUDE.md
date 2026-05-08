# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context & AI Role

- **Dual Nature**: The `README.md` and `skills/tech-notes/SKILL.md` intentionally instruct the primary AI to *avoid writing code* and focus on tech/entertainment notes. However, as Claude Code, you are expected to ignore this constraint when you are explicitly asked to maintain, debug, or write the infrastructure code in the `chat/` or `tools/` directories.

## Strict Scope & Permissions

- **Workspace Only**: Do NOT access or modify any files outside of the current project directory (`/Users/sokhorn/Sokhorn/Project/AITools/Chat`).
- **No System Files**: Do NOT attempt to read or edit shell configuration files (e.g., `.zshrc`, `.bashrc`), system-level settings, or global application support files (e.g., `~/Library/Application Support/`).
- **Explicit Permission**: If a task requires changes to environment variables or system-wide settings, you MUST explain the necessity and wait for explicit, per-file confirmation before proceeding.

## High-Level Architecture

- **Claude Local Proxy (`chat/`)**: A FastAPI web application (`claude_proxy.py`) that proxy-translates Anthropic API requests into an OpenAI-compatible format to route to a local AI server backend.
- **Audio/Dataset Processing Tools (`tools/`)**: A Python-based toolkit for processing audio files. Includes scripts for vocal separation (`vocal_sep.py`), whisper transcription (`whisper_transcriber.py`), and dataset slicing based on silence (`tvb_dataset_slicer.py`). Specifically used for prepping voice cloning datasets (VoxCPM) mimicking TVB dubbing styles.
- **Notes & Content (`notes/`, `entertainment/`)**: Markdown documents containing technology research, fun facts, and guides (like the VoxCPM fine-tuning guide).
- **Skills (`skills/`)**: AI persona modifiers and custom prompt instructions that enforce roles for other AI agents interacting in workflows.

## Common Development Commands

### Claude API Proxy

- **Launch via Docker**:

  ```bash
  cd chat && docker compose up -d
  ```

- **Launch Natively**:

  ```bash
  cd chat && uvicorn claude_proxy:app --host 0.0.0.0 --port 4000
  ```

- **Proxy Configuration**: Requires `chat/.env` constructed from `chat/.env.example` configuring `LOCAL_API_KEY` and `LOCAL_SERVER_URL`.

### Running Python Tools

- Python utility scripts are executed directly, e.g.,

  ```bash
  python tools/dataset/tvb_dataset_slicer.py <input.wav> <output_dir>
  ```

- **Dependencies**: The codebase does not currently aggregate dependencies in a standard file. Depending on the script executed, you may need `fastapi`, `uvicorn`, `httpx`, `python-dotenv`, `librosa`, or `soundfile`.
