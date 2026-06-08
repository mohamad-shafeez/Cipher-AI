import threading
import queue
import traceback
from core.hud_server import HUDServer
from core.watchdog import Watchdog

class TaskQueue:
    def __init__(self):
        self.queue = queue.Queue()
        # Daemon thread ensures the queue shuts down when the main script ends
        self.worker_thread = threading.Thread(target=self._run, daemon=True, name="TaskQueueWorker")
        self.worker_thread.start()
        
        # Register this worker thread in our Watchdog immunizer
        Watchdog().register("TaskQueueWorker", self._restart_worker)

    def add_task(self, func, *args, **kwargs):
        """Non-blocking call to add a task to the queue."""
        self.queue.put((func, args, kwargs))

    def _restart_worker(self):
        """Self-healing callback triggered by the watchdog to spawn a fresh queue processor."""
        print("🔄 [TASK QUEUE]: Watchdog detected deadlock. Re-igniting TaskQueueWorker thread...")
        HUDServer.push_log("🔄 TASK QUEUE: Deadlock recovery triggered. Spawning fresh worker.")
        self.worker_thread = threading.Thread(target=self._run, daemon=True, name="TaskQueueWorker")
        self.worker_thread.start()

    def _run(self):
        """The infinite loop that processes tasks in the background."""
        while True:
            # Pulse the Watchdog to signal that this thread is alive and healthy
            Watchdog().pulse("TaskQueueWorker")
            
            try:
                # Use a 5s timeout so we can periodically pulse the watchdog even when idle
                func, args, kwargs = self.queue.get(timeout=5)
            except queue.Empty:
                continue
                
            try:
                # Pulse again right before launching the execution payload
                Watchdog().pulse("TaskQueueWorker")
                func(*args, **kwargs)
            except Exception as e:
                # Capture the full crash log so we know exactly what broke
                error_trace = traceback.format_exc()
                print(f"🛑 [TASK QUEUE CRASH]:\n{error_trace}")
                HUDServer.push_log(f"🛑 SYSTEM ERROR: {str(e)}")
            finally:
                self.queue.task_done()
                # Pulse immediately after finishing the task
                Watchdog().pulse("TaskQueueWorker")
