import os
import re
import asyncio
import threading
import edge_tts
import pygame
import config

class Speaker:
    def __init__(self):
        print(f">> Loading Neural Voice for {config.ASSISTANT_NAME}...")
        pygame.mixer.init()
        # "en-US-ChristopherNeural" is professional male. 
        # "en-US-GuyNeural" or "en-GB-RyanNeural" are also great.
        self.voice = "en-US-ChristopherNeural" 
        self.output_file = "temp_voice.mp3"
        print(f">> Neural Voice: ONLINE")

    def clean_text(self, text):
        text = re.sub(r'[;:\-\*\#\|]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _generate_and_play(self, text):
        # --- NEW: Check if Neural Voice is toggled ON/OFF by the user ---
        neural_active = True
        try:
            from skills.voice_neural import is_neural_active
            neural_active = is_neural_active()
        except ImportError:
            pass # Default to True if the skill isn't loaded

        # Fallback to standard offline voice if user disabled Neural mode
        if not neural_active:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
                return
            except ImportError:
                print(">> [Voice] pyttsx3 not installed, falling back to neural.")

        # 1. Generate the audio asynchronously (UPDATED: Thread-Safe)
        async def generate():
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(self.output_file)

        # Replaced crashing asyncio.run() with Thread-Safe Event Loop
        def _run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate())
            loop.close()

        t = threading.Thread(target=_run_async)
        t.start()
        t.join(timeout=15)
        
        # 2. Play it synchronously
        try:
            pygame.mixer.music.load(self.output_file)
            pygame.mixer.music.play()
            
            # 3. Wait for it to finish speaking
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
        except Exception as e:
            print(f">> [Playback Error] {e}")
        
        # 4. Clean up
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except:
                pass

    def speak(self, text):
        if not text:
            return
        
        print(f"\n>> {config.ASSISTANT_NAME} speaking: {text}")
        
        try:
            cleaned = self.clean_text(text)
            self._generate_and_play(cleaned)
        except Exception as e:
            print(f">> Speech Error: {e}")

# =====================================================================
# For compatibility: Expose a global speak() function 
# so other files can just call speak("hello") easily.
# =====================================================================
_global_speaker = None

def speak(text: str):
    global _global_speaker
    if _global_speaker is None:
        _global_speaker = Speaker()
    _global_speaker.speak(text)