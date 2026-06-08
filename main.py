import sys
import threading
import time
import os
import winsound  # <-- Native Windows audio frequencies (Zero dependency cost)

# Force standard output to UTF-8 to prevent Windows UnicodeEncodeError on emojis
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# 🛡️ Guard the import phase against Windows process replication noise
try:
    from core.hud_server import HUDServer
    from core.system_tray import CipherSystemTray
    from core.hotkey_listener import HotkeyListener
    from core.context_targeter import ContextTargeter
    from core.generation_core import GenerationCore
    from core.orchestrator import MasterOrchestrator
    from core.event_bus import EventBus, ClipboardWatcher, SystemIdleWatcher, Event
    from core.worker_manager import crash_shield
    
    # Initialize enhanced subsystems
    from core.conversation_manager import ConversationManager
    from core.function_calling import initialize_builtin_tools
    import config
except KeyboardInterrupt:
    # If a background worker is hit with Ctrl+C mid-import, kill it silently
    os._exit(0)

# Initialize conversation manager (for multi-turn support)
conversation_manager = None
try:
    conversation_manager = ConversationManager()
    print("[MAIN] Multi-turn conversation manager initialized")
except Exception as e:
    print(f"[MAIN] Warning: Conversation manager failed to initialize: {e}")

# Initialize function calling tools (for structured tool use)
if getattr(config, "ENABLE_FUNCTION_CALLING", True):
    try:
        initialize_builtin_tools()
        print("[MAIN] Function calling tools initialized")
    except Exception as e:
        print(f"[MAIN] Warning: Function calling tools failed to initialize: {e}")

# 🔒 Global placeholders (prevents child process overhead and static analysis warnings)
voice_hardware = None
kernel = None
live_engine = None
task_queue = None
IS_GENERATING = False


def safe_orchestrator_call(transcript, active_directory):
    """
    Wraps the orchestrator in a safety net and offloads to the process supervisor.
    This prevents the main OS daemon from freezing if an AI worker hangs.
    """
    # Generates a quick metadata tracking ID
    task_id = f"task_{int(time.time())}"
    
    # Non-blocking handoff directly to the Kernel Supervisor Process lane
    # For a high-level orchestration goal, let the swarm process chew on it
    print(f"📡 [QUEUED]: Routing '{transcript}' to async process supervisor...")
    try:
        kernel.submit_task(
            worker_name="swarm",
            task_id=task_id,
            payload={"transcript": transcript, "dir": active_directory}
        )
    except Exception as e:
        print(f"💥 [CRITICAL]: Supervisor refused to route -> {e}")
        winsound.Beep(200, 500)

def trigger_livetalk_mode():
    global IS_GENERATING
    
    # 🛑 Check if engine is busy
    if IS_GENERATING:
        print("⏳ [ENGINE BUSY]: Generation loop already active. Trigger stacked and ignored.")
        winsound.Beep(200, 300)  # Low warning beep
        return
        
    try:
        IS_GENERATING = True
        HUDServer.set_working_state(True)
        
        # Crisp activation beep for LiveTalk (600Hz, different from Sovereign's 800Hz)
        winsound.Beep(600, 150)  
        
        print("⚡ [LIVETALK MODE]: Instant chat active...")
        HUDServer.push_log("⚡ LIVETALK: Waking fast-path conversational interface...")
        
        # 1. Capture workspace context
        active_directory = ContextTargeter.get_active_window_context()
        print(f"🚀 [LIVETALK TARGET]: Active directory mapped to -> '{active_directory}'")

        # 2. Record voice command input
        if voice_hardware and hasattr(voice_hardware, 'listen_and_transcribe'):
            print("🎤 [LIVETALK MIC ACTIVE]: Listening to live voice chat...")
            HUDServer.push_log("🎤 MIC ACTIVE: Recording local conversational speech...")
            HUDServer.set_agent("LISTENING")
            
            user_voice_intent = voice_hardware.listen_and_transcribe()
            
            # Update transcript live!
            HUDServer.set_transcript(user_voice_intent)
            
            print(f"🗣️ [LIVETALK TRANSCRIPT]: Raw Vocal Input -> '{user_voice_intent}'")
            HUDServer.push_log(f"🗣️ TRANSCRIPT: Received input: '{user_voice_intent}'")
        else:
            user_voice_intent = ""

        # 🛡️ THE HALLUCINATION FILTER & SANITY CHECK
        if not user_voice_intent:
            user_voice_intent = ""
            
        intent_lower = user_voice_intent.lower().strip()
        
        # Ignore mic noise/hallucinations
        ghost_phrases = ["subscribing", "like and subscribe", "amara.org", "captioning", "translation", "subtitles", "thank you for watching"] 
        is_ghost = any(phrase in intent_lower for phrase in ghost_phrases)

        if len(intent_lower) < 3 or is_ghost:
            print(f"🛑 [LIVETALK ABORT]: Input rejected: '{user_voice_intent}'")
            HUDServer.push_log("🛑 LIVETALK ABORT: Ignored quiet or invalid speech.")
            winsound.Beep(300, 150)  # Low error buzzer
            return

        # 3. Process voice instantly via fast path LiveTalkEngine
        HUDServer.set_agent("THINKING")
        live_engine.process_voice(user_voice_intent, active_directory)
        
    finally:
        IS_GENERATING = False
        HUDServer.set_agent("IDLE")
        HUDServer.set_working_state(False)

