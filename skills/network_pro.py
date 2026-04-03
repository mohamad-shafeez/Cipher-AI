import socket
import subprocess
import os

try:
    import speedtest
except ImportError:
    speedtest = None

class NetworkProSkill:
    def __init__(self):
        print(">> Network Skill: ONLINE")

    def execute(self, command: str) -> str | None:
        try:
            if not command:
                return None

            cmd = command.lower().strip()

            # --- TRIGGER DETECTION ---
            is_ip = any(w in cmd for w in ["ip address", "my ip", "network address"])
            is_speed = any(w in cmd for w in ["speed test", "internet speed", "connection speed"])
            is_ping = "ping" in cmd

            if not (is_ip or is_speed or is_ping):
                return None

            # GET LOCAL IP
            if is_ip:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                return f"Sir, your local network I.P. address is {ip}."

            # INTERNET SPEED
            elif is_speed:
                if speedtest is None:
                    return "Sir, the speedtest-cli module is not installed in the environment."
                
                print(">> [NetworkSkill] Testing speed (this may take a few seconds)...")
                st = speedtest.Speedtest()
                st.get_best_server() # Essential for accuracy and avoiding errors
                download = st.download() / 1_000_000
                upload = st.upload() / 1_000_000
                return f"Sir, the results are in. Download speed is {download:.2f} Mbps and upload is {upload:.2f} Mbps."

            # PING WEBSITE
            elif is_ping:
                # Extract target (e.g. "ping google.com")
                target = cmd.replace("ping", "").strip()
                
                if not target:
                    return "Sir, please specify a target domain to ping."

                # -n 2 means only 2 packets (fast response)
                # Windows uses -n, Linux/Mac uses -c
                flag = "-n" if os.name == 'nt' else "-c"
                
                result = subprocess.run(
                    ["ping", flag, "2", target],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    return f"Sir, the connection to {target} is stable and reachable."
                else:
                    return f"Sir, I was unable to establish a connection with {target}."

            return None

        except Exception as e:
            print(f"[NetworkSkill Error] {e}")
            return None