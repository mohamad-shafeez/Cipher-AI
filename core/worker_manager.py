# core/worker_manager.py — CIPHER OS (Worker Supervisor Kernel & IPC Bridge)
# =======================================================================

import os
import sys
import time
import signal
import logging
import traceback
import multiprocessing
import functools
import psutil
import requests
import gc
from core.hud_server import HUDServer

def evict_model_from_vram(model_name: str, host: str):
    """Forces Ollama to unload the model from memory instantly."""
    try:
        print(f"🧹 [MEMORY MANAGER]: Evicting {model_name} from VRAM...")
        # Sending keep_alive=0 tells Ollama to unload it immediately
        requests.post(
            f"{host}/api/generate",
            json={"model": model_name, "keep_alive": 0},
            timeout=5
        )
    except Exception as e:
        print(f"⚠️ [MEMORY MANAGER]: Failed to evict model: {e}")

# ⏳ Hard Timeout Architecture
TASK_TIMEOUTS = {
    "vision": 45,
    "automation": 60,
    "coding": 120,
    "swarm": 180
}

# ⚖️ CPU Scheduling Tiers
# LiveTalk (Main Thread) will run at HIGH_PRIORITY_CLASS
PRIORITY_MAP = {
    "automation": psutil.NORMAL_PRIORITY_CLASS,       # Needs to be fast to click buttons
    "vision": psutil.BELOW_NORMAL_PRIORITY_CLASS,     # Heavy, but needs to return somewhat fast
    "swarm": psutil.IDLE_PRIORITY_CLASS,              # Massive LLM workload; yields to everything else
    "coding": psutil.IDLE_PRIORITY_CLASS              # Massive LLM workload; yields to everything else
}

class CipherWorkerProcess(multiprocessing.Process):
    """An isolated OS process wrapper for heavy local AI execution."""
    def __init__(self, name, task_queue, result_queue):
        super().__init__()
        self.name = name
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.daemon = True  # Ensures parent exit cleans up child processes
        self.last_eviction_time = 0  # Track last eviction to prevent spam

    def run(self):
        """The sandboxed runtime execution environment."""
        try:
            os.makedirs("logs", exist_ok=True)
            logging.basicConfig(
                filename=f"logs/{self.name}.log", level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s"
            )
            
            # 🌐 PHASE 5: NETWORK ISOLATION
            # Force this sandbox to use the secondary heavy-compute Ollama instance
            os.environ["OLLAMA_HOST"] = "http://localhost:11435"
            
            print(f"📦 [KERNEL]: Process sandboxed -> {self.name} (PID: {os.getpid()})")

            # 🫀 PHASE 4: ACTIVE HEARTBEAT
            import threading
            def emit_heartbeat():
                while True:
                    try:
                        self.result_queue.put({"type": "heartbeat", "worker": self.name})
                    except Exception:
                        break # Queue closed
                    time.sleep(3)
                    
            threading.Thread(target=emit_heartbeat, daemon=True, name=f"{self.name}_Pulse").start()

            # 1. 🧠 CONTEXT INJECTION: Load specific skills into this isolated memory space
            # We do this INSIDE run() so it loads in the child process, not the parent.
            active_skills = {}
            try:
                if self.name == "swarm":
                    from skills.swarm_skill import SwarmSkill
                    active_skills["swarm"] = SwarmSkill()
                elif self.name == "coding":
                    from skills.swarm_skill import SwarmSkill
                    active_skills["coding"] = SwarmSkill()
                elif self.name == "vision":
                    from skills.vision_skill import VisionSkill
                    active_skills["vision"] = VisionSkill()
                elif self.name == "automation":
                    from skills.system_operator_skill import SystemOperatorSkill
                    active_skills["automation"] = SystemOperatorSkill()
            except Exception as e:
                logging.error(f"💥 Failed to inject skills into {self.name} sandbox:\n{traceback.format_exc()}")

            # Tell the parent we are fully loaded and ready
            self.result_queue.put({"type": "telemetry", "worker": self.name, "msg": "ONLINE"})

            while True:
                try:
                    # Continuous blocking wait for IPC payloads
                    task_id, payload = self.task_queue.get()
                    logging.info(f"📥 Processing task {task_id}...")
                    
                    # Check for compatibility function routing
                    if isinstance(payload, dict) and payload.get("type") == "function":
                        func_name = payload["func_name"]
                        args = payload["args"]
                        kwargs = payload["kwargs"]
                        
                        logging.info(f"⚙️ Running isolated function: {func_name}")
                        if func_name == "run_swarm_solver":
                            from skills.swarm_skill import run_swarm_solver
                            res = run_swarm_solver(*args, **kwargs)
                            result_data = {"status": "success" if res else "failed"}
                        elif func_name == "run_vision_analysis":
                            from skills.vision_skill import run_vision_analysis
                            res = run_vision_analysis(*args, **kwargs)
                            result_data = {"status": "success" if res else "failed"}
                        else:
                            time.sleep(1)
                            result_data = {"status": "success"}
                    else:
                        # 2. ⚡ ACTUAL EXECUTION ROUTING
                        intent = payload.get("intent", self.name)
                        
                        # Execute the skill if we have it loaded in this sandbox
                        if intent in active_skills:
                            # Pass the payload directly to the skill's execution graph
                            success = active_skills[intent].execute(payload)
                            result_data = {"status": "success" if success else "failed"}
                        else:
                            # Fallback for routing MasterOrchestrator transcripts
                            if "transcript" in payload:
                                from core.orchestrator import MasterOrchestrator
                                MasterOrchestrator.route_command(payload["transcript"], payload["dir"])
                                result_data = {"status": "success", "note": "transcript processed"}
                            else:
                                result_data = {"status": "failed", "error": "No matching skill in sandbox."}

                    # 3. 🌉 IPC RESULT DISPATCH: Send data back across the memory boundary
                    self.result_queue.put({
                        "type": "result", 
                        "task_id": task_id, 
                        "worker": self.name, 
                        "data": result_data
                    })
                    
                    # 🧹 PHASE 6: MEMORY CONSOLIDATION
                    # 1. Force Python to drop orphaned variables
                    del payload
                    del result_data
                    gc.collect()

                    # 2. DISABLED FOR VIDEO DEMO - Computer has enough RAM for 1.5b
                    # (Memory management will resume after recording)
                    # current_time = time.time()
                    # if current_time - self.last_eviction_time > 2:
                    #     host_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
                    #     if self.name == "coding" or self.name == "swarm":
                    #         evict_model_from_vram("qwen2.5-coder:7b", host_url)
                    #     elif self.name == "vision":
                    #         evict_model_from_vram("moondream:latest", host_url)
                    #     self.last_eviction_time = current_time
                    #     time.sleep(0.5)

                    logging.info(f"♻️ Memory footprint consolidated for {self.name}.")
                    
                except Exception as e:
                    error_trace = traceback.format_exc()
                    logging.error(f"💥 Critical Failure inside {self.name}:\n{error_trace}")
                    # Send the crash report back to the parent kernel via IPC
                    self.result_queue.put({
                        "type": "error", 
                        "task_id": task_id, 
                        "worker": self.name, 
                        "error": str(e)
                    })
        except KeyboardInterrupt:
            # Catch the CTRL+C signal quietly inside the sandbox
            # Do not print a traceback, just close down the process cleanly
            return


