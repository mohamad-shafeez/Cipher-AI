import os
import threading
from PIL import Image, ImageDraw
import pystray
from core.hud_server import HUDServer

class CipherSystemTray:
    def __init__(self):
        self.icon = None
        self.is_monitoring = True

    def _create_icon_image(self, color1="green", color2="black"):
        """Generates a dynamic 64x64 sensory indicator icon for the Windows taskbar."""
        image = Image.new("RGBA", (64, 64), color=color2)
        draw = ImageDraw.Draw(image)
        # Draw a technical 'C' terminal logo wrapper
        draw.chord((10, 10, 54, 54), 30, 330, fill=color1)
        return image

    def _toggle_monitoring(self, icon, item):
        """Allows the developer to quickly pause or resume global file monitoring from the taskbar."""
        self.is_monitoring = not self.is_monitoring
        status_text = "ACTIVE" if self.is_monitoring else "PAUSED"
        print(f"🤖 [SYSTEM DAEMON]: Global system-wide file safeguarding is now {status_text}.")
        HUDServer.push_log(f"📋 SYSTEM DAEMON: Workspace monitoring changed to {status_text}.")
        
        # Redraw icon indicator based on the tracking state
        new_color = "green" if self.is_monitoring else "red"
        self.icon.icon = self._create_icon_image(color1=new_color)

    def _on_exit(self, icon, item):
        """Executes a clean shutdown of all asynchronous core threads and exits the app matrix."""
        print("👋 [SYSTEM DAEMON]: Shutting down Cipher global background service modules...")
        HUDServer.push_log("🛑 SYSTEM DAEMON: Global service exit initiated.")
        self.icon.stop()
        os._exit(0) # Terminate the master background process cleanly

    def launch_background_service(self):
        """Spawns Cipher's persistent system tray instance on a dedicated UI window thread."""
        menu = pystray.Menu(
            pystray.MenuItem("Toggle Safeguard Watch", self._toggle_monitoring, checked=lambda item: self.is_monitoring),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Shutdown Cipher OS", self._on_exit)
        )
        
        self.icon = pystray.Icon(
            name="Cipher-AI",
            icon=self._create_icon_image(),
            title="CIPHER-AI // STANDALONE CORE",
            menu=menu
        )
        
        print("💼 [SYSTEM DAEMON]: Standalone system tray taskbar interface mounted successfully.")
        self.icon.run()