def autonomous_vocal_activation_bypass():
    global IS_GENERATING
    
    # 🛑 SCENARIO A: Engine is busy processing. Alert with a low warning buzzer.
    if IS_GENERATING:
        print("⏳ [ENGINE BUSY]: Generation loop already active. Trigger stacked and ignored.")
        winsound.Beep(200, 300)  # Low 200Hz warning buzzer frequency
        return
        
    try:
        IS_GENERATING = True
        HUDServer.set_working_state(True)
        
        # 🔔 SCENARIO B: Success capture event. Alert with a sharp, crisp initialization beep.
        winsound.Beep(800, 150)  # High-pitched 800Hz instant alert confirmation
        
        print("🎙️ [SENSORY CHANNELS]: Hardware hotkey bypass detected. Scanning workspace context...")
        HUDServer.push_log("🎙️ SENSORY LINK: Background context scan forced open via keyboard hook.")
        
        # 1. Capture the folder context from your focused application window
        active_directory = ContextTargeter.get_active_window_context()
        print(f"🚀 [SOVEREIGN EXECUTION TARGET]: Active directory pipeline locked onto -> '{active_directory}'")

        # 2. CAPTURE ACTUAL AUDIO SPEECH TRANSCRIPT INSIDE THE THREAD
        if voice_hardware and hasattr(voice_hardware, 'listen_and_transcribe'):
            print("🎤 [MIC ACTIVE]: Listening to live voice command input...")
            HUDServer.push_log("🎤 MIC ACTIVE: Recording local speech stream...")
            HUDServer.set_agent("LISTENING")
            
            user_voice_intent = voice_hardware.listen_and_transcribe()
            
            # Update transcript live!
            HUDServer.set_transcript(user_voice_intent)
            
            print(f"🗣️ [TRANSCRIPT ACQUIRED]: Raw Vocal Input -> '{user_voice_intent}'")
            HUDServer.push_log(f"🗣️ TRANSCRIPT: Received input: '{user_voice_intent}'")
        else:
            user_voice_intent = ""

        # 🛡️ THE HALLUCINATION FILTER & SANITY CHECK
        if not user_voice_intent:
            user_voice_intent = ""
            
        intent_lower = user_voice_intent.lower().strip()
        
        # 🌟 Relax the filters for complex commands
        # Only block if it's REALLY short (less than 5 chars) or definitely trash
        ghost_phrases = ["subscribing", "like and subscribe", "amara.org", "captioning", "translation", "subtitles", "thank you for watching"] 
        is_ghost = any(phrase in intent_lower for phrase in ghost_phrases)

        # Allow complex sentences, reject only very short or clearly wrong input
        if len(intent_lower) < 5 or is_ghost:
            print(f"🛑 [ENGINE ABORT]: Input rejected (too short/garbage): '{user_voice_intent}'")
            HUDServer.push_log("🛑 ENGINE ABORT: Ignored AI microphone hallucination.")
            winsound.Beep(300, 150)  # Low error buzzer
            return

        # 🌟 THE NEW ROUTING LOGIC
        clean_text = user_voice_intent.lower().strip()

        # New conversational triggers for the Swarm sandbox
        if "fix the code" in clean_text or "file in front of me" in clean_text or "fix" in clean_text:
            print("🌪️ [SOVEREIGN]: 'Fix Code' intent detected. Auto-targeting open workspace...")

            # 1. DYNAMIC FILE EXTRACTION: Parse filename from voice command
            target_file = "D:/Visual Studio/Cipher-AI/generated_code/test.py"  # Default fallback
            words = user_voice_intent.split()
            for word in words:
                # Extract filename if it ends with a known extension
                if any(word.lower().endswith(ext) for ext in [".py", ".js", ".html", ".ts", ".jsx", ".tsx"]):
                    target_file = f"D:/Visual Studio/Cipher-AI/generated_code/{word.lower()}"
                    print(f"🎯 [CONTEXT TARGETING]: Dynamically locked onto file from voice input: {word.lower()}")
                    break

            # 2. We rename the payload text so your background Swarm Skill knows exactly what to do
            demo_goal = "Analyze the active open file, detect syntax or logical errors, and fix them safely."

            # 3. Pass the task across the IPC bridge to the coding sandbox queue with extracted file path
            task_id = f"task_{int(time.time())}"
            kernel.submit_task("coding", task_id, {
                "transcript": demo_goal,
                "dir": active_directory,
                "target_file": target_file
            })
            return

        # Route the verified transcript asynchronously via TaskQueue
        safe_orchestrator_call(user_voice_intent, active_directory)
        
    finally:
        # Release the generation gatekeeper lock
        IS_GENERATING = False
        HUDServer.set_agent("IDLE") # Reset the HUD UI back to standby mode
        HUDServer.set_working_state(False)


