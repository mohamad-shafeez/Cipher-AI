import psutil
import subprocess
import platform
import time

class SecurityGuardianSkill:
    def __init__(self):
        print(">> Security Guardian Skill: ONLINE (System Defense Active)")

    def execute(self, command: str) -> str | None:
        try:
            if not command: 
                return None
            
            cmd = command.lower().strip()
            triggers = ["security check", "scan processes", "check network ports", "security scan", "guardian"]
            
            if not any(t in cmd for t in triggers):
                return None

            print("\n" + "="*40)
            print(">> [SECURITY GUARDIAN] SYSTEM SWEEP INITIATED")
            print("="*40)

            # --- 1. HIGH CPU PROCESSES ---
            suspicious_count = 0
            print("\n[ HIGH-CPU PROCESSES ]")
            # Brief sleep allows psutil to measure CPU delta
            time.sleep(0.1) 
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    cpu = p.info['cpu_percent']
                    if cpu and cpu > 40.0:
                        suspicious_count += 1
                        print(f"  [⚠] PID {p.info['pid']} — {p.info['name']} ({cpu}% CPU)")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if suspicious_count == 0:
                print("  [✓] No suspicious high-CPU processes found.")

            # --- 2. NETWORK PORTS ---
            ports_count = 0
            print("\n[ OPEN NETWORK PORTS ]")
            try:
                connections = psutil.net_connections(kind='inet')
                listening = [c for c in connections if c.status == 'LISTEN']
                ports_count = len(listening)
                
                if listening:
                    for c in listening[:5]: # Show top 5 to avoid spam
                        print(f"  [>] PORT {c.laddr.port} — LISTEN")
                    if ports_count > 5:
                        print(f"  ...and {ports_count - 5} more.")
                else:
                    print("  [✓] No open listening ports detected.")
            except psutil.AccessDenied:
                print("  [!] Access Denied: Run as Administrator to view network ports.")
                ports_count = -1

            # --- 3. FIREWALL STATUS ---
            print("\n[ FIREWALL STATUS ]")
            firewall_status = "Unknown"
            try:
                if platform.system() == "Windows":
                    out = subprocess.check_output(["netsh", "advfirewall", "show", "allprofiles", "state"], text=True)
                    firewall_status = "ACTIVE" if "ON" in out.upper() else "INACTIVE"
                    state_icon = "[✓]" if firewall_status == "ACTIVE" else "[⚠]"
                    print(f"  {state_icon} Windows Firewall: {firewall_status}")
                else:
                    out = subprocess.check_output(["ufw", "status"], text=True)
                    firewall_status = "ACTIVE" if "active" in out.lower() else "INACTIVE"
                    state_icon = "[✓]" if firewall_status == "ACTIVE" else "[⚠]"
                    print(f"  {state_icon} Linux Firewall: {firewall_status}")
            except Exception as e:
                print(f"  [!] Could not determine firewall status: {e}")

            print("="*40 + "\n")

            # --- VOICE SUMMARY ---
            # This is the only part Cipher will speak out loud
            voice_response = "Sir, the security sweep is complete. "
            
            if suspicious_count > 0:
                voice_response += f"I detected {suspicious_count} processes consuming high CPU. "
            else:
                voice_response += "CPU metrics are normal. "

            if firewall_status == "ACTIVE":
                voice_response += "The system firewall is currently active and protecting the network. "
            elif firewall_status == "INACTIVE":
                voice_response += "Warning: The system firewall is currently deactivated. "

            voice_response += "I have printed the full tactical report to your terminal for review."

            return voice_response

        except Exception as e:
            print(f"[SecurityGuardian Error] {e}")
            return "Sir, I encountered an error while scanning the system environment."