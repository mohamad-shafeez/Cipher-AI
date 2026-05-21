# ⚡ Cipher OS // Local-First Concurrent AI Runtime

![Status](https://img.shields.io/badge/Status-Active_Development-2ea44f?style=for-the-badge)
![Architecture](https://img.shields.io/badge/Architecture-Event--Driven_Multiprocessing-39ff14?style=for-the-badge)
![Engine](https://img.shields.io/badge/Engine-Local_Inference_(Ollama)-ff007f?style=for-the-badge)

Cipher OS is an experimental, fault-tolerant AI background daemon and runtime for Windows. Moving beyond traditional "chatbot wrappers," Cipher implements a centralized, OS-level AI runtime. 

It utilizes an event-driven architecture, strict process isolation, and OS-level CPU scheduling to manage heavy, multi-agent LLM workloads locally without ever blocking the primary user interface or real-time audio streams.

---

## 🧠 System Architecture

> 🔒 **Note on Repository State:** This public repository serves as the architecture blueprint and core stable build for Cipher OS. Advanced orchestration systems—including cross-project browser automation pipelines, active headless test controllers, private local validation tools, and multimodal worker sandboxes—are maintained within a private development environment to protect proprietary infrastructure design.

Cipher OS is designed as a centralized background runtime, separating high-priority sensory VAD streams from CPU-intensive LLM workflows. The diagram below illustrates the process boundaries, CPU priority rings, IPC serialized queues, and the hardware isolation lanes.

```mermaid
graph TD
    %% Styling
    classDef process fill:#0b0f19,stroke:#00f0ff,stroke-width:2px,color:#d4dde8;
    classDef isolation fill:#1a0b1c,stroke:#ff007f,stroke-width:2px,color:#d4dde8;
    classDef data fill:#061b1c,stroke:#39ff14,stroke-width:2px,color:#d4dde8;

    %% Main Process Layer
    subgraph Main OS Runtime [HIGH_PRIORITY_CLASS]
        Input((Mic / Hotkeys)) --> Dispatcher{Central Orchestrator}
        Dispatcher -- "CTRL+SPACE" --> FastPath[LiveTalk Engine]
        FastPath --> Ollama14[(Ollama: 11434<br>Fast VAD Queue)]
        
        Dispatcher -- "CTRL+SHIFT+SPACE" --> TaskQueue[Kernel Task Queue]
        
        EventBus[[Event Bus]]
        HUD[Telemetry HUD Server]
        EventBus -.-> HUD
    end

    %% IPC Bridge
    TaskQueue == "JSON Payload (IPC)" ==> IPC Bridge

    %% Isolated Sandbox Layer
    subgraph Isolated Worker Sandboxes [IDLE_PRIORITY_CLASS]
        IPC Bridge --> W1[Swarm Worker]
        IPC Bridge --> W2[Vision Worker]
        IPC Bridge --> W3[Coding Worker]
        IPC Bridge --> W4[System Worker]
        
        W1 & W2 & W3 & W4 --> Ollama15[(Ollama: 11435<br>Heavy Compute Queue)]
    end

    %% Watchdog & Persistence
    Watchdog((Kernel Watchdog)) -. "Monitors Heartbeats" .-> W1 & W2 & W3 & W4
    Watchdog -- "SIGKILL (Deadlock)" --> W1
    
    W1 & W2 & W3 & W4 -- "Results / Errors" --> IPC Bridge
    IPC Bridge == "State Sync" ==> EventBus
    
    EventBus --> DB[(SQLite WAL<br>Cognitive Memory)]

    %% Apply Styles
    class Main OS Runtime,FastPath,TaskQueue process;
    class W1,W2,W3,W4,Isolated Worker Sandboxes isolation;
    class Ollama14,Ollama15,DB,HUD data;
```

---

## 🛡️ Core Engineering Pillars

### 1. The Guardian Runtime Kernel
All automated tasks (e.g. Swarm workflows, vision comprehension, filesystem actions) are fully decoupled from the main event thread. The `WorkerSupervisor` tracks OS process identifiers (PIDs) globally and acts as the system kernel. If a subsystem enters an infinite loop or suffers from a memory leak, the primary audio listener and system hotkeys are unaffected.

### 2. Dual-Path Cognition & OS-Level CPU Scheduling
* **LiveTalk (Fast Path):** An ultra-low latency, real-time voice converser running on the primary process. It is bound to Windows `HIGH_PRIORITY_CLASS` scheduler priority to prevent OS thread preemption.
* **Sovereign Workflows (Heavy Path):** Local agent swarm reasoning and visual OCR tasks run inside worker subprocesses. These are automatically allocated to Windows `IDLE_PRIORITY_CLASS`, forcing the CPU to yield 100% of its resources to LiveTalk audio streaming the microsecond voice activation is triggered.
* **Dual Ollama Ports:** LiveTalk communicates on port `11434` while Sovereign tasks run on port `11435`, bypassing LLM query queuing bottlenecks.

### 3. "Shared-Nothing" IPC Messaging Layer
Because Windows utilizes the `spawn` method for multiprocessing (unlike POSIX `fork`), child processes share no global memory address space with the parent process. Cipher utilizes serialized JSON IPC communication channels over standard `multiprocessing.Queue()` lanes, bridging child-state telemetry, execution logs, and capability responses back to the parent `EventBus` without memory collision.

### 4. Flatline Watchdog with Respawn Cooldown
* **Active Heartbeats:** Child processes write timestamp pulses to the supervisor every 3 seconds.
* **Deadlock Recovery:** If a process fails to update its heartbeat for more than 45 seconds, the supervisor executes a native OS force kill (`taskkill /F /PID` on Windows or `SIGKILL` on Linux) to reclaim resources.
* **Respawn Cooldown Gate:** If a process crashes on boot (e.g. due to missing model assets or closed server ports), a 5-second cooldown is enforced to prevent resource-exhausting fork loops and process storms.

### 5. Aggressive Memory Consolidation & VRAM Eviction
Local inference is highly volatile. Cipher prevents VRAM/RAM exhaustion through aggressive cleanup routines:
* **Active VRAM Eviction:** Upon completing a task, the worker sends an eviction payload to Ollama (`{"model": "qwen2.5-coder:7b", "keep_alive": 0}`) to instantly unload the model weights from the GPU.
* **Explicit Garbage Collection:** Post-task executions trigger active Python garbage collection (`gc.collect()`) and explicit scope deletes to purge stale tensors and objects.

### 6. Concurrency Shield & Graceful Teardown
* **SQLite WAL Database:** To allow multiple isolated subprocesses to read and write database episodes simultaneously without throwing `sqlite3.OperationalError: database is locked`, the cognitive layer implements Write-Ahead Logging (`PRAGMA journal_mode=WAL`).
* **Nuclear Shutdown Sequence:** The entrypoint binds `signal.SIGINT` (Ctrl+C). When caught, it intercepts the keyboard interrupt, disables low-level Windows keyboard hooks, terminates the active process trees, and exits immediately via C-level `os._exit(0)` to prevent zombie memory leaks.

### 7. Cross-Project Browser Diagnostics & Headless Instrumentation
Cipher extends its runtime awareness outside its own repository boundaries through decoupled headless browser probing. When targeting external web applications, an isolated diagnostics worker leverages automated instrumentation (via headless browser APIs) to monitor the client-side environment in real time. It intercepts uncaught console exceptions, network failures, and DOM rendering crashes, writing local diagnostic artifacts synchronously without injecting overhead into the target code.

### 8. Multimodal Workflow Augmentation & Human-in-the-Loop QA
The runtime integrates a collaborative human-in-the-loop validation layer for high-throughput visual quality assurance and annotation. Using local multimodal vision pipelines, Cipher parses display layouts and streaming frames to identify visual regression anomalies, object morphing metrics, or structural interface inconsistencies. Instead of executing unvalidated mutations, it acts as an analytical co-pilot, surfacing structured observations to the telemetry HUD for explicit developer approval.

---

## 🎙️ Dual Cognitive Activation Modes

Cipher separates conversational latency from autonomous reasoning through dedicated hardware-triggered execution paths:

| Mode | Trigger | Purpose |
|------|---------|---------|
| LiveTalk | CTRL + SPACE | Ultra-low latency conversational interaction |
| Sovereign Mode | CTRL + SHIFT + SPACE | Heavy autonomous workflows, swarm reasoning, and system execution |

This separation ensures that long-running inference tasks never interfere with real-time voice responsiveness.

---

## 📡 Runtime Telemetry HUD

*(Insert Telemetry HUD Screenshot Here)*

The HUD provides a real-time web interface (`http://localhost:5000`) for monitoring the OS-level runtime, displaying active worker lanes, live CPU/RAM footprint, transcript streams, and individual sandbox heartbeat statuses.

---

## 🧪 Fault Tolerance Validation

Cipher has been stress-tested against:

- worker deadlocks
- forced process termination
- Ollama inference hangs
- interrupted audio streams
- concurrent IPC flooding
- Ctrl+C runtime teardown
- stale heartbeat recovery

Dead workers are automatically detected, terminated, and respawned without affecting the primary runtime loop.

---

## 🔄 Example Runtime Flow

**User Input:**
"Cipher, open Spotify and play the Interstellar soundtrack."

**Pipeline:**
Mic Input → VAD → Faster-Whisper → Intent Parser → ExecutionGraph → IPC Queue → System Worker → Spotify Launch → EventBus → HUD Telemetry → Cognitive Memory

---

## 🧩 Engineering Problems Solved

During development, Cipher required solving several low-level runtime challenges:

- Preventing LLM inference from blocking real-time audio streams
- Managing multiprocessing state safely on Windows (`spawn`)
- Eliminating SQLite concurrency locks using WAL mode
- Recovering from deadlocked AI workers automatically
- Separating conversational and autonomous execution lanes
- Handling graceful teardown of subprocess trees and keyboard hooks
- Reducing VRAM exhaustion during prolonged Ollama sessions

---
## 🚀 Capabilities & Advanced Subsystems

* **Cross-Project Test Runner (`diagnostics_worker`):** Programmatically mounts external project paths, runs localized boot scripts, and attaches telemetry probes to evaluate runtime health.
* **Headless Browser Probe (`browser_probe`):** Headless instrumentation engine capturing console errors, failed network requests, and active application state changes.
* **Assisted Repair Gateway (`repair_worker`):** Reads generated markdown error logs, aggregates contextual code repairs, and serves a structured `[Y/N]` modification gate to the user.
* **Multimodal QA Assistent (`multimodal_analyzer`):** Multi-modal evaluation engine that watches display inputs via local vision models to perform frame-by-frame anomaly detection.
* **Central Patch Database (`project_fixes/`):** A persistent local ledger auditing historical errors, screenshots, and structural corrections across all monitored developer workspaces.

---

## 📡 Subsystem Execution Matrix

| Subsystem Worker | Processing Layer | Data Channel | Primary Core Responsibility |
| :--- | :--- | :--- | :--- |
| **LiveTalk Engine** | Main OS Process | High-Priority Thread | Real-time audio VAD streams and direct system execution shortcuts |
| **Diagnostics Worker**| Isolated Subprocess | Serialized IPC Queue | External path verification, browser telemetry hooks, and log aggregation |
| **Multimodal Analyzer**| Isolated Subprocess | Shared memory frames | Frame analysis, visual QA profiling, and anomaly detection |
| **Agent Swarm Worker**| Isolated Subprocess | JSON IPC Lanes | Multi-node problem solving, code analysis, and local feedback loops |

---

## ⚙️ Tech Stack
* **Language:** Python 3.11+
* **Systems Management:** `multiprocessing`, `psutil`, `signal`, `threading`
* **Local Inference:** Ollama API (`qwen2.5-coder:7b` / `moondream:latest` / `1.5b` models)
* **Audio Pipeline:** `Faster-Whisper` (STT), `pyttsx3` (TTS), `Silero VAD`
* **Data Persistence:** `SQLite3` (WAL-enabled)

---

## 🛠️ Local Boot Sequence

> **Note:** Cipher strictly relies on local model inference to ensure zero data exfiltration.

```bash
# 1. Clone the repository
git clone https://github.com/mohamad-shafeez/Cipher-AI.git
cd Cipher-AI

# 2. Install dependencies
pip install -r requirements-local.txt

# 3. Boot the Primary and Secondary Inference Engines (Dual-Port)
ollama serve # Port 11434 (LiveTalk)
set OLLAMA_HOST=127.0.0.1:11435 && ollama serve # Port 11435 (Heavy Swarm)

# 4. Ignite the Runtime Kernel
python main.py
```
*Once running, access the Telemetry HUD at `http://localhost:5000` to view real-time process monitoring.*

***

*Architected and Engineered by Mohamad Shafeez (2026).*