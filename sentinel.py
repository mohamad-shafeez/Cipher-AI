import os
import subprocess
import time
import webbrowser
import sys
import winsound  # Added for audio feedback

# ══ CONFIGURATION ════════════════════════════════════════════
WAKE_WORDS = ["cipher", "cypher", "sifer", "sypher", "cyber", "hey", "sa"] 
BACKEND_SCRIPT = "main.py" 
FRONTEND_URL = "http://localhost:5500"
SLEEP_TIMEOUT = 600  # 10 minutes

class Sentinel:
    def __init__(self):
        self.is_awake = False
        self.last_activity = time.time()
        self.backend_proc = None # We track the specific process ID
        # "I am alive" Beep: High pitch, short duration
        winsound.Beep(1000, 400) 
        print(">> Sentinel: LOW-POWER MODE ACTIVE")

    def wake_system(self):
        if not self.is_awake:
            print(">> [WAKE] Booting Cipher App Interface...")
            
            # Start backend invisibly
            self.backend_proc = subprocess.Popen([sys.executable, BACKEND_SCRIPT], 
                                                 creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(2)

            # --- NEW APP WINDOW LOGIC ---
            import webview
            window = webview.create_window(
                'CIPHER OS — NEURAL DASHBOARD', 
                FRONTEND_URL,
                width=1200, 
                height=800,
                resizable=True,
                confirm_close=True,
                background_color='#000000'
            )
            webview.start()
            # ----------------------------

            self.is_awake = True
            self.last_activity = time.time()

    def hibernate_system(self):
        if self.is_awake:
            print(">> [SLEEP] Inactivity detected. Purging VRAM...")
            # Low beep to signal sleep
            winsound.Beep(500, 500)
            if self.backend_proc:
                self.backend_proc.terminate() # Kill only the backend, not the sentinel
            os.system("ollama stop deepseek-r1:7b") 
            self.is_awake = False

    def listen_loop(self):
        import speech_recognition as sr
        r = sr.Recognizer()
        r.energy_threshold = 300 
        r.dynamic_energy_threshold = True
        
        with sr.Microphone(device_index=1) as source:
            # Fast 1-second calibration for better response
            r.adjust_for_ambient_noise(source, duration=1)
            
            while True:
                try:
                    # Listen for the wake command
                    audio = r.listen(source, phrase_time_limit=3)
                    text = r.recognize_google(audio).lower()
                    
                    if any(word in text for word in WAKE_WORDS):
                        self.wake_system()

                except:
                    pass # Keep it silent in production
                
                # Auto-Sleep Logic
                if self.is_awake and (time.time() - self.last_activity > SLEEP_TIMEOUT):
                    self.hibernate_system()

if __name__ == "__main__":
    guard = Sentinel()
    guard.listen_loop()