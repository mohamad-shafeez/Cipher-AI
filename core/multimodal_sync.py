import os
import time
import requests
import config

class MultimodalSync:
    def __init__(self):
        self.vision_url = f"{getattr(config, 'OLLAMA_URL', 'http://localhost:11434')}/api/generate"
        self.vision_model = "llava"  # Local vision model from your system configuration

    @staticmethod
    def capture_screen_matrix() -> str:
        """Dynamically grabs a background screenshot and saves it temporarily for analysis."""
        try:
            from PIL import ImageGrab
            temp_path = "D:/Visual Studio/Cipher-AI/generated_code/live_viewport.png"
            
            # Snap active desktop boundaries
            screenshot = ImageGrab.grab()
            screenshot.save(temp_path, "PNG")
            return temp_path
        except Exception as e:
            print(f"⚠️ [SENSORY CRASH]: Screen grab capture failed: {str(e)}")
            return ""

    def process_visual_intent(self, vocal_command: str) -> str:
        """
        Intercepts vocal audio text. If spatial or visual references are found,
        it automatically binds screen pixels to the local reasoning matrix.
        """
        cmd_lower = vocal_command.lower()
        visual_triggers = ["look at this", "on my screen", "this window", "what is this", "see this"]
        
        if not any(trigger in cmd_lower for trigger in list(visual_triggers)):
            return "" # Pass safely if it's a pure text/vocal operational command

        print("👁️ [SENSORY CONVERGENCE]: Visual intent detected in voice stream! Syncing screen capture...")
        image_path = self.capture_screen_matrix()
        
        if not image_path or not os.path.exists(image_path):
            return "Sensory link established, but desktop viewport streaming failed."

        try:
            import base64
            with open(image_path, "rb") as img_file:
                b64_image = base64.b64encode(img_file.read()).decode('utf-8')

            print(f"🧠 [LOCAL INFERENCE]: Running local {self.vision_model} layout processing...")
            
            # Post your visual frames + vocal request directly to Ollama's native multimodal pipeline
            response = requests.post(
                self.vision_url,
                json={
                    "model": self.vision_model,
                    "prompt": f"Analyze this screenshot layout and answer the user's vocal query: {vocal_command}",
                    "images": [b64_image],
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                vision_analysis = response.json().get("response", "").strip()
                print("✨ [SENSORY CONVERGENCE LOOP LOCKED]: Vision analysis stream recovered.")
                return f"\n👁️ [SCREEN VIEWPORT OBSERVATION]: {vision_analysis}"
                
        except Exception as e:
            print(f"❌ [VISION MATRIX FAILURE]: {str(e)}")
            
        return "Sensory processing loop dropped frames during vision matrix aggregation."
