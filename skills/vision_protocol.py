"""
Cipher Skill — Vision Protocol
Organ: The Visual Cortex
Architecture: Uncapped 16GB RAM Edition.
Uses LLaVA for deep image reasoning, lazy-loaded to preserve 1.8s boot time.
Includes auto-cleanup to prevent disk bloat.
"""

import os
from datetime import datetime

class VisionProtocolSkill:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        # 16GB RAM allows us to use the heavy, highly accurate LLaVA model
        self.vision_model = "llava" 
        self.temp_dir = "temp_vision"
        os.makedirs(self.temp_dir, exist_ok=True)
        print(f">> Vision Protocol: ONLINE (Optical Engine: {self.vision_model})")

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()
        triggers = ["analyze screen", "what's on my screen", "read my screen", "look at this", "scan screen", "what do you see"]
        
        if not any(t in cmd for t in triggers):
            return None

        print(">> [Vision] Capturing neural optical snapshot...")
        
        try:
            # LAZY LOAD: Protects the FastBoot sequence from heavy library lag
            import pyautogui
            import base64
            import requests

            # 1. Capture the screen
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.temp_dir, f"vision_input_{timestamp}.png")
            pyautogui.screenshot(screenshot_path)

            # 2. Encode to Base64
            with open(screenshot_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

            # 3. Neural Analysis via LLaVA
            print(f">> [Vision] Routing optical data to {self.vision_model}...")
            
            prompt = (
                "Act as the visual cortex of an advanced AI. Describe exactly what is on the user's screen right now. "
                "Identify open applications, read visible text, and spot any code or errors. Be analytical, precise, and tactical."
            )
            
            payload = {
                "model": self.vision_model,
                "prompt": prompt,
                "images": [encoded_string],
                "stream": False,
                "options": {
                    "temperature": 0.2  # Low temp for factual, precise visual analysis
                }
            }

            # Extended timeout because LLaVA takes a moment to process images
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                analysis = response.json().get("response", "").strip()
            else:
                return f"Sir, the optical backend returned an error: {response.status_code}"

            # 4. Maintenance: Claude's auto-cleanup so your disk doesn't fill up
            self._cleanup_temp()

            return f"Sir, I have analyzed your workspace. {analysis}"

        except Exception as e:
            print(f"[Vision Error] {e}")
            return "Sir, my optical sensors encountered a critical fault during analysis."

    def _cleanup_temp(self, keep_last: int = 5):
        """Keeps only the 5 most recent captures to avoid disk bloat."""
        try:
            files = sorted(
                [os.path.join(self.temp_dir, f) for f in os.listdir(self.temp_dir)],
                key=os.path.getmtime,
            )
            # Delete all but the last 5 files
            for old_file in files[:-keep_last]:
                os.remove(old_file)
        except Exception as e:
            print(f"[Vision Cleanup Error] {e}")