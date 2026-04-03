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
from skills.turbo_brain  import turbo_think          # ← fast LLM call
import config

# ── Flask ─────────────────────────────────────────────────────
app     = Flask(__name__)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR  = os.path.join(BASE_DIR, 'web')

# ── Boot sequence ─────────────────────────────────────────────
def boot():
    import time
    t0 = time.perf_counter()
    print("=" * 52)
    print(f"   {config.ASSISTANT_NAME.upper()} OS  — BOOTING")
    print("=" * 52)

    global ear, brain, mouth, skills, agent, context

    # 1. Skills load in parallel (fastest step)
    skills  = FastSkillLoader(max_workers=14)

    # 2. Core modules
    print(">> Loading core modules...")
    ear     = Listener()
    brain   = Brain()
    mouth   = Speaker()

    # 3. Agent + Context
    agent   = CipherAgent(skills, brain)
    context = SessionContext(max_turns=6)

    # 4. Pre-warm Ollama in background (doesn't block boot)
    skills.prewarm_ollama()

    elapsed = time.perf_counter() - t0
    print(f">> Boot complete in {elapsed:.2f}s")
    print("=" * 52)

# Declare globals before boot() fills them
ear = brain = mouth = skills = agent = context = None
boot()


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


# ── CLI main loop ─────────────────────────────────────────────
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    print(f">> Web UI  →  http://localhost:5500")
    print(f">> Chat    →  http://localhost:5500/chat.html")
    print(f">> API     →  http://localhost:5500/api/command")

    mouth.speak(f"{config.ASSISTANT_NAME} is online.")

    while True:
        try:
            print("\n>> SPACE = Voice  |  T = Type  |  Ctrl+C = Quit")
            mode = None
            while True:
                ev = keyboard.read_event()
                if ev.event_type == keyboard.KEY_DOWN:
                    if ev.name == 'space': mode = 'voice'; break
                    if ev.name == 't':
                        while keyboard.is_pressed('t'): pass
                        mode = 'text'; break

            if mode == 'voice':
                mouth.speak("Yes sir?")
                user_text = ear.listen()
            else:
                print("\n>> TEXT MODE")
                user_text = input("> ")

            if not user_text:
                continue

            response = process_command(user_text)

            if isinstance(response, dict):
                mouth.speak(response.get('message', 'Done.'))
            else:
                mouth.speak(response)

        except KeyboardInterrupt:
            print(f"\n>> Shutting down {config.ASSISTANT_NAME}...")
            os._exit(0)


if __name__ == "__main__":
    main()