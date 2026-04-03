"""
Cipher Skill — Voice Neural
Organ: The Vocal Cords
Upgrades Cipher's TTS to Microsoft Edge Neural voices (en-US-ChristopherNeural).
Thread-safe execution prevents Flask/Asyncio crashes while using pygame for playback.
"""

import os
import asyncio
import threading
import time

# Global toggle so the rest of Cipher knows which voice to use
_neural_mode_active = True  # Defaulting to True because you have 16GB RAM!

class VoiceNeuralSkill:
    def __init__(self):
        print(">> Voice Neural Skill: ONLINE (Christopher Neural Active)")

    def execute(self, command: str) -> str | None:
        global _neural_mode_active
        cmd = command.lower().strip()

        if any(kw in cmd for kw in ["switch to neural voice", "use pro voice", "enable neural voice"]):
            _neural_mode_active = True
            # We return the string, and the TTS engine will speak it in the NEW voice
            return "Sir, I have transitioned to neural speech synthesis. My vocal patterns are now optimized."

        if any(kw in cmd for kw in ["disable neural voice", "switch to normal voice", "use robotic voice"]):
            _neural_mode_active = False
            return "Sir, I have reverted to the standard local voice engine."

        if "voice status" in cmd:
            mode = "Neural (Edge-TTS)" if _neural_mode_active else "Standard (pyttsx3)"
            return f"Sir, my current vocal matrix is set to {mode}."

        return None

# =====================================================================
# GLOBAL HELPER: Can be imported by core/speak.py to replace pyttsx3
# =====================================================================
def is_neural_active() -> bool:
    return _neural_mode_active

def speak_neural(text: str):
    """
    Thread-safe neural TTS generation and playback.
    Usage in core/speak.py:
        from skills.voice_neural import is_neural_active, speak_neural
        if is_neural_active(): speak_neural(text)
    """
    try:
        # Lazy loading to protect the 1.8s boot time
        import edge_tts
        import pygame
    except ImportError:
        print("[Voice Error] edge-tts or pygame missing. Run: pip install edge-tts pygame")
        return

    voice = "en-US-ChristopherNeural"
    output_file = "temp_voice.mp3"

    async def _generate():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)

    # 1. Thread-safe execution to avoid Flask event-loop collisions
    def _run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate())
        loop.close()

    t = threading.Thread(target=_run_async)
    t.start()
    t.join(timeout=15) # Wait for generation to finish

    # 2. Pygame Playback
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()
        
        # Block until audio finishes playing
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        
        # Cleanup temp file
        if os.path.exists(output_file):
            os.remove(output_file)
            
    except Exception as e:
        print(f"[Playback Error] {e}")