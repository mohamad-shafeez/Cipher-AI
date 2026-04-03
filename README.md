# 🔐 CIPHER — Local Multi-Agent AI Operating System

> *"Not a chatbot. Not a wrapper. A thinking machine running entirely on your hardware."*

Cipher is a fully offline, locally-running **Multi-Agent AI OS** built in Python. It converts unstructured voice and text input into deterministic system actions using a hybrid pipeline of rule-based skill execution and LLM reasoning — with no cloud, no API keys, and no internet required.

Dual-interface: control Cipher from the **terminal** (Spacebar voice / T-key text) or the **Web UI** served over your local network — accessible from any device on the same hotspot.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Ollama](https://img.shields.io/badge/Ollama-deepseek--r1:1.5b-green?style=flat-square)
![Whisper](https://img.shields.io/badge/Whisper-faster--whisper-orange?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-5500-black?style=flat-square&logo=flask)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)
![Android](https://img.shields.io/badge/Android-ADB_Bridge-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

---

## 🎬 System Boot Sequence

```
╔══════════════════════════════════════════╗
║         CIPHER SYSTEM ONLINE            ║
╚══════════════════════════════════════════╝

[FAST BOOT] Parallel skill loading initiated...
>> Core Agent        : ONLINE
>> Turbo Brain       : ONLINE  (deepseek-r1:1.5b via Ollama)
>> Mobile Bridge     : ONLINE  (ADB Hotspot)
>> Vision Protocol   : ONLINE
>> Security Guardian : ONLINE
>> Git Commander     : ONLINE
>> Knowledge Forge   : ONLINE
>> Web Scout         : ONLINE
[BOOT] 35 skills loaded in 1.8s

>> Flask server running on http://0.0.0.0:5500
>> SPACE = Voice | T = Text | Q = Quit

>> Heard: open instagram
   Skill → mobile.py | Action: Opening Instagram on your phone.

>> Heard: debug my code
   Skill → autonomous_debugger.py | Swarm agents dispatched...

>> Heard: what is transformer architecture
   Brain → deepseek-r1:1.5b | Reasoning...
   Cipher: A transformer uses self-attention to process sequences in parallel...
```

---

## 🧠 Architecture Overview

Cipher is built around a **hybrid deterministic + generative pipeline**. The system never relies on the LLM when a deterministic skill can handle the job — keeping execution fast, predictable, and hallucination-free.

```
┌─────────────────────────────────────────────────────┐
│                   INPUT LAYER                       │
│   SPACE (Voice) │ T-Key (Text) │ Web UI / Mobile    │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │    main.py      │  Dual-thread: Flask + Terminal
              │   (Router)      │  keyboard.read_event() loop
              └────────┬────────┘
                       │
         ┌─────────────▼──────────────┐
         │      skills_manager.py      │  Auto-discovers all skills
         │   Fuzzy match → dispatch    │  thefuzz + class-based routing
         └──┬──────────────────────┬──┘
            │                      │
   ┌────────▼───────┐    ┌─────────▼──────────┐
   │  Skill Layer   │    │   Fallback: LLM     │
   │  (35+ modules) │    │  think.py + Ollama  │
   │  Deterministic │    │  deepseek-r1:1.5b   │
   └────────┬───────┘    └─────────┬───────────┘
            │                      │
         ┌──▼──────────────────────▼──┐
         │         speak.py           │  pyttsx3 TTS + Web response
         └────────────────────────────┘
```

### Core Design Principles

| Principle | Implementation |
|---|---|
| **Offline-first** | deepseek-r1:1.5b via Ollama — zero cloud dependency |
| **Determinism over generation** | Skills fire before LLM is ever consulted |
| **Parallel boot** | `fast_loader.py` loads all 35 skills concurrently |
| **LRU caching** | Repeated queries served from cache, no re-inference |
| **Streaming LLM** | Token-by-token streaming from Ollama for low latency |
| **Memory** | SQLite-backed `memory.db` for persistent conversation context |

---

## ✨ Skill Modules (35+)

Cipher's capabilities are organized into skill organs — each a self-contained Python class auto-discovered at boot.

### 🖥️ System Control
- Volume, brightness, screenshots, shutdown, restart, lock screen
- CPU, RAM, disk usage monitoring (`system_monitor.py`)
- Process management — kill, list, prioritize (`process_manager.py`)
- Environment variable management (`env_manager.py`)
- Clipboard read, write, sync (`clipboard_sync.py`)
- Window management — minimize, maximize, close (`window.py`)

### 📱 Mobile Bridge (Android via ADB)
- Open any app by voice — Instagram, WhatsApp, YouTube, Spotify
- Make calls and send SMS
- WhatsApp messages via ADB (`whatsapp_pro.py`)
- Camera control — photo, video
- Set alarms and timers
- Google Maps navigation
- Phone battery status
- **Mobile Hotspot** — connects phone over Wi-Fi via ADB, no USB required (`mobile_hotspot.py`)

### 🤖 AI & Reasoning
- **Turbo Brain** — enhanced LLM reasoning layer (`turbo_brain.py`)
- **Coding Swarm** — multi-agent code generation using parallel LLM workers (`codeskills/swarm.py`)
- **Autonomous Debugger** — self-directed bug detection and fix loop (`autonomous_debugger.py`, `codeskills/debugger.py`)
- **Vector Memory** — semantic search over conversation history (`vector_memory.py`)
- **Knowledge Forge** — builds and queries a local knowledge base (`knowledge_forge.py`)
- **Voice Neural** — enhanced voice processing layer (`voice_neural.py`)

### 🔍 Research & Intelligence
- Wikipedia summaries
- Google search and Google News
- YouTube search
- **Web Scout** — deep web scraping and summarization (`web_scout.py`)
- **Market Analyst** — financial data queries (`market_analyst.py`)
- **Research V2** — enhanced multi-source research pipeline (`research_v2.py`)

### 💻 Coding Assistant
- Boilerplate generation — Python, JS, React, HTML, Django, FastAPI
- Run Python/JS files by voice (`codeskills/executor.py`)
- Copy code snippets to clipboard
- Stack Overflow search
- VS Code launcher
- **Git Commander** — voice-controlled git operations: commit, push, status, log (`git_commander.py`)

### 🗂️ Files & Knowledge
- File create, delete, move, rename (`files.py`)
- **File Vault** — encrypted local file storage (`file_vault.py`)
- **Document Intel** — read and summarize documents by voice (`document_intel.py`)
- **Study Vault** — personal notes and flashcard system (`study_vault.py`)
- **Notes** — quick note capture with SQLite backend (`notes.py`)

### 🛡️ Security & Network
- **Security Guardian** — monitors system security events (`security_guardian.py`)
- **Network Pro** — network diagnostics, speed tests, IP info (`network_pro.py`)

### 💬 Communication
- **Email Pro** — Gmail compose and send (`email_pro.py`)
- **WhatsApp Pro** — enhanced WhatsApp messaging (`whatsapp_pro.py`)
- Browser automation — Chrome, Firefox control (`browser.py`)

### 👁️ Vision
- **Vision Protocol** — screen/image analysis using vision model (`vision_protocol.py`)
- **Vision** — basic image capture and analysis (`vision.py`)

### 🕒 Utilities
- **Clock** — time, date, alarms, countdowns (`clock.py`)
- **Scheduler** — task scheduling (`scheduler.py`)
- **Media Forge** — media playback and control (`media_forge.py`)
- **Hello** — greetings and Cipher's personality layer (`hello.py`)

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Speech Recognition | Faster-Whisper (base.en) |
| LLM Engine | Ollama + deepseek-r1:1.5b |
| Text-to-Speech | pyttsx3 |
| Web Server | Flask (port 5500, 0.0.0.0) |
| Terminal Interface | keyboard (SPACE = voice, T = text) |
| Mobile Control | ADB (USB + Hotspot) |
| System Control | psutil, pyautogui, subprocess |
| Memory | SQLite (`cipher_data/memory.db`) |
| Skill Loading | Parallel via `fast_loader.py` |
| Response Caching | LRU Cache (in-memory) |
| Fuzzy Matching | thefuzz |
| Architecture | Modular Auto-Discovery Plugin System |

---

## 📁 Project Structure

```
cipher/
│
├── main.py                    # Entry point — dual-thread (Flask + Terminal)
├── config.py                  # Global configuration
├── communication.py           # Shared communication utilities
├── requirements-local.txt     # Dependencies
├── .env                       # Environment variables
│
├── core/                      # System organs
│   ├── agent.py               # Central agent coordinator
│   ├── context.py             # Conversation context manager
│   ├── fast_loader.py         # Parallel skill loader (concurrent boot)
│   ├── listen.py              # Faster-Whisper voice input
│   ├── skills_manager.py      # Auto-discovers & routes to skills
│   ├── speak.py               # pyttsx3 TTS output
│   └── think.py               # Ollama LLM brain (streaming)
│
├── skills/                    # 35+ auto-loaded skill modules
│   ├── system.py              # OS control
│   ├── system_monitor.py      # CPU/RAM/disk monitoring
│   ├── mobile.py              # ADB Android control
│   ├── mobile_hotspot.py      # Wi-Fi ADB bridge
│   ├── apps.py                # App launcher
│   ├── browser.py             # Browser automation
│   ├── files.py               # File management
│   ├── file_vault.py          # Encrypted file storage
│   ├── git_commander.py       # Voice git operations
│   ├── process_manager.py     # Process control
│   ├── env_manager.py         # Environment variables
│   ├── clipboard_sync.py      # Clipboard management
│   ├── window.py              # Window management
│   ├── research.py            # Wikipedia, Google, News
│   ├── research_v2.py         # Enhanced multi-source research
│   ├── web_scout.py           # Deep web scraping
│   ├── market_analyst.py      # Financial queries
│   ├── coding.py              # Code generation
│   ├── autonomous_debugger.py # Self-directed debug agent
│   ├── turbo_brain.py         # Enhanced LLM reasoning
│   ├── knowledge_forge.py     # Local knowledge base
│   ├── vector_memory.py       # Semantic memory search
│   ├── voice_neural.py        # Enhanced voice processing
│   ├── document_intel.py      # Document reading & summarization
│   ├── study_vault.py         # Notes & flashcards
│   ├── notes.py               # Quick note capture (SQLite)
│   ├── vision.py              # Image capture & analysis
│   ├── vision_protocol.py     # Vision model integration
│   ├── security_guardian.py   # Security monitoring
│   ├── network_pro.py         # Network diagnostics
│   ├── email_pro.py           # Gmail compose
│   ├── whatsapp_pro.py        # WhatsApp messaging
│   ├── media.py               # Media control
│   ├── media_forge.py         # Media playback
│   ├── scheduler.py           # Task scheduler
│   ├── clock.py               # Time, alarms, countdowns
│   └── hello.py               # Greetings & personality
│
├── codeskills/                # Code execution agents
│   ├── swarm.py               # Multi-agent coding swarm
│   ├── executor.py            # Python/JS file runner
│   └── debugger.py            # Autonomous debug engine
│
├── cipher_data/
│   └── memory.db              # Persistent SQLite memory
│
├── cipher_knowledge/          # Local knowledge base store
├── generated_code/            # Output from coding swarm
├── data/
│   ├── contacts.json          # Phone contacts
│   └── logs.txt               # System logs
│
└── web/
    ├── index.html             # Landing page
    └── chat.html              # Web UI (served on port 5500)
```

---

## 🚀 Installation

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- ADB installed (for Android mobile control)
- Android phone with USB Debugging enabled

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/mohamad-shafeez/cipher-ai.git
cd cipher-ai
```

**2. Install dependencies**
```bash
pip install -r requirements-local.txt
```

**3. Pull the AI model**
```bash
ollama pull deepseek-r1:1.5b
```

**4. Configure**
```python
# config.py
ASSISTANT_NAME = "Cipher"
LLM_MODEL = "deepseek-r1:1.5b"
WHISPER_SIZE = "base.en"
FLASK_PORT = 5500
```

**5. Add your contacts (optional)**
```json
// data/contacts.json
{
  "mom": "+91XXXXXXXXXX",
  "dad": "+91XXXXXXXXXX"
}
```

**6. Launch Cipher**
```bash
# Terminal 1 — Start Ollama
ollama serve

# Terminal 2 — Start Cipher (boots Flask + Terminal simultaneously)
python main.py
```

Cipher will boot all 35+ skills in parallel and expose two interfaces:
- **Terminal** — `SPACE` for voice, `T` for text, `Q` to quit
- **Web UI** — `http://localhost:5500` or `http://<your-ip>:5500` from any device on the network

---

## 🎮 Usage

### Terminal Mode

| Key | Action |
|---|---|
| `SPACE` | Activate voice input (Faster-Whisper) |
| `T` | Type a command directly |
| `Q` | Shutdown Cipher |

### Web UI Mode

Open `http://localhost:5500` in any browser. The cyberpunk-themed chat interface connects to the same Flask backend — accessible from your phone, tablet, or another PC on the same network.

### Example Commands

| Voice / Text Command | Skill | Action |
|---|---|---|
| *"open instagram"* | mobile.py | Opens Instagram on Android |
| *"call mom"* | mobile.py | Dials via ADB |
| *"phone battery"* | mobile.py | Returns battery % |
| *"git status"* | git_commander.py | Runs git status |
| *"git commit fixed auth bug"* | git_commander.py | Commits with message |
| *"debug my code"* | autonomous_debugger.py | Launches debug swarm |
| *"create python file app"* | coding.py | Generates app.py boilerplate |
| *"system info"* | system_monitor.py | CPU, RAM, disk stats |
| *"screenshot"* | system.py | Captures screen |
| *"volume 60"* | system.py | Sets volume to 60% |
| *"kill chrome"* | process_manager.py | Terminates process |
| *"web search quantum computing"* | web_scout.py | Deep web search |
| *"what is transformer architecture"* | think.py | deepseek-r1 reasons it out |
| *"note meeting at 3pm"* | notes.py | Saves to SQLite |
| *"navigate to airport"* | mobile.py | Opens Google Maps |
| *"connect hotspot"* | mobile_hotspot.py | ADB over Wi-Fi |

---

## 📱 Mobile Setup (Android ADB)

### USB Mode
1. Settings → About Phone → Tap **Build Number** 7 times (enables Developer Options)
2. Settings → Developer Options → Enable **USB Debugging**
3. Connect phone via USB cable
4. Accept the **"Allow USB debugging?"** popup
5. Verify: `adb devices`

### Hotspot Mode (Wireless ADB)
1. Connect phone via USB first and authorize
2. Say: *"connect hotspot"* — Cipher runs `adb tcpip 5555` and pairs wirelessly
3. Disconnect USB — mobile bridge remains active over Wi-Fi

---

## 🔌 Adding Custom Skills

Drop a `.py` file in `skills/` — Cipher auto-discovers it at next boot. Zero config changes needed.

```python
# skills/my_skill.py

class MySkill:
    def __init__(self):
        print(">> My Skill: ONLINE")

    def execute(self, command: str) -> str | None:
        if "my trigger" in command.lower():
            return "My skill executed successfully."
        return None  # Return None to pass to next skill or LLM fallback
```

That's it. The `skills_manager.py` picks it up automatically. 🎉

---

## ⚙️ Configuration Reference

```python
# config.py

ASSISTANT_NAME  = "Cipher"
LLM_MODEL       = "deepseek-r1:1.5b"   # Ollama model
WHISPER_SIZE    = "base.en"             # tiny.en = faster, base.en = more accurate
FLASK_HOST      = "0.0.0.0"            # Binds to all interfaces (LAN access)
FLASK_PORT      = 5500
SAMPLE_RATE     = 16000
CHUNK_SIZE      = 1024
```

---

## 🏗️ System Design Notes

### Why deepseek-r1:1.5b?
Cipher runs on hardware with limited VRAM/RAM (8GB). deepseek-r1:1.5b was chosen for its strong logical reasoning capability at a small footprint — it handles the Coding Swarm and Autonomous Debugger tasks without memory pressure. The LLM is only invoked when no deterministic skill matches, keeping the system fast.

### Determinism vs Generation
A core design constraint: **the LLM is a fallback, not the controller**.

- **Deterministic Layer** — skill commands (`"open Instagram"`, `"git commit"`) always produce predictable, testable outputs
- **Generative Layer** — deepseek-r1:1.5b handles open-ended queries, explanations, and reasoning

This separation reduces hallucination risk and makes Cipher trustworthy for real system actions.

### Parallel Boot (`fast_loader.py`)
All 35+ skills are loaded concurrently using Python threading at startup. This reduces boot time significantly compared to sequential import.

### LRU Response Cache
Repeated queries (e.g., `"system info"`, `"what time is it"`) are served from an in-memory LRU cache — no re-inference, instant response.

### Streaming LLM Calls
Ollama responses stream token-by-token into both the terminal and the Web UI, so Cipher starts speaking before the full response is generated.

---

## 🙋 Developer

**Mohamad Shafeez**
- 🌐 [GitHub](https://github.com/mohamad-shafeez)
- 💼 [LinkedIn](https://linkedin.com/in/mohamad-shafeez)
- 📧 shafeezchappi18@gmail.com

Final-year BCA student at Srinivas University, Mangalore — building production-grade AI systems, backend applications, and local LLM infrastructure.

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<p align="center">
  <b>CIPHER — Built to run locally. Built to think clearly. Built to ship.</b><br/>
  <sub>Made by Mohamad Shafeez</sub>
</p>