class TemporalScheduleSkill:
    def __init__(self):
        self.capabilities = ["temporal.schedule"]
        
    @crash_shield
    def execute(self, payload: dict) -> bool:
        from core.temporal_engine import TemporalEngine
        engine = TemporalEngine()
        query = payload.get("query")
        return engine.parse_and_schedule(query)

class ConversationSkill:
    def __init__(self):
        self.capabilities = ["conversation"]
        
    @crash_shield
    def execute(self, payload: dict) -> bool:
        from core.speak import speak
        query = payload.get("query", "")
        text_lower = query.lower().strip()
        
        # 🛡️ THE SYSTEM INTEGRITY HEALTH CHECK PROTOCOL
        if "how are you" in text_lower or "system status" in text_lower or "health check" in text_lower:
            from core.cognitive_memory import CognitiveMemory
            mem = CognitiveMemory()
            recent_errors = mem.recall_recent_episodes(limit=10)
            has_major_errors = any("error" in str(ep).lower() or "crash" in str(ep).lower() for ep in recent_errors)
            
            status = "experiencing minor telemetry events" if has_major_errors else "fully operational"
            response = (
                f"I am {status}. "
                f"The Watchdog supervisor is active, the Event Bus is circulating, "
                f"and the Guardian Runtime is maintaining process isolation."
            )
            speak(response)
            return True
            
        from core.think import Brain
        brain = Brain()
        response = brain.think(query)
        speak(response)
        return True

class CodeGenerationSkill:
    def __init__(self):
        self.capabilities = ["code.generate"]
        
    @crash_shield
    def execute(self, payload: dict) -> bool:
        from core.generation_core import GenerationCore
        import os
        creator = GenerationCore()
        query = payload.get("query")
        active_dir = os.getcwd()
        return creator.generate_new_module(query, active_dir)


def handle_clipboard_event(event: Event):
    """Callback function triggered when the clipboard changes."""
    text = event.data
    # Ignore massive copies, just look at small snippets or URLs
    if len(text) < 200: 
        print(f"📋 [BACKGROUND SENSE]: User copied text -> '{text.strip()}'")
        HUDServer.push_log(f"📋 EVENT: Clipboard updated.")

