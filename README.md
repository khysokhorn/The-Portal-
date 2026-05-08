# Chat & Tech Notes

Welcome to your dedicated space for exploring the cutting edge of technology, open source, and entertainment.

## 🚀 Purpose

This project is designed for:

- **Chatting**: Discussing the latest trends in tech and open source.
- **Note Taking**: Documenting interesting findings, fun facts, and entertainment news.

## 🚫 Scope

This workspace is **not** for:

- Writing code.
- Debugging software.
- Technical implementation tasks.

## 📂 Structure

- `notes/`: Technology and Open Source notes.
- `entertainment/`: Fun, games, movies, and entertainment content.
- `skills/`: Custom instructions for Antigravity.

## 🛠 How to Use

Simply ask me about a new technology or share an open-source project you found. We can discuss it and I'll help you organize your thoughts into notes!

### 🔌 How to Start Claude Local

To use the official Claude CLI with your local models:

1. **Launch Proxy**: Open a terminal and run `cd chat && docker compose up -d`.
2. **Backend**: This proxy connects to the [Antigravity Manager Local Proxy](https://github.com/lbjlaq/Antigravity-Manager/agents?author=khysokhorn) using your local API key and server URL.

**Backend Config:**

- `LOCAL_API_KEY`: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

- `LOCAL_SERVER_URL`: `http://127.0.0.1:4000/v1/chat/completions`
