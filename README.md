# 🔐 CIPHER OS — Local Multi-Agent AI Operating System

> *"Not a chatbot. Not a wrapper. A thinking machine running entirely on your hardware."*

Cipher is a fully offline, locally-running **Multi-Agent AI OS** built in Python. It converts unstructured voice and text input into deterministic system actions using a hybrid pipeline of rule-based skill execution and LLM reasoning — with no cloud, no API keys, and no internet required.

Dual-interface: control Cipher from the **terminal** (Spacebar voice / T-key text) or the **Web UI** served over your local network — accessible from any device on the same hotspot.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Ollama](https://img.shields.io/badge/Ollama-deepseek--r1:1.5b-green?style=flat-square)
![Whisper](https://img.shields.io/badge/Whisper-faster--whisper-orange?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-5500-black?style=flat-square&logo=flask)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)
![Android](https://img.shields.io/badge/Android-ADB_Bridge-brightgreen?style=flat-square)
![RAM](https://img.shields.io/badge/Engine-16GB_Uncapped-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

---

## 🎬 System Boot Sequence

```
╔══════════════════════════════════════════════════════╗
║              CIPHER OS  — BOOTING                   ║
╚══════════════════════════════════════════════════════╝

[FAST BOOT] Parallel skill loading initiated (14 workers)...
>> Core Agent           : ONLINE
>> Turbo Brain          : ONLINE  (deepseek-r1:1.5b via Ollama)
>> Autonomous Coder     : ONLINE  (FIM Patching + Memory Vault)
>> Plagiarism Guardian  : ONLINE  (Academic Weapon Active)
>> Mobile Bridge        : ONLINE  (ADB Hotspot)
>> Vision Protocol      : ONLINE
>> Security Guardian    : ONLINE
>> Git Commander        : ONLINE
>> Knowledge Forge      : ONLINE
>> Ghost Handler        : ONLINE  (Sentinel Mode Active)
>> Web Scout            : ONLINE
[BOOT] 45 skills loaded in 1.8s

>> Flask server → http://0.0.0.0:5500
>> SPACE = Voice | T = Text | Q = Quit

>> Heard: fix the error in safenav
   Skill → autonomous_coder.py | FIM patch generated. Awaiting approval.

>> Heard: check plagiarism in thesis.txt
   Skill → plagiarism_guardian.py | 3-phase scan initiated...

>> Heard: what is transformer architecture
   Brain → deepseek-r1:1.5b | Reasoning...
   Cipher: A transformer uses self-attention to process sequences in parallel...
```

---

## 🧠 Architecture Overview

Cipher is built around a **hybrid deterministic + generative pipeline**. The system never relies on the LLM when a deterministic skill can handle the job — keeping execution fast, predictable, and hallucination-free.

```
┌──────────────────────────────────────────────────────────┐
│                      INPUT LAYER                         │
│   SPACE (Voice) │ T-Key (Text) │ Web UI / Mobile         │
└───────────────────────────┬──────────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │    main.py      │  Dual-thread: Flask + Terminal
                   │   (Router)      │  keyboard.read_event() loop
                   └────────┬────────┘
                            │
          ┌─────────────────▼──────────────────┐
          │         skills_manager.py           │  Auto-discovers all skills
          │      Fuzzy match → dispatch         │  thefuzz + class-based routing
          └──┬──────────────────────────────┬──┘
             │                              │
    ┌────────▼────────┐          ┌──────────▼──────────┐
    │  Skill Layer    │          │    Fallback: LLM     │
    │  (45+ modules)  │          │  think.py + Ollama   │
    │  Deterministic  │          │  deepseek-r1:1.5b    │
    └────────┬────────┘          └──────────┬───────────┘
             │                              │
          ┌──▼──────────────────────────────▼──┐
          │              speak.py               │  Neural TTS + Web response
          └─────────────────────────────────────┘
```

### Core Design Principles

| Principle | Implementation |
| :--- | :--- |
| **Offline-first** | deepseek-r1:1.5b via Ollama — zero mandatory cloud dependency |
| **Determinism** | Skills fire before the LLM is ever consulted |
| **Parallel boot** | `fast_loader.py` loads all 45 skills concurrently in ~1.8s |
| **LRU caching** | Repeated queries served from cache — no re-inference |
| **Streaming LLM** | Token-by-token streaming from Ollama for near-zero latency |
| **Adaptive listening**| VAD-calibrated mic threshold — never cuts you off mid-thought |
| **Memory** | SQLite-backed `memory.db` for persistent conversation context |
| **Ghost Mode** | Invisible background operation via `sentinel.py` |

---

## ✨ Skill Modules (45+)

Cipher's capabilities are organized into skill organs — each a self-contained Python class auto-discovered at boot.

### 🖥️ System Control
- Volume, brightness, screenshots, shutdown, restart, lock screen
- CPU, RAM, disk usage monitoring (`system_monitor.py`)
- Process management — kill, list, prioritize (`process_manager.py`)
- Environment variable management (`env_manager.py`)
- Clipboard read, write, sync (`clipboard_sync.py`)
- Window management — minimize, maximize, close (`window.py`)
- Fast boot profiles (`fast_boot.py`)

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
- **Turbo Brain** — enhanced LLM reasoning with streaming + LRU cache (`turbo_brain.py`)
- **Coding Swarm** — multi-agent code generation using parallel LLM workers (`codeskills/swarm.py`)
- **Autonomous Coder** — Level 5 AI Software Engineer with FIM patching, Memory Vault, Sandbox Shield, and Kill-Switch approval (`autonomous_coder.py`)
- **Autonomous Debugger** — self-directed bug detection and fix loop (`autonomous_debugger.py`)
- **Vector Memory** — semantic search over conversation history (`vector_memory.py`)
- **Knowledge Forge** — builds and queries a persistent local knowledge base (`knowledge_forge.py`)
- **Voice Neural** — Microsoft Edge Neural TTS (en-GB-RyanNeural) via edge-tts (`voice_neural.py`)

### 🎓 Academic Weapons
- **Plagiarism Guardian** — 3-phase plagiarism detection: n-gram lexical hashing, semantic cosine similarity via sentence-transformers, live internet cross-check via DuckDuckGo + BeautifulSoup, and surgical AI rewrite of flagged sentences (`plagiarism_guardian.py`)
- **Study Vault** — personal notes, flashcard system, spaced repetition (`study_vault.py`)
- **Document Intel** — read and summarize documents (PDF, DOCX, TXT) by voice (`document_intel.py`)
- **Humanizer** — AI text humanization and style transformation (`humanizer.py`)

### 🔍 Research & Intelligence
- Wikipedia summaries
- Google search and Google News
- YouTube search
- **Web Scout** — deep web scraping and LLM summarization (`web_scout.py`)
- **Market Analyst** — financial data, moving averages, trend analysis via Yahoo Finance (`market_analyst.py`)
- **Research V2** — DuckDuckGo + scrape + TurboBrain synthesis pipeline (`research_v2.py`)

### 💻 Coding & Dev Tools
- Boilerplate generation — Python, JS, React, HTML, Django, FastAPI
- Run Python/JS files by voice (`codeskills/executor.py`)
- Stack Overflow search
- VS Code launcher
- **Git Commander** — voice-controlled git: commit, push, pull, status, log (`git_commander.py`)
- **OS Automator** — natural language → Python script → execute with 3-layer safety rails (`os_automator.py`)

### 🗂️ Files & Knowledge
- File create, delete, move, rename (`files.py`)
- **File Vault** — AES-256 encrypted local file storage (`file_vault.py`)
- **Notes** — quick note capture with SQLite backend (`notes.py`)

### 🛡️ Security & Network
- **Security Guardian** — port scanning, process auditing, firewall status (`security_guardian.py`)
- **Network Pro** — diagnostics, speed tests, IP info (`network_pro.py`)

### 💬 Communication
- **Email Pro** — Gmail compose and send (`email_pro.py`)
- **WhatsApp Pro** — ADB-based WhatsApp messaging — no Selenium, no browser (`whatsapp_pro.py`)
- Browser automation — Chrome, Firefox control (`browser.py`)

### 👁️ Vision
- **Vision Protocol** — screen/webcam capture + moondream vision model for image description (`vision_protocol.py`)
- **Vision** — basic image capture and analysis (`vision.py`)

### 🕒 Utilities & Media
- **Clock** — time, date, alarms, countdowns (`clock.py`)
- **Scheduler** — task scheduling (`scheduler.py`)
- **Media Forge** — FFmpeg-powered media playback and control (`media_forge.py`)
- **PPTX Forge** — voice → full PowerPoint presentation via python-pptx (`pptx_forge.py`)
- **Data Forge** — matplotlib visualizations from voice (`data_forge.py`)
- **Image Forge** — AI image generation via Bing Image Creator (`image_forge.py`)
- **Hello** — greetings, personality, task-aware royal welcome (`hello.py`)
- **Motor** — system motor/automation control (`motor.py`)

### 👻 Ghost Mode (Invisible OS)
- **Sentinel** — background watchdog process (`sentinel.py`)
- **Ghost Handler** — invisible assistant layer, proactive notifications, screen context awareness (`core/ghost_handler.py`)

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Speech Recognition** | Faster-Whisper (base.en) with VAD + adaptive noise floor |
| **LLM Engine** | Ollama + deepseek-r1:1.5b (streaming, LRU cache) |
| **LLM Fallback** | Google Gemini 1.5 Flash (via google-genai SDK) |
| **Text-to-Speech** | pyttsx3 + edge-tts (Neural voice) |
| **Web Server** | Flask (port 5500, 0.0.0.0, CORS enabled) |
| **Terminal UI** | keyboard (SPACE = voice, T = text, Q = quit) |
| **Mobile Control** | ADB (USB + Hotspot wireless) |
| **System Control** | psutil, pyautogui, subprocess |
| **Semantic Search** | sentence-transformers (all-MiniLM-L6-v2) |
| **Memory** | SQLite (`cipher_data/memory.db`) |
| **Code Patching** | FIM (Fill-in-the-Middle) via deepseek-coder:6.7b |

---

## 📁 Project Structure

```
cipher/
│
├── main.py                      # Entry point — dual-thread (Flask + Terminal)
├── config.py                    # Global configuration
├── communication.py             # Shared communication utilities
├── sentinel.py                  # Ghost Mode background watchdog
├── requirements-local.txt       # Dependencies
├── .env                         # Environment variables (gitignored)
│
├── core/                        # System organs
│   ├── agent.py                 # Central agent coordinator
│   ├── context.py               # Conversation context manager
│   ├── fast_loader.py           # Parallel skill loader (14 concurrent workers)
│   ├── ghost_handler.py         # Invisible assistant layer
│   ├── listen.py                # Faster-Whisper + VAD + adaptive threshold
│   ├── skills_manager.py        # Auto-discovers & fuzzy-routes to skills
│   ├── speak.py                 # pyttsx3 TTS + Neural voice output
│   └── think.py                 # Ollama LLM brain (streaming + Gemini fallback)
│
├── skills/                      # 45+ auto-loaded skill modules
│   ├── autonomous_coder.py      # Level 5 AI Software Engineer (FIM + Vault + Sandbox)
│   ├── autonomous_debugger.py   # Self-directed debug agent
│   ├── plagiarism_guardian.py   # 3-phase plagiarism detection + surgical rewrite
│   ├── humanizer.py             # AI text humanization
│   ├── turbo_brain.py           # Enhanced LLM reasoning
│   ├── knowledge_forge.py       # Local knowledge base
│   ├── vector_memory.py         # Semantic memory search
│   ├── voice_neural.py          # Edge Neural TTS
│   ├── vision.py                # Image capture & analysis
│   ├── vision_protocol.py       # Vision model integration
│   ├── system.py                # OS control
│   ├── system_monitor.py        # CPU/RAM/disk monitoring
│   ├── mobile.py                # ADB Android control
│   ├── mobile_hotspot.py        # Wi-Fi ADB bridge
│   ├── apps.py                  # App launcher
│   ├── browser.py               # Browser automation
│   ├── files.py                 # File management
│   ├── file_vault.py            # AES-256 encrypted storage
│   ├── git_commander.py         # Voice git operations
│   ├── os_automator.py          # NL → Python script executor
│   ├── process_manager.py       # Process control
│   ├── env_manager.py           # Environment variables
│   ├── clipboard_sync.py        # Clipboard management
│   ├── window.py                # Window management
│   ├── research.py              # Wikipedia, Google, News
│   ├── research_v2.py           # Multi-source research pipeline
│   ├── web_scout.py             # Deep web scraping
│   ├── market_analyst.py        # Financial queries (Yahoo Finance)
│   ├── coding.py                # Code generation
│   ├── document_intel.py        # Document reading & summarization
│   ├── study_vault.py           # Notes & flashcards
│   ├── notes.py                 # Quick note capture (SQLite)
│   ├── security_guardian.py     # Security monitoring
│   ├── network_pro.py           # Network diagnostics
│   ├── email_pro.py             # Gmail compose
│   ├── whatsapp_pro.py          # WhatsApp messaging (ADB)
│   ├── media.py                 # Media control
│   ├── media_forge.py           # FFmpeg media playback
│   ├── pptx_forge.py            # Voice → PowerPoint generator
│   ├── data_forge.py            # matplotlib chart generator
│   ├── image_forge.py           # Bing AI image generation
│   ├── scheduler.py             # Task scheduler
│   ├── clock.py                 # Time, alarms, countdowns
│   ├── fast_boot.py             # Boot profiles
│   ├── motor.py                 # System motor/automation
│   └── hello.py                 # Greetings & personality
│
├── codeskills/                  # Code execution agents
│   ├── swarm.py                 # Multi-agent coding swarm
│   ├── executor.py              # Python/JS file runner
│   └── debugger.py              # Autonomous debug engine
│
├── cipher_data/                 # Runtime data (gitignored)
│   ├── memory.db                # Persistent SQLite memory
│   ├── command_history.json     # Command log
│   └── last_seen.png            # Vision capture cache
│
├── cipher_knowledge/            # Local knowledge base (gitignored)
├── generated_code/              # Coding swarm output (gitignored)
├── temp_vision/                 # Vision captures (gitignored)
├── data/
│   ├── contacts.json            # Phone contacts (gitignored)
│   └── logs.txt                 # System logs
│
└── web/
    ├── index.html               # Landing page (boot sequence + skill grid)
    ├── chat.html                # Main OS dashboard
    ├── css/
    │   ├── index.css            # Landing page styles
    │   └── chat.css             # Dashboard styles
    └── js/
        ├── index.js             # Landing page logic
        └── chat.js              # Dashboard logic + diff card + plagiarism UI
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

**3. Pull the AI models**
```bash
ollama pull deepseek-r1:1.5b       # Core brain (required)
ollama pull deepseek-coder:6.7b    # Autonomous Coder (recommended)
ollama pull moondream               # Vision Protocol (optional)
```

**4. Configure**
```python
# config.py
ASSISTANT_NAME = "Cipher"
LLM_MODEL      = "deepseek-r1:1.5b"
WHISPER_SIZE   = "base.en"
FLASK_PORT     = 5500
```

**5. Add your contacts (optional)**
```json
// data/contacts.json
{
  "mom": "+91XXXXXXXXXX",
  "dad": "+91XXXXXXXXXX"
}
```

**6. Configure environment (optional — for Gemini fallback)**
```env
# .env
GEMINI_API_KEY=your_key_here
BING_COOKIE=your_bing_cookie_here
```

**7. Launch Cipher**
```bash
# Terminal 1 — Start Ollama
ollama serve

# Terminal 2 — Start Cipher
python main.py
```

Cipher boots all 45+ skills in parallel and exposes two interfaces:
- **Terminal** — `SPACE` for voice, `T` for text, `Q` to quit
- **Web UI** — `http://localhost:5500` or `http://<your-ip>:5500` from any device on the network

---

## 🎮 Usage

### Terminal Mode

| Key | Action |
| :--- | :--- |
| **SPACE** | Activate voice input (Faster-Whisper + VAD) |
| **T** | Type a command directly |
| **Q** | Shutdown Cipher safely |
### Web UI Mode

Open `http://localhost:5500` in any browser. The cyberpunk-themed dashboard connects to the same Flask backend — accessible from your phone, tablet, or another PC on the same network.

### Example Commands

| Voice / Text Command | Skill | Action |
|---|---|---|
| *"open instagram"* | mobile.py | Opens Instagram on Android |
| *"call mom"* | mobile.py | Dials via ADB |
| *"phone battery"* | mobile.py | Returns battery % |
| *"git status"* | git_commander.py | Runs git status |
| *"git commit fixed auth bug"* | git_commander.py | Commits with message |
| *"fix safenav"* | autonomous_coder.py | FIM patch + Kill-Switch approval |
| *"activate auto-heal on votehub"* | autonomous_coder.py | Watchdog monitors project |
| *"scan errors in cipher"* | autonomous_coder.py | Batch-scans entire project |
| *"check plagiarism in thesis.txt"* | plagiarism_guardian.py | 3-phase scan + rewrites |
| *"compare essay.txt with source.txt"* | plagiarism_guardian.py | Document vs document |
| *"create presentation about ML"* | pptx_forge.py | Generates full .pptx |
| *"visualize cpu"* | data_forge.py | Dual-panel system graph |
| *"generate image of a cyberpunk city"* | image_forge.py | Bing AI art |
| *"deep research quantum computing"* | research_v2.py | Web scrape + LLM synthesis |
| *"automate move all PDFs to Documents"* | os_automator.py | NL → script → execute |
| *"system info"* | system_monitor.py | CPU, RAM, disk stats |
| *"screenshot"* | system.py | Captures screen |
| *"volume 60"* | system.py | Sets volume to 60% |
| *"kill chrome"* | process_manager.py | Terminates process |
| *"what is transformer architecture"* | think.py | deepseek-r1 reasons it out |
| *"note meeting at 3pm"* | notes.py | Saves to SQLite |
| *"navigate to airport"* | mobile.py | Opens Google Maps |
| *"connect hotspot"* | mobile_hotspot.py | ADB over Wi-Fi |

---

## 📱 Mobile Setup (Android ADB)

### USB Mode
1. Settings → About Phone → Tap **Build Number** 7 times
2. Settings → Developer Options → Enable **USB Debugging**
3. Connect phone via USB cable
4. Accept the **"Allow USB debugging?"** popup
5. Verify: `adb devices`

### Hotspot Mode (Wireless ADB)
1. Connect phone via USB first and authorize
2. Say: *"connect hotspot"* — Cipher runs `adb tcpip 5555` and pairs wirelessly
3. Disconnect USB — mobile bridge stays active over Wi-Fi

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
        return None  # Return None → passes to next skill or LLM fallback
```

The `skills_manager.py` picks it up automatically. 🎉

---

## ⚙️ Configuration Reference

```python
# config.py
ASSISTANT_NAME  = "Cipher"
LLM_MODEL       = "deepseek-r1:1.5b"
WHISPER_SIZE    = "base.en"         # tiny.en = faster, base.en = more accurate
FLASK_HOST      = "0.0.0.0"
FLASK_PORT      = 5500
SAMPLE_RATE     = 16000
CHUNK_SIZE      = 1024
```

---

## 🏗️ System Design Notes

### Autonomous Coder — Level 5 AI Software Engineer
Built with insights from DeepSeek-Coder and InfCode architectures:
- **FIM (Fill-in-the-Middle)** — isolates the exact broken lines and patches surgically instead of rewriting entire files
- **Memory Vault** — persists every fix in `D:\Cipher Ai\codedebug\<project>\` with fixed/unfixed/updates/roadmap folders
- **Sandbox Shield** — tests every patch in a temp copy before touching live files
- **Kill-Switch** — voice announcement + Web UI diff card with Approve/Reject buttons before any file is overwritten
- **Auto-Heal Watchdog** — monitors project folders on every file save, auto-queues detected errors
- **Batch Queue** — scans entire project, fixes all errors in sequence

### Plagiarism Guardian — Academic Weapon
Three-phase detection pipeline with zero paid APIs:
- **Phase 1 (Lexical)** — n-gram fingerprinting with MD5 hashing catches exact copy-paste
- **Phase 2 (Semantic)** — `sentence-transformers` cosine similarity catches paraphrased plagiarism
- **Phase 3 (Internet)** — DuckDuckGo search + BeautifulSoup scrape cross-checks against live web
- **Phase 4 (Rewrite)** — Gemini / deepseek-r1 surgically rewrites flagged sentences with Apply buttons in Web UI

### Voice Engine Upgrades
- **Adaptive noise floor** — calibrates mic threshold to your room at boot
- **Pre-speech ring buffer** — never misses first syllable
- **2.5s silence tolerance** — pause to think without being cut off
- **Streaming LLM** — Cipher starts speaking before full response is generated
- **Interrupt flag** — say "stop" while Cipher is thinking

### Determinism vs Generation
The LLM is a fallback, not the controller. Skills always fire first — the LLM only handles what no skill matches. This eliminates hallucinations for system actions.

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