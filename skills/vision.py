"""
Cipher Skill — Vision
Organ: The Eyes
Merged Architecture: Combines fast-boot lazy loading with robust hardware release protocols.
"""

import os
import time

class VisionSkill:
    """
    Skill module that handles all camera/vision-related commands.
    Captures screen or webcam frame efficiently without slowing down the FastLoader.
    """
    
    def __init__(self):
        # Resolve dynamic path and create temp directory
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.temp_dir = os.path.join(self.base_dir, "temp_vision")
        os.makedirs(self.temp_dir, exist_ok=True)
        print(">> Vision Skill: ONLINE (Hardware Ready)")

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()

        # Route 1: Screen Capture
        screen_triggers = ["what is on my screen", "screenshot", "capture screen", "look at screen"]
        if any(kw in cmd for kw in screen_triggers):
            return self._capture_screen()

        # Route 2: Webcam Capture
        webcam_triggers = ["look at me", "webcam", "camera", "take a picture", "show me what you see"]
        if any(kw in cmd for kw in webcam_triggers):
            return self._capture_webcam()

        return None

    def _capture_screen(self) -> str:
        """Captures the screen using mss (fast) or pyautogui (fallback)."""
        filename = os.path.join(self.temp_dir, f"screen_{int(time.time())}.png")
        
        try:
            # Lazy load mss for memory efficiency
            import mss
            import mss.tools
            with mss.mss() as sct:
                # Grab the primary monitor
                monitor = sct.monitors[1]
                shot = sct.grab(monitor)
                mss.tools.to_png(shot.rgb, shot.size, output=filename)
            return f"Sir, I have captured your screen. The image is saved to {filename}."

        except ImportError:
            # Fallback to pyautogui
            try:
                import pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(filename)
                return f"Sir, screen captured via fallback and saved to {filename}."
            except Exception as e:
                return f"Sir, screen capture failed entirely: {e}"
        except Exception as e:
            return f"Sir, an error occurred during screen capture: {e}"

    def _capture_webcam(self) -> str:
        """Opens webcam, warms up sensor, captures frame, and releases safely."""
        filename = os.path.join(self.temp_dir, f"webcam_{int(time.time())}.jpg")
        cap = None
        
        try:
            # Lazy load OpenCV so it doesn't drag down the boot time
            import cv2

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "Sir, I was unable to access the camera. It may be in use by another application."

            # User's brilliant warm-up loop for auto-exposure stabilization
            for _ in range(5):
                cap.read()

            ret, frame = cap.read()

            if not ret or frame is None:
                return "Sir, the camera opened but failed to capture a frame."

            success = cv2.imwrite(filename, frame)
            if not success:
                return f"Sir, I captured the frame but failed to save it. Please check permissions."

            return f"Sir, I have captured the image from the camera. It is saved at {filename}."

        except ImportError:
            return "Sir, OpenCV is not installed. Please run: pip install opencv-python-headless"
        except Exception as e:
            return f"Sir, an unexpected error occurred during webcam capture: {e}"
        finally:
            # The user's bulletproof hardware release protocol
            if cap is not None and cap.isOpened():
                cap.release()