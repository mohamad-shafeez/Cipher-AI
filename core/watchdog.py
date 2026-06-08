import threading
import time
from core.hud_server import HUDServer

class Watchdog:
    """The Immune System: Monitors thread health and restarts deadlocked background tasks."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Watchdog, cls).__new__(cls)
                cls._instance.registry = {}  # {thread_name: last_heartbeat}
                cls._instance.monitors = {}  # {thread_name: restart_callback}
                cls._instance.lock = threading.Lock()
                cls._instance.started = False
            return cls._instance

    def pulse(self, thread_name: str):
        """Sends a heartbeat pulse to keep the Watchdog from triggering."""
        with self.lock:
            self.registry[thread_name] = time.time()

    def register(self, thread_name: str, restart_callback=None):
        """Registers a thread for monitoring with an optional self-healing restart callback."""
        with self.lock:
            self.registry[thread_name] = time.time()
            if restart_callback:
                self.monitors[thread_name] = restart_callback

    def start(self):
        """Starts the background monitor thread if it isn't already active."""
        with self.lock:
            if not self.started:
                threading.Thread(target=self._monitor, daemon=True, name="WatchdogMonitor").start()
                self.started = True
                print("🛡️ [WATCHDOG]: System immune monitor online.")

    def stop(self):
        """Gracefully disarms the watchdog monitor loop during system exit."""
        self.started = False
        print("🛡️ [WATCHDOG]: System immune monitor disarmed.")

    def _monitor(self):
        while self.started:
            time.sleep(10)
            now = time.time()
            to_restart = []
            with self.lock:
                for name, last_pulse in list(self.registry.items()):
                    # If a registered thread goes silent for more than 45s (loosened slightly for Ollama lag)
                    if now - last_pulse > 45:
                        print(f"🚨 [WATCHDOG]: '{name}' is deadlocked or silent for {int(now - last_pulse)}s!")
                        HUDServer.push_log(f"🚨 WATCHDOG: Timeout on thread '{name}'.")
                        
                        # Reset heartbeat timing to prevent infinite restart loop on same tick
                        self.registry[name] = now
                        
                        # Get restart callback
                        callback = self.monitors.get(name)
                        if callback:
                            to_restart.append((name, callback))
            
            for name, callback in to_restart:
                try:
                    print(f"🛡️ [WATCHDOG]: Triggering restart callback for '{name}'...")
                    HUDServer.push_log(f"🛡️ WATCHDOG: Restarting '{name}'...")
                    callback()
                except Exception as restart_err:
                    print(f"💥 [WATCHDOG RESTART FAILED]: Could not restart '{name}': {restart_err}")
