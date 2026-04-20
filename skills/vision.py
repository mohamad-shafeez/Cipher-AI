import os
from typing import Optional
from google import genai
from PIL import Image
import mss

class VisionSkill:
    """
    Vision skill using Gemini 1.5 Flash to analyse screen captures.
    Fast screen capture with mss + AI description via Google GenAI SDK.
    """

    def __init__(self):
        # Initialise Gemini client if API key is available
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print(">> VisionSkill WARNING: GEMINI_API_KEY environment variable not set.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)

        # Ensure storage directory exists
        self.data_dir = "cipher_data"
        os.makedirs(self.data_dir, exist_ok=True)

    def capture_screen(self) -> str:
        """
        Captures the primary monitor using mss and saves to cipher_data/last_seen.png.
        Returns the file path.
        """
        output_path = os.path.join(self.data_dir, "last_seen.png")
        with mss.mss() as sct:
            # Monitor 1 is the primary monitor in most configurations
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)
        return output_path

    def analyze_screen(self, user_prompt: str) -> str:
        """
        Captures screen, sends it with user_prompt to Gemini 1.5 Flash,
        returns the text response. Handles API errors gracefully.
        """
        if self.client is None:
            return "Error: Gemini API key not configured. Please set GEMINI_API_KEY."

        try:
            print(">> [Vision] Capturing Optic Feed...")
            image_path = self.capture_screen()

            with Image.open(image_path) as img:
                # --- THE SHRINK RAY ---
                # We resize to 720p BEFORE sending. 
                # This drastically reduces the token count and helps avoid the 429 error.
                img.thumbnail((1280, 720)) 
                
                print(">> [Vision] Processing Image via Neural Link (Optimized)...")
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[user_prompt, img]
                )
                return response.text

        except Exception as e:
            return f"Sorry, I couldn't analyse the screen due to an error: {str(e)}"
        
    def execute(self, command: str) -> Optional[str]:
        cmd = command.lower().strip()

        # Added "scan" and "display" to match the Planner's vocabulary
        vision_anchors = ["look", "see", "screen", "visual", "monitor", "watching", "scan", "display"]

        if any(anchor in cmd for anchor in vision_anchors):
            words = cmd.split()
            if len(words) < 5:
                prompt = "What is on my screen right now? Describe it in 2 sentences."
            else:
                prompt = f"Look at my screen and answer this: {command}"
            
            return self.analyze_screen(prompt)

        return None    

    def execute(self, command: str) -> Optional[str]:
        """
        Main router. Uses 'Anchor Words' to capture the command
        even if the noise filter removes small words.
        """
        cmd = command.lower().strip()

        # Anchor Words: If ANY of these are in the command, we trigger Vision.
        vision_anchors = ["look", "see", "screen", "visual", "monitor", "watching", "screenshot"]

        if any(anchor in cmd for anchor in vision_anchors):
            # Check if it's a short command or a specific question
            words = cmd.split()
            if len(words) < 5:
                # Default behavior for "Cipher, look" or "Look at screen"
                prompt = "What is on my screen right now? Describe it in 2 sentences."
            else:
                # Passes your specific question (e.g., "...tell me what is my wallpaper") to Gemini
                prompt = f"Look at my screen and answer this: {command}"
            
            return self.analyze_screen(prompt)
    

        return None