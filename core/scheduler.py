# core/scheduler.py
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from core.state_manager import StateManager
from core.memory_vector import MemoryVector
from skills.osint_aggregator import OSINTAggregatorSkill

class AgentHeartbeat:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AgentHeartbeat, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.scheduler = BackgroundScheduler(daemon=True)
        self._initialized = True
        # Graceful shutdown handler registered globally
        atexit.register(self.stop)

    def _background_osint_scan(self):
        print(">> [HEARTBEAT] Starting background periodic OSINT scan...")
        StateManager.update_state("background_tasks_running", True)
        StateManager.set_status("OSINT Periodic Scan")

        try:
            # Instantiate skills
            osint = OSINTAggregatorSkill()
            
            # Fetch feed results
            hn_data = osint.fetch_feed("hacker news")
            sec_data = osint.fetch_feed("security updates")
            
            # Save into vector database
            vector_mem = MemoryVector()
            
            hn_fact = f"Periodic OSINT Feed Collection (Hacker News):\n{hn_data}"
            sec_fact = f"Periodic OSINT Feed Collection (Security Updates):\n{sec_data}"
            
            vector_mem.remember_fact(hn_fact, {"source": "background_heartbeat", "feed": "hacker_news"})
            vector_mem.remember_fact(sec_fact, {"source": "background_heartbeat", "feed": "security_updates"})
            
            # Record reflection console update
            StateManager.add_reflection_log("[HEARTBEAT] Background OSINT loop executed successfully. Cached in ChromaDB.")
            
            # Add to memory retrievals
            StateManager.add_memory_retrieval("Background OSINT indexing: Hacker News & Security Updates stored.")
        except Exception as e:
            print(f"[HEARTBEAT ERROR] Background OSINT loop failed: {e}")
            StateManager.add_reflection_log(f"[HEARTBEAT ERROR] Background loop failed: {e}")
        finally:
            StateManager.update_state("background_tasks_running", False)
            StateManager.set_status("Idle")

    def start(self):
        if not self.scheduler.running:
            # Schedule a background scan every 60 minutes
            self.scheduler.add_job(
                self._background_osint_scan,
                'interval',
                minutes=60,
                id='background_osint_scan'
            )
            # Run once immediately on start so the user can verify it works instantly!
            self.scheduler.add_job(
                self._background_osint_scan,
                'date',
                id='immediate_osint_scan'
            )
            self.scheduler.start()
            print(">> [HEARTBEAT] Background sleep-worker scheduler started.")

    def stop(self):
        if self.scheduler.running:
            try:
                self.scheduler.shutdown(wait=False)
                print(">> [HEARTBEAT] Background scheduler shutdown gracefully.")
            except Exception:
                pass
