import base64
import io
from PIL import ImageGrab
import requests
from core.hud_server import HUDServer

class VisionEngine:
    """Handles OS-level screen capture and local visual processing via Moondream."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.vision_model = "moondream:latest"

    def _capture_screen_b64(self) -> str:
        """Takes a silent screenshot and converts it to a base64 string."""
        print("📸 [VISION ENGINE]: Capturing OS visual context...")
        HUDServer.push_log("📸 VISION: Capturing screen matrix...")
        
        # Capture the entire primary screen
        screenshot = ImageGrab.grab()
        
        # Compress it slightly so the local model processes it faster
        screenshot = screenshot.convert("RGB")
        screenshot.thumbnail((1024, 1024)) 
        
        # Convert to Base64
        buffered = io.BytesIO()
        screenshot.save(buffered, format="JPEG", quality=80)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def analyze_screen(self, query: str = "Describe what is on the screen.") -> str:
        """Feeds the screenshot to Moondream to answer the user's query."""
        try:
            b64_image = self._capture_screen_b64()
        except Exception as capture_err:
            error_msg = f"Failed to capture screen: {capture_err}"
            print(f"🛑 [VISION ERROR]: {error_msg}")
            HUDServer.push_log("🛑 VISION: Capture failed.")
            return error_msg
        
        print(f"👁️ [VISION ENGINE]: Analyzing visual data for query: '{query}'")
        HUDServer.set_agent("ResearchAssistant")
        
        payload = {
            "model": self.vision_model,
            "prompt": query,
            "stream": False,
            "images": [b64_image]
        }
        
        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=120)
            response.raise_for_status()
            result = response.json().get("response", "Visual analysis failed.")
            print(f"🧠 [VISION OUTPUT]: {result}")
            HUDServer.push_log("🧠 VISION: Analysis complete.")
            return result
        except Exception as e:
            error_msg = f"Vision Engine Error: {str(e)}"
            print(f"🛑 [VISION FATAL]: {error_msg}")
            return error_msg
