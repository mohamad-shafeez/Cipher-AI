import time
import requests
import threading
from core.event_bus import EventBus, Event
from core.orchestrator import MasterOrchestrator
from core.hud_server import HUDServer

class MobileBridge:
    """A secure, polling cloud bridge linking your mobile device to the local OS."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_update_id = 0
        self.is_active = False

    def send_message(self, text: str):
        """Pushes a notification from your Desktop OS to your Phone."""
        if not self.bot_token or not self.chat_id or "YOUR_" in self.bot_token:
            return
            
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"⚠️ [MOBILE BRIDGE]: Failed to push notification -> {e}")

    def handle_system_event(self, event: Event):
        """Subscribes to the Event Bus to notify your phone when things happen."""
        if event.type == "swarm.consensus.reached":
            self.send_message("✅ *Swarm Update:*\nThe autonomous agents have successfully resolved the codebase issue.")
        elif event.type == "graph.step.success":
            intent = event.data.get("intent", "task")
            self.send_message(f"⚙️ *OS Action:*\nSuccessfully executed: `{intent}`")
        elif event.type == "os.system.idle":
            # Idle alert is published when idle is reached
            self.send_message("🔒 *Security:* PC has transitioned to idle inactive state.")

    def _poll_commands(self):
        """Silently listens for commands sent from your phone."""
        print("📱 [MOBILE BRIDGE]: Cloud uplink established. Listening for remote commands...")
        
        while self.is_active:
            try:
                url = f"{self.base_url}/getUpdates?offset={self.last_update_id + 1}&timeout=10"
                response = requests.get(url, timeout=15).json()

                if response.get("ok"):
                    for result in response["result"]:
                        self.last_update_id = result["update_id"]
                        message = result.get("message", {})
                        
                        # Verify the message is actually from YOU (Security check)
                        if str(message.get("chat", {}).get("id")) != self.chat_id:
                            continue
                            
                        text = message.get("text")
                        if text:
                            print(f"📡 [REMOTE UPLINK INCOMING]: '{text}'")
                            HUDServer.push_log(f"📱 MOBILE COMMAND RECEIVED: {text}")
                            
                            # Acknowledge receipt on the phone
                            self.send_message(f"🚀 *Received.* Orchestrator is executing...")
                            
                            # Throw the remote text directly into the Master Orchestrator!
                            # We use None for active_directory so it defaults to the main workspace
                            MasterOrchestrator.route_command(text, active_directory=None)
                            
            except Exception:
                pass # Ignore network blips and keep polling
                
            time.sleep(2) # Prevent rate-limiting

    def start(self):
        if not self.bot_token or not self.chat_id or "YOUR_" in self.bot_token or "YOUR_" in self.chat_id:
            print("⚠️ [MOBILE BRIDGE]: Token/Chat ID missing or placeholder active. Remote uplink disabled.")
            return
            
        self.is_active = True
        threading.Thread(target=self._poll_commands, daemon=True).start()