class WorkerSupervisor:
    """The Cipher Kernel: Controls process lifecycles and crash containment."""
    _instance = None # Tracks the single global instance

    def __new__(cls, *args, **kwargs):
        """Forces the Singleton Pattern so only ONE Kernel ever exists."""
        if not cls._instance:
            cls._instance = super(WorkerSupervisor, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        # Prevent the init variables from resetting if imported twice
        if getattr(self, '__initialized', False):
            return
        self.__initialized = True

        self.workers = {}  # {worker_name: CipherWorkerProcess}
        self.queues = {}   # {worker_name: multiprocessing.Queue}
        self.result_queue = multiprocessing.Queue()
        self.active_tasks = {} # {task_id: (worker_name, start_time)}
        self.heartbeats = {} # Track the last pulse timestamp
        self.respawn_timers = {} # Tracks when we last revived a worker
        self.is_shutting_down = False  # Flag to prevent respawn during teardown

        # Core active worker matrix configuration
        self.worker_types = ["vision", "coding", "automation", "swarm"]

    def initialize_kernel(self):
        """Spawns completely isolated child processes across the OS tree."""
        print("🏁 [KERNEL]: Booting Supervisor Engine...")
        for worker_type in self.worker_types:
            self._spawn_worker(worker_type)
        
        # Start the non-blocking monitoring loop inside a standalone daemon thread
        import threading
        threading.Thread(target=self._monitor_lifecycle_loop, daemon=True, name="KernelMonitor").start()

    def _spawn_worker(self, worker_name):
        """Creates a fresh, uncorrupted OS-level process boundary and enforces CPU priority."""
        task_queue = multiprocessing.Queue()
        process = CipherWorkerProcess(worker_name, task_queue, self.result_queue)
        
        self.queues[worker_name] = task_queue
        self.workers[worker_name] = process
        self.heartbeats[worker_name] = time.time()  # Reset heartbeat on spawn to avoid premature flatlines!
        process.start()
        # 🛡️ NEW: Notify Telemetry HUD of worker spawn online status
        try:
            HUDServer.set_worker_health(worker_name, "ONLINE")
        except Exception:
            pass

        # ⚖️ OS-LEVEL CPU THROTTLING
        try:
            p = psutil.Process(process.pid)
            if sys.platform == "win32":
                target_priority = PRIORITY_MAP.get(worker_name, psutil.NORMAL_PRIORITY_CLASS)
                p.nice(target_priority)
            else:
                # POSIX fallback (Mac/Linux)
                p.nice(10 if worker_name in ["swarm", "coding"] else 0)
            
            print(f"⚖️ [SCHEDULER]: '{worker_name}' CPU priority throttled successfully.")
        except Exception as e:
            print(f"⚠️ [SCHEDULER]: Failed to set priority for {worker_name}: {e}")

    def submit_task(self, worker_name: str, task_id: str, payload: dict):
        """Asynchronously dispatches execution parameters across the IPC pipeline."""
        if worker_name not in self.workers:
            print(f"🛑 [KERNEL ERROR]: Unknown worker target '{worker_name}'")
            return False
        
        # Track submission metrics for hard timeout processing
        self.active_tasks[task_id] = (worker_name, time.time())
        
        # Non-blocking IPC pipe write
        self.queues[worker_name].put((task_id, payload))
        print(f"📡 [KERNEL QUEUE]: Task '{task_id}' routed to {worker_name} process.")
        return True

    def _monitor_lifecycle_loop(self):
        """The core operating loop protecting main.py from deadlocks."""
        import queue # Needed for Non-blocking queue reads
        from core.event_bus import EventBus, Event
        from core.hud_server import HUDServer
        
        while True:
            time.sleep(0.1) # Fast tick rate for IPC reading
            now = time.time()
            
            # --- 1. IPC EVENT BRIDGE (Read from children) ---
            try:
                # Drain the result queue continuously without blocking
                while True:
                    ipc_msg = self.result_queue.get_nowait()
                    msg_type = ipc_msg.get("type")
                    
                    if msg_type == "heartbeat":
                        # 🫀 Register the pulse
                        self.heartbeats[ipc_msg["worker"]] = now
                    
                    elif msg_type == "telemetry":
                        HUDServer.push_log(f"🟢 SANDBOX: {ipc_msg['worker']} is online.")
                    
                    elif msg_type == "result":
                        task_id = ipc_msg["task_id"]
                        if task_id in self.active_tasks:
                            del self.active_tasks[task_id] # Clear timeout tracker
                        # Broadcast the child's success to the parent's EventBus
                        EventBus().publish(Event(
                            type="worker.task.completed",
                            source="WorkerSupervisor",
                            data=ipc_msg
                        ))
                    
                    elif msg_type == "error":
                        task_id = ipc_msg.get("task_id")
                        if task_id in self.active_tasks:
                            del self.active_tasks[task_id]
                        HUDServer.push_log(f"🛑 IPC CRASH [{ipc_msg['worker']}]: {ipc_msg['error'][:50]}")
                        
            except queue.Empty:
                pass # Queue is empty, move on to timeout checks

            # --- 2. HARDWARE ENFORCEMENT & WATCHDOG ---
            for worker_name in list(self.workers.keys()):
                # Check 1: Is the OS process literally dead?
                if not self.workers[worker_name].is_alive():
                    # 🛡️ NEW: Notify Telemetry HUD of worker death status
                    try:
                        HUDServer.set_worker_health(worker_name, "DEAD")
                    except Exception:
                        pass

                    # 🛡️ SHUTDOWN CHECK: Only respawn if the system isn't intentionally shutting down
                    if self.is_shutting_down:
                        print(f"💤 [WATCHDOG]: System teardown active. Standing down worker respawn for {worker_name}.")
                        continue

                    last_respawn = self.respawn_timers.get(worker_name, 0)

                    # 🛡️ THE RESPAWN COOLDOWN (Rate Limiting)
                    # If it crashed less than 5 seconds ago, skip respawning this tick to prevent a loop.
                    if now - last_respawn < 5:
                        continue

                    print(f"💥 [WATCHDOG]: {worker_name} collapsed. Respawning (Rate Limited)...")
                    HUDServer.push_log(f"💥 FATAL: {worker_name} collapsed. Respawning (Rate Limited)...")
                    self.respawn_timers[worker_name] = now # Mark the time of revival
                    self._spawn_worker(worker_name)
                    continue
                
                # Check 2: Flatline Detection (45 seconds without a pulse)
                last_beat = self.heartbeats.get(worker_name, now)
                if now - last_beat > 45:
                    print(f"🚨 [WATCHDOG]: '{worker_name}' flatlined (Deadlock detected)! Executing SIGKILL.")
                    HUDServer.push_log(f"🚨 WATCHDOG: Deadlock in {worker_name}. Purging.")
                    self._relaunch_deadlocked_worker(worker_name)

            # --- 3. HARD TIMEOUT ENFORCEMENT ---
            expired_tasks = []
            for task_id, (worker_name, start_time) in list(self.active_tasks.items()):
                max_duration = TASK_TIMEOUTS.get(worker_name, 60)
                if now - start_time > max_duration:
                    print(f"🚨 [KERNEL]: Worker '{worker_name}' hung on task '{task_id}'! Exceeded {max_duration}s.")
                    self._relaunch_deadlocked_worker(worker_name)
                    expired_tasks.append(task_id)
            
            for task_id in expired_tasks:
                del self.active_tasks[task_id]

    def _relaunch_deadlocked_worker(self, worker_name):
        """Terminates a frozen process ID cleanly across OS boundaries and resets the lane."""
        process = self.workers[worker_name]
        pid = process.pid
        
        try:
            print(f"💀 [KERNEL FORCE KILL]: Sending SIGKILL to {worker_name} (PID: {pid})...")
            if sys.platform == "win32":
                os.system(f"taskkill /F /PID {pid}")
            else:
                os.kill(pid, signal.SIGKILL)
        except Exception:
            pass  # Already dead or failed
            
        # Revive execution lane
        try:
            HUDServer.set_worker_health(worker_name, "DEAD")
        except Exception:
            pass
        self._spawn_worker(worker_name)
        HUDServer.push_log(f"🛡️ SUPERVISOR: Force killed and reset hung worker: {worker_name}")

    def shutdown(self):
        """Executes a graceful teardown of all sandboxed processes."""
        self.is_shutting_down = True  # Muzzle the Watchdog before killing workers
        print("\n🛑 [KERNEL]: Initiating global teardown sequence...")
        for worker_name, process in list(self.workers.items()):
            if process.is_alive():
                print(f"💀 [SHUTDOWN]: Terminating {worker_name} (PID: {process.pid})...")
                try:
                    if sys.platform == "win32":
                        os.system(f"taskkill /F /PID {process.pid}")
                    else:
                        process.terminate()
                    process.join(timeout=1)
                except Exception:
                    pass
        print("✅ [KERNEL]: All execution lanes purged. System offline.")


# ============================================================
# 🔌 BACKWARD COMPATIBILITY LAYER & DECORATORS
# ============================================================

# Global single instance initialized for cross-import use
kernel = WorkerSupervisor()

class WorkerManager:
    """Compatibility layer mapping old ThreadPool/ProcessPool executor calls to the WorkerSupervisor."""
    _instance = None
    _lock = multiprocessing.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(WorkerManager, cls).__new__(cls)
                    cls._instance.supervisor = kernel
        return cls._instance

    @classmethod
    def submit_task(cls, func, *args, **kwargs):
        """Map raw skill tasks to the corresponding isolated process worker lanes."""
        instance = cls()
        func_name = getattr(func, "__name__", "anonymous")
        worker_name = "automation"
        if "vision" in func_name.lower():
            worker_name = "vision"
        elif "swarm" in func_name.lower():
            worker_name = "swarm"
        elif "code" in func_name.lower():
            worker_name = "coding"
            
        task_id = f"task_{func_name}_{int(time.time())}"
        payload = {
            "type": "function",
            "func_name": func_name,
            "args": args,
            "kwargs": kwargs
        }
        
        # Submit to supervisor
        success = instance.supervisor.submit_task(worker_name, task_id, payload)
        if not success:
            print(f"⚠️ [WORKER FALLBACK]: Worker '{worker_name}' not available. Executing '{func_name}' synchronously...")
            try:
                # Execute the function directly within the current process boundary
                func(*args, **kwargs)
            except Exception as e:
                print(f"💥 [WORKER FALLBACK CRASH]: Synchronous execution of '{func_name}' failed: {e}")
        
        # Return a simple mock future-like object so calling skills don't break
        class MockFuture:
            def add_done_callback(self, fn):
                pass
            def result(self, timeout=None):
                return True
        return MockFuture()


def crash_shield(func):
    """Decorator to protect skill executions from crashing the orchestrator thread."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error = f"💥 [CRASH SHIELD]: Skill '{func.__name__}' failed: {e}"
            print(error)
            HUDServer.push_log(error)
            return False
    return wrapper
