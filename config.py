# config.py
# ============================================================
#   CIPHER OS — SYSTEM CONFIGURATION
# ============================================================

# --- IDENTITY ---
ASSISTANT_NAME = "Cipher"
WAKE_WORD = "cipher"

# --- INTELLIGENCE (OLLAMA) ---
# Ensure these match your 'ollama list'
LLM_MODEL = "phi3.5"         # Primary reasoning model
VISION_MODEL = "llava"       # Primary optical model
OLLAMA_BASE_URL = "http://localhost:11434"

# --- VOICE & AUDIO ---
WHISPER_SIZE = "tiny.en"     # 'tiny.en' for speed, 'base.en' for accuracy
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

# --- NETWORK & WEB UI ---
WEB_PORT = 5500              # Port for your Flask/Chat interface
API_TIMEOUT = 30             # Seconds to wait for LLM response

# --- MEMORY SETTINGS ---
MAX_CONTEXT_TURNS = 6        # Short-term memory window