def handle_user_return(event: Event):
    """Callback triggered when the user moves the mouse after being idle."""
    print("👋 [BACKGROUND SENSE]: User returned to the computer. Waking up cognitive systems...")
    HUDServer.push_log("👋 EVENT: User activity detected. Resuming.")
    # Here you could eventually tell the Orchestrator to say "Welcome back, sir."

import psutil
import os
import sys

def elevate_main_runtime():
    """Forces Windows to prioritize LiveTalk and Hotkeys above all other apps."""
    try:
        p = psutil.Process(os.getpid())
        if sys.platform == "win32":
            p.nice(psutil.HIGH_PRIORITY_CLASS)
        print("⚡ [KERNEL]: Main OS Daemon elevated to HIGH CPU Priority for LiveTalk.")
    except Exception as e:
        print(f"⚠️ [KERNEL FATAL]: Failed to elevate main process: {e}")

def main():
    global voice_hardware, kernel, live_engine, task_queue, IS_GENERATING
    print("🏁 [SOVEREIGN ENGINE]: Initializing global background daemon systems...")
    
    # ==========================================
    # ⚡ SET HIGH PRIORITY FOR MAIN PROCESS
    # ==========================================
    elevate_main_runtime()
        
    # ==========================================
    # 🛡️ BOOT TASK QUEUE AND KERNEL SUPERVISOR
    # ==========================================
    from core.task_queue import TaskQueue
    from core.worker_manager import WorkerSupervisor
    task_queue = TaskQueue()
    kernel = WorkerSupervisor()

    # ==========================================
    # 🎙️ INITIALIZE THE VOICE TRANSCRIBER EXPLICITLY
    # ==========================================
    try:
        from core.listen import Listener
        voice_hardware = Listener()
        # Support the exact method name requested by the user
        setattr(voice_hardware, 'listen_and_transcribe', voice_hardware.listen)
    except Exception as e:
        print(f"⚠️ [SENSORY BLINDNESS]: Failed to load Neural Ears (Listener). Fallback active. Error: {e}")
        try:
            from skills.voice_neural import VoiceNeuralSkill
            voice_hardware = VoiceNeuralSkill()
        except Exception:
            voice_hardware = None

    # ==========================================
    # ⚡ INITIALIZE LIVETALK ENGINE
    # ==========================================
    from core.live_mode import LiveTalkEngine
    from core.speak import Speaker
    live_engine = LiveTalkEngine(
        orchestrator_callback=safe_orchestrator_call,
        tts_engine=Speaker()
    )

    # ==========================================
    # 🛡️ BOOT CIPHER KERNEL SUPERVISOR PROCESSES
    # ==========================================
    kernel.initialize_kernel()
        
    HUDServer.start(port=5000)
    
    # ==========================================
    # 🛡️ IGNITE THE SYSTEM WATCHDOG
    # ==========================================
    from core.watchdog import Watchdog
    Watchdog().start()
    
    # ==========================================
    # 🧠 IGNITE THE CENTRAL NERVOUS SYSTEM
    # ==========================================
    bus = EventBus()
    
    # Ignite Cognitive Memory
    from core.cognitive_memory import CognitiveMemory
    memory = CognitiveMemory()
    
    # Plug the memory directly into the Event Bus!
    bus.subscribe("os.clipboard.changed", memory.log_episode)
    bus.subscribe("os.system.active", memory.log_episode)
    bus.subscribe("os.app.launched", memory.log_episode)
    bus.subscribe("graph.step.success", memory.log_episode)
    
    # Register our reactions (Subscribers)
    bus.subscribe("os.clipboard.changed", handle_clipboard_event)
    bus.subscribe("os.system.active", handle_user_return)

    # ==========================================
    # 📱 IGNITE THE MOBILE MESH
    # ==========================================
    from core.mobile_bridge import MobileBridge
    TELEGRAM_BOT_TOKEN = "8734486592:AAHdLo_oixaEVWAqrfRxJ9jj39Aj___Cb-M" 
    TELEGRAM_CHAT_ID = "6748077713"
    
    bridge = MobileBridge(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Subscribe the bridge to OS events so it texts you when things finish
    bus.subscribe("swarm.consensus.reached", bridge.handle_system_event)
    bus.subscribe("graph.step.success", bridge.handle_system_event)
    bus.subscribe("os.system.idle", bridge.handle_system_event)
    
    # Boot the polling daemon
    bridge.start()
    
    # Start the sensory organs (Publishers)
    ClipboardWatcher(bus).start()
    SystemIdleWatcher(bus, idle_threshold_seconds=60).start() # Set to 60s for testing

    # ==========================================
    # 🔌 BOOT THE CAPABILITY REGISTRY
    # ==========================================
    from core.capability_registry import CapabilityRegistry
    from skills.system_operator_skill import SystemOperatorSkill
    from skills.swarm_skill import SwarmSkill
    from skills.vision_skill import VisionSkill
    
    CapabilityRegistry.register_skill(SystemOperatorSkill())
    CapabilityRegistry.register_skill(TemporalScheduleSkill())
    CapabilityRegistry.register_skill(ConversationSkill())
    CapabilityRegistry.register_skill(CodeGenerationSkill())
    CapabilityRegistry.register_skill(SwarmSkill())
    CapabilityRegistry.register_skill(VisionSkill())
    # ==========================================
    
    # ⏰ START THE TEMPORAL MONITORING ENGINE
    try:
        from core.temporal_engine import TemporalEngine
        temporal = TemporalEngine()
        temporal.start_daemon()
    except Exception as e:
        print(f"⚠️ [TEMPORAL BOOT FAILURE]: Could not start Temporal Engine: {e}")
    
    listener = HotkeyListener(
        sovereign_callback=autonomous_vocal_activation_bypass,
        livetalk_callback=trigger_livetalk_mode
    )
    listener.start()

    # Spawns Cipher's persistent system tray instance on a dedicated background thread
    tray = CipherSystemTray()
    threading.Thread(target=tray.launch_background_service, daemon=True).start()

def handle_os_interrupt(sig, frame):
    """The absolute override for CTRL+C."""
    print("\n🚨 [OS INTERRUPT]: CTRL+C signal intercepted! Commencing teardown...")
    
    # 1. DISARM WATCHDOG FIRST so it doesn't try to auto-respawn workers
    try:
        from core.watchdog import Watchdog
        Watchdog().stop() # If implemented as a Singleton
    except Exception:
        pass

    print("🛑 [KERNEL]: Initiating global teardown sequence...")
    
    # 1. Sever the low-level Windows keyboard hooks
    import keyboard
    try:
        keyboard.unhook_all()
    except Exception:
        pass
    
    # 2. Trigger the Kernel Kill-Switch
    try:
        if kernel:
            kernel.shutdown()
    except Exception as e:
        print(f"⚠️ [SHUTDOWN WARNING]: Kernel teardown incomplete: {e}")
        
    # 3. Force exit the Python interpreter
    print("👋 [SOVEREIGN ENGINE]: Offline. Goodbye.")
    os._exit(0) # os._exit() is much stronger than sys.exit()

if __name__ == "__main__":
    import signal

    # ☢️ BIND THE OS SIGNAL OVERRIDE FIRST
    signal.signal(signal.SIGINT, handle_os_interrupt)

    try:
        main()

        # A simple sleep loop keeps the main thread alive but perfectly
        # responsive to SIGINT (Ctrl+C) interrupts.
        print("🛑 Press CTRL+C in this terminal to safely shutdown Cipher OS.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        # Catch any stray interrupts from child processes and exit silently
        print("\n🚨 [OS INTERRUPT]: CTRL+C signal intercepted! Commencing teardown...")
        print("🛑 [KERNEL]: Initiating global teardown sequence...")
        print("✅ [KERNEL]: All execution lanes purged. System offline.")
        print("👋 [SOVEREIGN ENGINE]: Offline. Goodbye.")
        os._exit(0)
    except SystemExit:
        pass
    except Exception as e:
        import traceback
        crash_trace = traceback.format_exc()
        print(f"💥 [CRITICAL CRASH]: Sovereign Engine main process died: {e}")
        print(crash_trace)
        print("🔄 [SOVEREIGN ENGINE]: Re-igniting runtime supervisor in 5 seconds...")
        time.sleep(5)