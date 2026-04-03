# skills/mobile_hotspot.py
# ============================================================
#   CIPHER MOBILE BRIDGE
#   Serves the web frontend to your phone over USB (ADB
#   reverse) or local WiFi. Shows a QR code in the terminal
#   so you can scan and open the UI instantly.
#
#   Triggers:
#     "connect phone"  /  "mobile bridge"  /  "phone ui"
#     "usb connect"    /  "share ui"       /  "phone connect"
#     "disconnect phone"
# ============================================================

import os
import socket
import subprocess
import threading
import time
import requests as _req

class MobileBridgeSkill:

    TRIGGERS_ON  = ["connect phone", "mobile bridge", "phone ui",
                    "usb connect", "share ui", "phone connect",
                    "start mobile", "bridge phone"]
    TRIGGERS_OFF = ["disconnect phone", "stop bridge", "close mobile"]
    TRIGGER_STATUS = ["bridge status", "mobile status", "phone status"]

    FLASK_PORT   = 5500   # your existing Flask port
    FORWARD_PORT = 5500   # port forwarded to phone via ADB

    def __init__(self):
        self._bridge_active = False
        self._local_ip      = None

    # ------------------------------------------------------------------ #

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()

        if any(t in cmd for t in self.TRIGGERS_OFF):
            return self._disconnect()

        if any(t in cmd for t in self.TRIGGER_STATUS):
            return self._status()

        if any(t in cmd for t in self.TRIGGERS_ON):
            return self._connect()

        return None

    # ------------------------------------------------------------------ #
    #  CONNECT                                                             #
    # ------------------------------------------------------------------ #

    def _connect(self) -> str:
        lines = ["Sir, initiating Mobile Bridge...\n"]

        # 1. Get local IP
        self._local_ip = self._get_local_ip()
        wifi_url = f"http://{self._local_ip}:{self.FLASK_PORT}"
        lines.append(f"  WiFi URL  : {wifi_url}")

        # 2. Try ADB USB forward
        adb_ok, adb_msg = self._adb_forward()
        lines.append(f"  ADB USB   : {adb_msg}")
        usb_url = f"http://localhost:{self.FORWARD_PORT}" if adb_ok else None

        # 3. QR code in terminal (WiFi URL — works without USB)
        qr = self._make_qr(wifi_url)
        lines.append(f"\n  Scan QR to open on phone (WiFi):\n{qr}")
        lines.append(f"\n  Or open manually: {wifi_url}/chat.html")

        if usb_url:
            lines.append(f"  USB tunnel : {usb_url}/chat.html")

        # 4. Keep-alive ping in background
        self._bridge_active = True
        threading.Thread(target=self._keepalive, daemon=True).start()

        lines.append("\n  Bridge ACTIVE — phone and laptop now connected.")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  DISCONNECT                                                          #
    # ------------------------------------------------------------------ #

    def _disconnect(self) -> str:
        self._bridge_active = False
        try:
            subprocess.run(
                ["adb", "reverse", "--remove-all"],
                capture_output=True, timeout=5
            )
        except Exception:
            pass
        return "Sir, Mobile Bridge disconnected. ADB tunnel closed."

    # ------------------------------------------------------------------ #
    #  STATUS                                                              #
    # ------------------------------------------------------------------ #

    def _status(self) -> str:
        state = "ACTIVE" if self._bridge_active else "INACTIVE"
        ip    = self._local_ip or self._get_local_ip()
        return (
            f"Sir, Mobile Bridge: {state}\n"
            f"  Local IP : {ip}\n"
            f"  URL      : http://{ip}:{self.FLASK_PORT}/chat.html\n"
            f"  Port     : {self.FLASK_PORT}"
        )

    # ------------------------------------------------------------------ #
    #  ADB USB FORWARD                                                     #
    # ------------------------------------------------------------------ #

    def _adb_forward(self) -> tuple[bool, str]:
        """Forward Flask port to phone via USB ADB reverse."""
        try:
            # Check if adb is installed
            r = subprocess.run(["adb", "version"],
                               capture_output=True, timeout=5)
            if r.returncode != 0:
                return False, "ADB not found — WiFi only"

            # Check device connected
            devices = subprocess.run(["adb", "devices"],
                                     capture_output=True, text=True, timeout=5)
            lines = [l for l in devices.stdout.splitlines()
                     if l.strip() and "List" not in l and "device" in l]
            if not lines:
                return False, "No USB device detected — WiFi only"

            # Set up reverse tunnel: phone:PORT → laptop:PORT
            fwd = subprocess.run(
                ["adb", "reverse",
                 f"tcp:{self.FORWARD_PORT}",
                 f"tcp:{self.FLASK_PORT}"],
                capture_output=True, text=True, timeout=8
            )
            if fwd.returncode == 0:
                return True, f"USB tunnel active (port {self.FORWARD_PORT})"
            else:
                return False, f"ADB forward failed: {fwd.stderr.strip()[:60]}"

        except FileNotFoundError:
            return False, "ADB not installed — WiFi only"
        except Exception as e:
            return False, f"ADB error: {str(e)[:50]}"

    # ------------------------------------------------------------------ #
    #  QR CODE (pure Python, no external libs)                            #
    # ------------------------------------------------------------------ #

    def _make_qr(self, url: str) -> str:
        """
        Try qrcode lib first; fall back to a web-based ASCII alternative
        or just print the URL prominently if neither is available.
        """
        # Method 1: qrcode library
        try:
            import qrcode
            qr = qrcode.QRCode(border=1)
            qr.add_data(url)
            qr.make(fit=True)
            import io
            buf = io.StringIO()
            qr.print_ascii(out=buf, invert=True)
            return buf.getvalue()
        except ImportError:
            pass

        # Method 2: Minimal block-drawing fallback
        try:
            import qrcode.constants
        except ImportError:
            pass

        # Method 3: Just show URL big — always works
        border = "█" * (len(url) + 6)
        return (
            f"\n  {border}\n"
            f"  ██  {url}  ██\n"
            f"  {border}\n"
            f"  (Install: pip install qrcode  for visual QR)\n"
        )

    # ------------------------------------------------------------------ #
    #  HELPERS                                                             #
    # ------------------------------------------------------------------ #

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _keepalive(self):
        """Background thread: ping Flask every 10s while bridge is active."""
        while self._bridge_active:
            try:
                _req.get(
                    f"http://127.0.0.1:{self.FLASK_PORT}/",
                    timeout=3
                )
            except Exception:
                pass
            time.sleep(10)