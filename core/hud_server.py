import http.server
import socketserver
import threading
import json
import os
import re
import psutil
import time

# 🌐 Global thread-safe state variables
TELEMETRY_LOGS = []
CURRENT_AGENT = "IDLE"
LAST_TRANSCRIPT = ""
MEMORY_RETRIEVALS = []
SYSTEM_STATUS = "ONLINE"
IS_WORKING = False
TOTAL_REPAIRS = 0

# 🛡️ New: Track the isolated execution lanes
WORKER_HEALTH = {
    "vision": "OFFLINE",
    "coding": "OFFLINE",
    "automation": "OFFLINE",
    "swarm": "OFFLINE"
}

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Allows the server to handle the infinite SSE stream AND file requests concurrently."""
    allow_reuse_address = True
    daemon_threads = True

class HUDRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress console spam

    def do_GET(self):
        global TELEMETRY_LOGS, CURRENT_AGENT, LAST_TRANSCRIPT, MEMORY_RETRIEVALS, SYSTEM_STATUS, IS_WORKING, TOTAL_REPAIRS, WORKER_HEALTH
        
        # ⚡ NEW ROUTE: High-Frequency Server-Sent Events (SSE) Stream
        if self.path == "/api/stream":
            self.send_response(200)
            self.send_header('Content-type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Grab the main process to track its specific CPU usage
            main_process = psutil.Process(os.getpid())
            
            try:
                while True:
                    payload = {
                        "cpu_total": psutil.cpu_percent(interval=None),
                        "cpu_main": main_process.cpu_percent(interval=None),
                        "ram_usage": psutil.virtual_memory().percent,
                        "system_status": SYSTEM_STATUS,
                        "current_agent": CURRENT_AGENT,
                        "last_transcript": LAST_TRANSCRIPT,
                        "reflection_logs": TELEMETRY_LOGS[-40:], # Last 40 lines
                        "worker_health": WORKER_HEALTH,
                        "background_tasks_running": IS_WORKING,
                        "total_repairs": TOTAL_REPAIRS,
                        "memory_retrievals": MEMORY_RETRIEVALS
                    }
                    # Format as SSE standard: "data: <json>\n\n"
                    self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode('utf-8'))
                    self.wfile.flush()
                    time.sleep(0.5) # Stream at 2 FPS
            except Exception:
                pass # Client disconnected (closed the browser tab)
            return

        # 📊 API ROUTE: Matches front-end expectation for legacy polling
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            payload = {
                "cpu_usage": psutil.cpu_percent(interval=None),
                "ram_usage": psutil.virtual_memory().percent,
                "system_status": SYSTEM_STATUS,
                "current_agent": CURRENT_AGENT,
                "last_transcript": LAST_TRANSCRIPT,
                "reflection_logs": TELEMETRY_LOGS[-40:],  # Send last 40 logs
                "memory_retrievals": MEMORY_RETRIEVALS,
                "background_tasks_running": IS_WORKING,
                "total_repairs": TOTAL_REPAIRS,
                "worker_health": WORKER_HEALTH
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        # 🎨 ROUTE: Serve the cyberpunk index.html from disk dynamically
        if self.path == "/" or self.path == "/index.html":
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                html_path = os.path.join(base_dir, "templates", "index.html")
                
                if os.path.exists(html_path):
                    with open(html_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    content = content.replace("{{ url_for('static', filename='css/style.css') }}", "/static/css/style.css")
                    content = content.replace("{{ url_for('static', filename='js/app.js') }}", "/static/js/app.js")
                    
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                else:
                    raise FileNotFoundError()
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                fallback_html = f"""<!DOCTYPE html>
                <html>
                <head>
                    <title>CIPHER OS // COGNITIVE INTEGRITY SYSTEM</title>
                    <style>
                        body {{ background: #060809; color: #d4dde8; font-family: sans-serif; text-align: center; padding-top: 15%; }}
                        h2 {{ color: #00f0ff; font-weight: 300; letter-spacing: 2px; }}
                        p {{ color: #ff007f; }}
                    </style>
                </head>
                <body>
                    <h2>CIPHER OS // HUD INTERCEPT ACTIVE</h2>
                    <p>Error loading index.html dynamically: {e}</p>
                </body>
                </html>"""
                self.wfile.write(fallback_html.encode("utf-8"))
            return

        # 💅 ROUTE: Serve style.css
        if self.path == "/static/css/style.css":
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                css_path = os.path.join(base_dir, "templates", "static", "css", "style.css")
                with open(css_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "text/css; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except Exception:
                self.send_response(404)
                self.end_headers()
            return

        # ⚡ ROUTE: Serve app.js
        if self.path == "/static/js/app.js":
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                js_path = os.path.join(base_dir, "templates", "static", "js", "app.js")
                with open(js_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "application/javascript; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except Exception:
                self.send_response(404)
                self.end_headers()
            return

        super().do_GET()

    def do_POST(self):
        global TELEMETRY_LOGS, CURRENT_AGENT, LAST_TRANSCRIPT, MEMORY_RETRIEVALS, SYSTEM_STATUS, IS_WORKING, TOTAL_REPAIRS, WORKER_HEALTH

        if self.path == "/api/update":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                action = data.get("action")
                value = data.get("value")

                if action == "push_log":
                    TELEMETRY_LOGS.append(value)
                elif action == "set_agent":
                    CURRENT_AGENT = value
                elif action == "set_transcript":
                    LAST_TRANSCRIPT = value
                elif action == "set_working_state":
                    IS_WORKING = bool(value)
                elif action == "increment_repairs":
                    TOTAL_REPAIRS += 1
                elif action == "set_worker_health":
                    worker_name = data.get("worker")
                    status = data.get("status")
                    if worker_name in WORKER_HEALTH:
                        WORKER_HEALTH[worker_name] = status

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode("utf-8"))

            except (ConnectionResetError, ConnectionAbortedError):
                # Silently ignore connection drops during shutdown
                pass
            except Exception as e:
                try:
                    self.send_response(500)
                    self.end_headers()
                except (ConnectionResetError, ConnectionAbortedError):
                    pass
            return

        self.send_response(404)
        self.end_headers()

class HUDServer:
    _running = False

    @classmethod
    def push_log(cls, text: str):
        import requests
        clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text) 
        try:
            requests.post("http://localhost:5000/api/update", json={"action": "push_log", "value": clean_text}, timeout=0.5)
        except Exception:
            global TELEMETRY_LOGS
            TELEMETRY_LOGS.append(clean_text)

    @classmethod
    def set_agent(cls, agent_name: str):
        import requests
        try:
            requests.post("http://localhost:5000/api/update", json={"action": "set_agent", "value": agent_name}, timeout=0.5)
        except Exception:
            global CURRENT_AGENT
            CURRENT_AGENT = agent_name

    @classmethod
    def set_transcript(cls, text: str):
        import requests
        try:
            requests.post("http://localhost:5000/api/update", json={"action": "set_transcript", "value": text}, timeout=0.5)
        except Exception:
            global LAST_TRANSCRIPT
            LAST_TRANSCRIPT = text
            
    @classmethod
    def set_working_state(cls, is_working: bool):
        import requests
        try:
            requests.post("http://localhost:5000/api/update", json={"action": "set_working_state", "value": is_working}, timeout=0.5)
        except Exception:
            global IS_WORKING
            IS_WORKING = is_working

    @classmethod
    def increment_repairs(cls):
        import requests
        try:
            requests.post("http://localhost:5000/api/update", json={"action": "increment_repairs"}, timeout=0.5)
        except Exception:
            global TOTAL_REPAIRS
            TOTAL_REPAIRS += 1

    # 🛡️ NEW METHOD: Hook this into your Watchdog!
    @classmethod
    def set_worker_health(cls, worker_name: str, status: str):
        import requests
        try:
            requests.post("http://localhost:5000/api/update", json={"action": "set_worker_health", "worker": worker_name, "status": status}, timeout=0.5)
        except Exception:
            global WORKER_HEALTH
            if worker_name in WORKER_HEALTH:
                WORKER_HEALTH[worker_name] = status

    @classmethod
    def start(cls, port: int = 5000):
        if cls._running:
            return
        cls._running = True
        
        def run_server():
            # Using our new ThreadedTCPServer!
            with ThreadedTCPServer(("", port), HUDRequestHandler) as httpd:
                print(f"🌐 [HUD SERVER]: Telemetry stream dashboard broadcast initialized at http://localhost:{port}")
                httpd.serve_forever()
                
        threading.Thread(target=run_server, daemon=True, name="HUD_Server").start()
