import os
from typing import Optional
import base64
import requests
import mss
import config
from PIL import Image

class VisionSkill:
    """
    Vision skill using a local optical model (like LLaVA or Moondream) via Ollama 
    to analyse screen captures.
    """

    def __init__(self):
        self.data_dir = "cipher_data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.ollama_url = f"{config.OLLAMA_BASE_URL}/api/generate"
        print(f">> VisionSkill: ONLINE (Local Model: {config.VISION_MODEL})")

    def capture_screen(self) -> str:
        """
        Captures the primary monitor using mss and saves to cipher_data/last_seen.png.
        Returns the file path.
        """
        output_path = os.path.join(self.data_dir, "last_seen.png")
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)
        return output_path

    def analyze_screen(self, user_prompt: str) -> str:
        """
        Captures screen, sends it with user_prompt to local Ollama Vision model,
        returns the text response. Handles API errors gracefully.
        """
        try:
            print(">> [Vision] Capturing Optic Feed...")
            image_path = self.capture_screen()

            # We resize to 720p BEFORE sending to save RAM and processing time.
            with Image.open(image_path) as img:
                img.thumbnail((1280, 720))
                # Save optimized image back
                optimized_path = os.path.join(self.data_dir, "last_seen_optimized.png")
                img.save(optimized_path, format="PNG")

            with open(optimized_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

            print(f">> [Vision] Processing Image via Local Neural Link ({config.VISION_MODEL})...")
            response = requests.post(self.ollama_url, json={
                "model": config.VISION_MODEL,
                "prompt": user_prompt,
                "images": [encoded_string],
                "stream": False
            }, timeout=120)

            if response.status_code == 200:
                return response.json().get("response", "No response received.")
            else:
                return f"Error from Ollama Vision API: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Sorry, I couldn't analyse the screen due to an error: {str(e)}"
        
    def execute(self, command: str) -> Optional[str]:
        """
        Main router. Uses 'Anchor Words' to capture the command.
        """
        cmd = command.lower().strip()

        vision_anchors = ["look", "see", "screen", "visual", "monitor", "watching", "screenshot"]

        if any(anchor in cmd for anchor in vision_anchors):
            return "Sir, a vision model like LLaVA is not currently installed. Please run 'ollama run llava' in your terminal to enable screen analysis."
    
        return None