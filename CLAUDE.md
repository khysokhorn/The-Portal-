# AITools Workspace

Welcome to the command center. This workspace is divided into three core pillars: **Chat**, **Usage Tools**, and **Entertainment**.

## 🏗️ Project Structure

-   **/chat**: AI Agent infrastructure and proxy configurations.
    -   *Primary Tool*: `claude_proxy.py` (The bridge for Claude Code).
-   **/tools**: Production and deployment utilities.
    -   *Primary Tool*: `upload_to_colab.py` (Secure bridge for Google Colab).
-   **/fun**: Entertainment and creative AI modules.
    -   *Planned*: YouTube processing, Voice Cloning (VoxCPM), and Media automation.

## 🛠 Usage Instructions

### Chat (Local LLM)
To start the local Claude environment:
1. Navigate to `/chat`
2. Run `docker compose up -d`
3. Launch Claude with the `claude-local` alias.

### Tools (Colab Bridge)
To move files to the cloud for heavy processing:
1. Place files in `/tools`
2. Run `python engine/upload_to_colab.py`
3. Copy the generated `wget` commands to your Colab notebook.

## 🎨 Design Principles
- **Premium Code**: All Python scripts must be modular, documented, and use clean error handling.
- **Agentic Ready**: Every tool should be "agent-friendly"—meaning a subagent can understand and run it easily.
- **Aesthetic UI**: Any web interfaces created (Streamlit/FastAPI) should use dark mode, glassmorphism, and premium gradients.

## 🤖 Subagent Guidelines
- **@architect**: Use for project-wide structural decisions.
- **@coder**: Use for implementing new features in `/tools` or `/fun`.
- **@entertainment-specialist**: Expert in media processing and Khmer localization.
