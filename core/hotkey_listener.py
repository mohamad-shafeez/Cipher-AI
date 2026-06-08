import threading
import keyboard
from core.hud_server import HUDServer

class HotkeyListener:
    def __init__(self, sovereign_callback, livetalk_callback):
        self.sovereign_hotkey = "ctrl+shift+space"
        self.livetalk_hotkey = "ctrl+space"
        self.sovereign_callback = sovereign_callback
        self.livetalk_callback = livetalk_callback

    def _on_sovereign_pressed(self):
        print(f"🎹 [HOTKEY INTERCEPT]: Sovereign Mode hardware trigger activated ({self.sovereign_hotkey.upper()})!")
        HUDServer.push_log("🎹 HOTKEY: Sovereign Mode override shortcut intercepted. Waking sensory pipeline...")
        if self.sovereign_callback:
            threading.Thread(target=self.sovereign_callback, daemon=True).start()

    def _on_livetalk_pressed(self):
        print(f"🎹 [HOTKEY INTERCEPT]: LiveTalk Mode hardware trigger activated ({self.livetalk_hotkey.upper()})!")
        HUDServer.push_log("🎹 HOTKEY: LiveTalk Mode instant chat shortcut intercepted.")
        if self.livetalk_callback:
            threading.Thread(target=self.livetalk_callback, daemon=True).start()

    def start(self):
        """Registers the global operating system shortcut hooks in a non-blocking layout."""
        keyboard.add_hotkey(self.sovereign_hotkey, self._on_sovereign_pressed)
        keyboard.add_hotkey(self.livetalk_hotkey, self._on_livetalk_pressed)
        print(f"🎹 [HOTKEY LISTENER]: Dual trigger anchors registered:")
        print(f"   👑 Sovereign Mode: [{self.sovereign_hotkey.upper()}]")
        print(f"   ⚡ LiveTalk Mode:  [{self.livetalk_hotkey.upper()}]")
