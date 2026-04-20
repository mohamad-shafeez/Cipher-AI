# config.py
# ============================================================
#   CIPHER OS — SYSTEM CONFIGURATION (GHOST EDITION)
# ============================================================

# --- IDENTITY ---
ASSISTANT_NAME = "Cipher"
MASTER_NAME = "Shafeez"

# Common misspellings for robust wake-word detection
WAKE_WORDS = ["cipher", "cypher", "sifer", "sypher", "cyber"]

# --- INTELLIGENCE (OLLAMA) ---
# Centralized model management for system-wide sync
LLM_MODEL = "phi3.5"         # Primary reasoning & planning model
VISION_MODEL = "llava"       # Primary optical model
OLLAMA_BASE_URL = "http://localhost:11434"

# --- GHOST MODE SETTINGS ---
# The 2-key combo to summon the Ghost instantly
GHOST_HOTKEY = "ctrl+space" 
WAKE_WORD_ENABLED = True     # Toggle for "Show-off" mode
GHOST_SILENT_BOOT = True    # Keep terminal hidden on startup

# --- VOICE & AUDIO ---
WHISPER_SIZE = "base.en"    # High speed for the i5 processor
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

# --- NETWORK & WEB UI ---
WEB_PORT = 5500              
# IMPORTANT: Increased to 120s to prevent lag-crashes on local hardware
API_TIMEOUT = 120             

# --- MEMORY SETTINGS ---
MAX_CONTEXT_TURNS = 10       # Slightly increased for deeper coding context

SAMPLE_RATE = 16000
CHUNK_SIZE  = 1024