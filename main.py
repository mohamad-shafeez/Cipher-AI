# main.py — CIPHER OS  (Phase 4 — Full Agent + Turbo Boot)
# ============================================================
#   What's new vs Phase 3:
#   ✓ FastSkillLoader  — parallel boot, all skills in ~1-2s
#   ✓ Ollama pre-warm  — model loaded before first query
#   ✓ TurboBrain       — response cache + streaming
#   ✓ CipherAgent      — multi-step planner
#   ✓ SessionContext   — conversational memory
#   ✓ MobileBridge     — phone UI on startup check
# ============================================================

import sys
import os
import threading
import keyboard
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ── Cipher modules ───────────────────────────────────────────
from core.listen         import Listener
from core.think          import Brain
from core.speak          import Speaker
from core.fast_loader    import FastSkillLoader      # ← replaces SkillManager
from core.agent          import CipherAgent
from core.context        import SessionContext
from skills.plagiarism_guardian import get_result, set_result
from skills.turbo_brain  import turbo_think          # ← fast LLM call
import config
from skills.autonomous_coder import get_pending_patch, set_pending_patch, clear_pending_patch

# ── Flask ─────────────────────────────────────────────────────
app     = Flask(__name__)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR  = os.path.join(BASE_DIR, 'web')

# Declare globals BEFORE the boot function so Python knows they exist
ear = brain = mouth = skills = agent = context = None

# ── Boot sequence ─────────────────────────────────────────────
def boot():
    import time
    t0 = time.perf_counter()
    print("=" * 52)
    print(f"   {config.ASSISTANT_NAME.upper()} OS  — GHOST BOOTING")
    print("=" * 52)

    global ear, brain, mouth, skills, agent, context

    # 1. Skills load in parallel (fastest step)
    skills  = FastSkillLoader(max_workers=14)

    # 2. Core modules
    print(">> Initializing Neural Organs...")
    ear     = Listener()
    brain   = Brain()
    mouth   = Speaker()

    # 3. Agent + Context (INJECTING THE SPEAKER FOR GHOST MODE)
    agent   = CipherAgent(skills, brain, speaker=mouth)
    context = SessionContext(max_turns=config.MAX_CONTEXT_TURNS)

    # 4. Pre-warm Ollama in background (doesn't block boot)
    skills.prewarm_ollama()

    elapsed = time.perf_counter() - t0
    print(f">> Ghost Systems Online in {elapsed:.2f}s")
    print("=" * 52)

# Notice we DO NOT call boot() here anymore!
# It will be called at the very end of the file.

# ── Core command processor ────────────────────────────────────
def process_command(command_text: str):
    command = command_text.lower().strip()

    # Strip noise words
    for noise in ["the", "a", "an", "hey", "okay", "so", "please"]:
        command = command.replace(f" {noise} ", " ").strip()
    if not command:
        return "I didn't catch that."

    print(f"\n>> [{command[:80]}]")

    # ── SWARM: build / generate ───────────────────────────────
    if command.startswith("build ") or command.startswith("generate "):
        from codeskills.swarm import CodingSwarm
        swarm     = CodingSwarm()
        clean     = command.replace("build ", "").replace("generate ", "").strip()
        parts     = clean.split(" ", 1)
        if len(parts) < 2:
            return "Please provide a filename and a description."
        return swarm.execute_swarm(parts[1], filename=parts[0])

    # ── SWARM: fix ────────────────────────────────────────────
    if command.startswith("fix "):
        from codeskills.swarm import CodingSwarm
        swarm = CodingSwarm()
        parts = command.replace("fix ", "").split(" ", 1)
        if len(parts) < 2:
            return "Please tell me the filename and the error."
        return swarm.debug_file(parts[0], parts[1])

    # ── Session reset ─────────────────────────────────────────
    if command in ("new session", "new chat", "reset session", "clear memory"):
        agent.clear_session()
        context.reset()
        return "Sir, session memory cleared. Starting fresh."

    # ── Agent core (handles everything else) ──────────────────
    result = agent.run(command)

    if result:
        context.add("user",   command)
        context.add("cipher", result if isinstance(result, str) else result.get("message",""))
        return result

    # ── Turbo brain fallback (cached LLM) ────────────────────
    prefix = context.build_prompt_prefix()
    reply  = turbo_think(prefix + command)   # ← streaming + cache
    context.add("user",   command)
    context.add("cipher", reply)
    return reply


