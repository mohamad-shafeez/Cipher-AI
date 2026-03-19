# 🔐 CIPHER — AI Voice Assistant

> A fully offline, locally-running AI voice assistant built with Python, Faster-Whisper, and Ollama. Control your laptop and Android phone entirely by voice.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Ollama](https://img.shields.io/badge/Ollama-phi3.5-green?style=flat-square)
![Whisper](https://img.shields.io/badge/Whisper-faster--whisper-orange?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)
![Android](https://img.shields.io/badge/Android-ADB-brightgreen?style=flat-square)

---

## 🎬 Demo

```
========================================
   CIPHER SYSTEM ONLINE
========================================
>> Mobile Skills: ONLINE
>> System Skills: ONLINE (Windows)
>> App Skills: ONLINE
>> Research Skills: ONLINE
>> Press SPACE to give a command.
>> Waiting for SPACE key...
>> Voice Detected...
>> Detected language: en (confidence: 1.00)
Heard: open instagram
Skill Action: Opening instagram on your phone.

Heard: phone battery
Skill Action: Phone battery is at 87 percent.

Heard: what is machine learning
Cipher: Machine learning enables systems to learn from data without explicit programming.
```

---

## ✨ Features

### 🖥️ Laptop Control
- Volume, brightness, screenshots, shutdown, restart, lock screen
- CPU, RAM, disk usage monitoring
- Clipboard read/clear
- App launcher (VS Code, Chrome, Spotify, etc.)
- File management (create, delete, move, rename)
- Window management (minimize, maximize, close)

### 📱 Mobile Control (Android via ADB)
- Open any app by voice (Instagram, WhatsApp, YouTube, Spotify, etc.)
- Make calls and send SMS
- Send WhatsApp messages
- Camera control (photo, video)
- Set alarms
- Google Maps navigation
- Phone battery status

### 🧠 AI Brain
- Local LLM via Ollama (phi3.5) — 100% offline
- Conversation memory with context history
- Real-time battery and time awareness
- No API keys, no internet required

### 🔍 Research
- Wikipedia summaries
- Google search
- YouTube search
- Google News

### 💻 Coding Assistant
- Create boilerplate files (Python, JS, React, HTML, Django, FastAPI)
- Run Python/JS files by voice
- Copy code snippets to clipboard
- Search Stack Overflow
- Open VS Code

### 💬 Communication
- WhatsApp Web messaging
- Gmail compose
- SMS via ADB

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Speech Recognition | Faster-Whisper (base.en) |
| Wake Detection | Spacebar hotkey + thefuzz |
| AI Brain | Ollama + phi3.5 |
| Text-to-Speech | pyttsx3 |
| Mobile Control | ADB (Android Debug Bridge) |
| System Control | psutil, pyautogui, subprocess |
| Architecture | Modular Plugin System |

---

## 📁 Project Structure

```
cipher/
├── main.py                 # Entry point
├── config.py               # Configuration
├── requirements.txt        # Dependencies
│
├── core/
│   ├── listen.py           # Faster-Whisper voice input
│   ├── think.py            # Ollama LLM brain
│   ├── speak.py            # pyttsx3 TTS output
│   └── skills_manager.py   # Auto-discovers & loads skills
│
├── skills/
│   ├── mobile.py           # Android ADB control
│   ├── system.py           # Windows system control
│   ├── apps.py             # App launcher
│   ├── browser.py          # Web browser control
│   ├── coding.py           # Code assistant
│   ├── research.py         # Wikipedia, Google, YouTube
│   ├── communication.py    # WhatsApp, Gmail, SMS
│   ├── file.py             # File management
│   ├── window.py           # Window management
│   └── hello.py            # Greetings & personality
│
└── web/
    └── index.html          # Landing page
```

---

## 🚀 Installation

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- ADB installed (for mobile control)
- Android phone with USB debugging enabled

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/mohamad-shafeez/cipher-ai.git
cd cipher-ai
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Pull the AI model**
```bash
ollama pull phi3.5
```

**4. Configure**
```python
# config.py
ASSISTANT_NAME = "Cipher"
WAKE_WORD = "cipher"
LLM_MODEL = "phi3.5"
WHISPER_SIZE = "base.en"
```

**5. Add your contacts (optional)**
```python
# skills/mobile.py
self.contacts = {
    "mom": "+91XXXXXXXXXX",
    "dad": "+91XXXXXXXXXX",
}
```

**6. Run Cipher**
```bash
# Terminal 1 — Start Ollama
ollama serve

# Terminal 2 — Start Cipher
python main.py
```

---

## 🎮 Usage

Press **SPACEBAR** → Speak your command → Cipher responds

### Example Commands

| Voice Command | Action |
|---|---|
| *"open instagram"* | Opens Instagram on phone |
| *"call mom"* | Calls mom via phone |
| *"phone battery"* | Phone battery % |
| *"battery"* | Laptop battery % |
| *"screenshot"* | Takes screenshot |
| *"volume 50"* | Sets volume to 50% |
| *"open YouTube"* | Opens YouTube in browser |
| *"what is machine learning"* | AI explains |
| *"create python file called app"* | Creates app.py |
| *"system info"* | CPU, RAM, disk usage |
| *"tell me a joke"* | Coding joke |
| *"navigate to airport"* | Opens Google Maps |

---

## 📱 Mobile Setup (Android)

1. Enable **Developer Options** on your phone
   - Settings → About Phone → Tap MIUI Version 7 times
2. Enable **USB Debugging**
   - Settings → Additional Settings → Developer Options → USB Debugging
3. Connect via USB cable
4. Accept the **"Allow USB debugging?"** popup on phone
5. Verify connection:
```bash
adb devices
```

---

## ⚙️ Configuration

```python
# config.py

ASSISTANT_NAME = "Cipher"     # Assistant name
WAKE_WORD = "cipher"          # Hotkey-based, not wake word
LLM_MODEL = "phi3.5"          # Ollama model
WHISPER_SIZE = "base.en"      # tiny.en = faster, base.en = accurate

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
```

---

## 🔌 Adding Custom Skills

Drop a `.py` file in the `skills/` folder — Cipher auto-discovers it!

```python
# skills/my_skill.py

class MySkill:
    def __init__(self):
        print(">> My Skill: ONLINE")

    def execute(self, command):
        if "my trigger" in command.lower():
            return "My skill response!"
        return None
```

No changes to any other file needed. 🎉

---

## 🏗️ Architecture

```
SPACE KEY → listen.py (Whisper) → main.py (Router)
                                       ↓
                              skills_manager.py
                              ↙     ↓      ↘
                         Skills  Skills  Skills
                              ↓
                         think.py (Ollama) ← fallback
                              ↓
                         speak.py (pyttsx3)
```

---

## 🙋 Developer

**Mohamad Shafeez**
- 🌐 [GitHub](https://github.com/mohamad-shafeez)
- 💼 [LinkedIn](https://linkedin.com/in/mohamad-shafeez)
- 📧 shafeezchappi18@gmail.com

Final-year BCA student at Srinivas University, Mangalore.
Building production-ready AI systems and backend applications.

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

<p align="center">Built with 🔥 by Mohamad Shafeez</p>