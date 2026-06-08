import os
import subprocess
import platform
import logging
from core.hud_server import HUDServer
from core.event_bus import EventBus, Event

class SystemOperatorSkill:
    def __init__(self):
        self.capabilities = ["system.app.open", "mobile.app.open"]

    def execute(self, payload: dict) -> bool:
        intent = payload.get("intent")
        target = payload.get("target", "").lower().strip()
        
        if not target:
            logging.error("❌ [SYSTEM OPERATOR]: Missing target application name.")
            return False

        try:
            if intent == "system.app.open":
                return self._launch_pc_app(target)
            elif intent == "mobile.app.open":
                return self._launch_mobile_app(target)
            return False
        except Exception as e:
            logging.error(f"❌ [SYSTEM OPERATOR CRASH]: {str(e)}")
            return False

    def _launch_pc_app(self, app_name: str) -> bool:
        """Launches local Windows apps via URI protocols and suppresses system error popups with a Chrome fallback."""
        import os
        import subprocess
        import logging
        from core.event_bus import EventBus, Event

        logging.info(f"💻 [PC LAUNCH]: Processing application target: {app_name}")
        
        # Core Application Database: { common_voice_name: (Windows_Protocol_or_Exe, Chrome_Web_Fallback) }
        app_database = {
            "spotify": ("spotify:", "https://open.spotify.com"),
            "instagram": ("instagram:", "https://www.instagram.com"),
            "chrome": ("chrome", "https://www.google.com"),
            "notepad": ("notepad.exe", None),
            "calculator": ("calc.exe", None),
            "whatsapp": ("whatsapp:", "https://web.whatsapp.com"),
            "youtube": ("start https://www.youtube.com", "https://www.youtube.com")
        }
        
        # If the app isn't explicitly mapped, default to searching for it on Google
        target_command, fallback_url = app_database.get(
            app_name, 
            (app_name, f"https://www.google.com/search?q={app_name}")
        )
        
        try:
            # Handle protocol URIs and classic Windows executables cleanly
            if ":" in target_command or target_command.endswith(".exe"):
                # os.startfile executes protocols directly and throws an catchable Python error if missing
                os.startfile(target_command)
                logging.info(f"✅ [SUCCESS]: Launched local application protocol: {target_command}")
                return True
            else:
                # Traditional binary verification path
                result = subprocess.run(f"where {target_command}", shell=True, capture_output=True, text=True)
                if result.returncode == 0 or target_command == "chrome":
                    subprocess.Popen(f"start {target_command}", shell=True)
                    return True
                raise FileNotFoundError
                
        except (FileNotFoundError, OSError, Exception):
            logging.warning(f"⚠️ [APP NOT FOUND]: Local '{app_name}' unindexed or missing. Rerouting to Google Chrome...")
            
            if fallback_url:
                # Suppress windows popups and open the cloud fallback link cleanly inside Chrome
                chrome_cmd = f'start chrome "{fallback_url}"'
                subprocess.Popen(chrome_cmd, shell=True)
                
                # Use project's EventBus signature to avoid any errors:
                EventBus().publish(Event(type="hud.log", source="SystemOperator", data={"message": f"Redirected {app_name} to Chrome fallback layer."}))
                return True
            else:
                logging.error(f"❌ [SYSTEM CRITICAL]: No web fallback url found for target: {app_name}")
                return False

    def _launch_mobile_app(self, app_package: str) -> bool:
        """Launches ANY Android application over ADB via package name mapping."""
        logging.info(f"📱 [MOBILE ADB LAUNCH]: Sending execution intent for package: {app_package}")
        
        # Common Android package mappings (Change these to match your targeted mobile apps)
        mobile_mappings = {
            "spotify": "com.spotify.music",
            "youtube": "com.google.android.youtube",
            "instagram": "com.instagram.android",
            "whatsapp": "com.whatsapp",
            "camera": "com.android.camera"
        }
        
        package_id = mobile_mappings.get(app_package, app_package)
        
        # Verify if an ADB device is physically connected
        check_device = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if "device" not in check_device.stdout.split("\n")[1]:
            logging.error("❌ [ADB ERROR]: No active physical mobile device linked via ADB.")
            HUDServer.push_log(f"❌ ADB ERROR: No active mobile device linked via ADB.")
            return False

        # Flawless Android launch hook utilizing the device monkey engine tool
        adb_cmd = f"adb shell monkey -p {package_id} -c android.intent.category.LAUNCHER 1"
        subprocess.Popen(adb_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        HUDServer.push_log(f"📱 Launched Mobile App: {app_package}")
        EventBus().publish(Event(type="hud.log", source="SystemOperator", data={"message": f"Fired ADB mobile launch intent: {app_package}"}))
        EventBus().publish(Event(type="worker.task.success", source="SystemOperator", data={"skill": "SystemOperator", "action": "mobile.app.open"}))
        return True