# ── Flask routes ──────────────────────────────────────────────
@app.route('/')
def serve_root():
    return send_from_directory(WEB_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory(WEB_DIR, filename)

@app.route('/api/command', methods=['POST'])
def api_command():
    data      = request.json or {}
    user_text = data.get('command', '').strip()
    print(f"\n[WEB] {user_text[:80]}")
    if not user_text:
        return jsonify({"response": "No command received."})
    result = process_command(user_text)
    if isinstance(result, dict):
        return jsonify({"response": result.get("message",""), "code": result.get("code","")})
    return jsonify({"response": result})

@app.route('/api/agent/log', methods=['GET'])
def api_agent_log():
    return jsonify({"log": agent.get_task_log()[-20:]})

@app.route('/api/agent/context', methods=['GET'])
def api_agent_context():
    return jsonify({
        "history":    context.get_history(),
        "turns":      context.turn_count(),
        "session_mem": agent.get_session_memory(),
    })

@app.route('/api/skills', methods=['GET'])
def api_skills():
    return jsonify({"skills": skills.skill_names(), "count": len(skills.skills)})

def run_flask():
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    # Allows connections from your phone/external devices
    app.run(host="0.0.0.0", port=5500, debug=False, use_reloader=False)


# ── GHOST OS CORE ─────────────────────────────────────────────
def summon_cipher():
    """Triggered by the Hotkey. Wakes up the Ghost."""
    print("\n>> [GHOST SUMMONED]")
    
    # 1. Trigger the Royal Greeting for Shafeez
    if agent:
        agent.activate_ghost() 
    
    # 2. Open the Voice Loop
    while True:
        user_text = ear.listen()
        if not user_text: 
            continue
        
        # 3. Dismissal Protocol (Voice Command to hide the Ghost)
        if any(w in user_text.lower() for w in ["dismissed", "go to sleep", "close cipher", "goodbye"]):
            mouth.speak("Returning to the shadows, Shafeez. Systems standing by.")
            break # Exits the voice loop, returns to background waiting
            
        # 4. Process the command
        response = process_command(user_text)
        
        if isinstance(response, dict):
            mouth.speak(response.get('message', 'Done.'))
        elif response:
            mouth.speak(response)

def ghost_listener():
    """Monitors the hotkey silently in the background"""
    import keyboard
    # Bind Ctrl+Space to the summon function
    keyboard.add_hotkey(config.GHOST_HOTKEY, summon_cipher)
    
    # Keep the program running at 0% CPU while waiting
    keyboard.wait()

# ══════════════════════════════════════════════════════════════
# Cipher Autonomous Coder — Kill-Switch Web API
# ══════════════════════════════════════════════════════════════

@app.route('/api/patch/pending', methods=['GET'])
def api_patch_pending():
    patch = get_pending_patch()
    if not patch:
        return jsonify({"status": "none"})
    return jsonify({
        "status":    "pending",
        "file":      patch.get("file", ""),
        "error":     patch.get("error", ""),
        "diff":      patch.get("diff", ""),
        "timestamp": patch.get("timestamp", ""),
    })

@app.route('/api/patch/decision', methods=['POST'])
def api_patch_decision():
    data = request.json or {}
    decision = data.get("decision", "").lower()

    if decision not in ("approved", "rejected"):
        return jsonify({"error": "Invalid decision. Use 'approved' or 'rejected'."}), 400

    patch = get_pending_patch()
    if not patch:
        return jsonify({"error": "No pending patch found."}), 404

    patch["status"] = decision
    set_pending_patch(patch)

    return jsonify({"status": decision, "file": patch.get("file", "")})

# ── EXECUTION ENTRY POINT ─────────────────────────────────────
if __name__ == "__main__":
    # 1. Run the system boot
    boot()

    # 2. Start Flask in a background thread for the Web HUD
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    print(f">> Ghost HUD active at: http://localhost:{config.WEB_PORT}")

    # 3. Start the Ghost Hotkey Listener
    print(f">> GHOST MODE ACTIVE: Summon with {config.GHOST_HOTKEY.upper()}")
    
    try:
        ghost_listener()
    except KeyboardInterrupt:
        import os
        print(f"\n>> Shutting down {config.ASSISTANT_NAME} safely...")
        os._exit(0)

# ══════════════════════════════════════════════════════════════
 
@app.route('/api/plagiarism/check', methods=['POST'])
def api_plagiarism_check():
    """
    Trigger plagiarism analysis from Web UI.
    Body: {
      "text": "...",           # required if no file
      "file_path": "...",      # optional: path to file
      "compare_file": "...",   # optional: for doc vs doc mode
      "mode": "internet"|"document"
    }
    """
    data      = request.json or {}
    text      = data.get("text", "").strip()
    file_path = data.get("file_path", "").strip()
    compare   = data.get("compare_file", "").strip()
    mode      = data.get("mode", "internet")
 
    # Find the skill instance
    plag_skill = None
    for skill in skills.skills:
        if skill.__class__.__name__ == "PlagiarismGuardianSkill":
            plag_skill = skill
            break
 
    if not plag_skill:
        return jsonify({"error": "PlagiarismGuardianSkill not loaded."}), 503
 
    if file_path:
        command = f"check plagiarism in {file_path}"
        if compare:
            command = f"compare {file_path} with {compare} for plagiarism"
    elif text:
        command = f"plagiarism check this text: {text}"
    else:
        return jsonify({"error": "Provide 'text' or 'file_path'."}), 400
 
    result_msg = plag_skill.execute(command)
    return jsonify({"status": "started", "message": result_msg})
 
 
@app.route('/api/plagiarism/result', methods=['GET'])
def api_plagiarism_result():
    """
    Poll for analysis results.
    Returns full report JSON when ready, or {"status": "pending"} while running.
    """
    from skills.plagiarism_guardian import get_result
    result = get_result()
    if not result:
        return jsonify({"status": "pending"})
    return jsonify({"status": "ready", "report": result})        
# ══════════════════════════════════════════════════════════════
# Cipher Autonomous Coder — Kill-Switch Web API
# ══════════════════════════════════════════════════════════════

@app.route('/api/patch/pending', methods=['GET'])
def api_patch_pending():
    patch = get_pending_patch()
    if not patch:
        return jsonify({"status": "none"})
    return jsonify({
        "status":    "pending",
        "file":      patch.get("file", ""),
        "error":     patch.get("error", ""),
        "diff":      patch.get("diff", ""),
        "timestamp": patch.get("timestamp", ""),
    })

@app.route('/api/patch/decision', methods=['POST'])
def api_patch_decision():
    data = request.json or {}
    decision = data.get("decision", "").lower()

    if decision not in ("approved", "rejected"):
        return jsonify({"error": "Invalid decision. Use 'approved' or 'rejected'."}), 400

    patch = get_pending_patch()
    if not patch:
        return jsonify({"error": "No pending patch found."}), 404

    patch["status"] = decision
    set_pending_patch(patch)

    return jsonify({"status": decision, "file": patch.get("file", "")})

if __name__ == "__main__":
    # 1. Boot all 36 skills silently
    loader = FastLoader()
    loader.boot_all()
    
    # 2. Start the Ghost Handler (Hotkey + Wake Word)
    # This runs in the background. No window needed.
    print(">> CIPHER OS: GHOST MODE ENGAGED")
    print(">> Summon via 'Ctrl + Space' or 'Cipher'...")
    
    # Keep the main thread alive without using CPU
    import time
    while True:
        time.sleep(1)