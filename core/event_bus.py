import threading
import time
import pyperclip
import win32api
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Any
from core.hud_server import HUDServer

@dataclass
class Event:
    """A standardized event packet sent across the system."""
    type: str
    source: str
    data: Any = None
    timestamp: datetime = field(default_factory=datetime.now)

class EventBus:
    """Thread-safe Publish/Subscribe central nervous system."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        # Enforce Singleton pattern: Only one Event Bus can exist
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance.subscribers: Dict[str, List[Callable]] = {}
                cls._instance.bus_lock = threading.Lock()
        return cls._instance

    def subscribe(self, event_type: str, callback: Callable):
        """Register a function to listen for a specific event type."""
        with self.bus_lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)
            print(f"🔌 [EVENT BUS]: New subscriber attached to '{event_type}'")

    def publish(self, event: Event):
        """Broadcast an event to all subscribed listeners asynchronously."""
        with self.bus_lock:
            if event.type not in self.subscribers:
                return # No one is listening to this event type

            # Run callbacks in separate lightweight threads so they don't block the bus
            for callback in self.subscribers[event.type]:
                threading.Thread(target=self._safe_execute, args=(callback, event), daemon=True).start()

    def _safe_execute(self, callback: Callable, event: Event):
        """Ensure a crashing subscriber doesn't take down the Event Bus."""
        try:
            callback(event)
        except Exception as e:
            print(f"🛑 [EVENT BUS CRASH]: Subscriber failed on {event.type} -> {str(e)}")

# ==========================================
# 🕵️‍♂️ OS-LEVEL DAEMON WATCHERS
# ==========================================

class ClipboardWatcher:
    """Monitors the Windows clipboard for changes and publishes an event."""
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.last_content = pyperclip.paste()

    def start(self):
        def watch_loop():
            print("👁️ [WATCHER ONLINE]: Monitoring Clipboard stream...")
            while True:
                time.sleep(1.5) # Check every 1.5 seconds
                try:
                    current_content = pyperclip.paste()
                    if current_content != self.last_content and current_content.strip():
                        self.last_content = current_content
                        # 📢 Publish the event!
                        self.bus.publish(Event(
                            type="os.clipboard.changed",
                            source="ClipboardWatcher",
                            data=current_content
                        ))
                except Exception:
                    pass
        
        threading.Thread(target=watch_loop, daemon=True).start()

class SystemIdleWatcher:
    """Monitors mouse/keyboard input to determine if the user has stepped away."""
    def __init__(self, bus: EventBus, idle_threshold_seconds: int = 300):
        self.bus = bus
        self.threshold = idle_threshold_seconds
        self.is_idle = False

    def get_idle_time(self) -> int:
        """Returns seconds since last user input using native Win32 API."""
        last_input = win32api.GetLastInputInfo()
        tick_count = win32api.GetTickCount()
        return (tick_count - last_input) // 1000

    def start(self):
        def watch_loop():
            print("👁️ [WATCHER ONLINE]: Monitoring System Idle State...")
            while True:
                time.sleep(5)
                idle_seconds = self.get_idle_time()

                if idle_seconds >= self.threshold and not self.is_idle:
                    self.is_idle = True
                    self.bus.publish(Event(
                        type="os.system.idle",
                        source="IdleWatcher",
                        data={"idle_time": idle_seconds}
                    ))
                
                elif idle_seconds < 5 and self.is_idle:
                    self.is_idle = False
                    self.bus.publish(Event(
                        type="os.system.active",
                        source="IdleWatcher",
                        data={"message": "User returned"}
                    ))

        threading.Thread(target=watch_loop, daemon=True).start()
