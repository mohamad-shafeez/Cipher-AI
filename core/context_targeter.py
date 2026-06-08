import ctypes
import os
import re
import psutil
from core.hud_server import HUDServer

class ContextTargeter:
    @classmethod
    def get_active_window_context(cls) -> str:
        """
        Queries the Windows OS kernel for the active foreground window handle,
        resolves its process executable properties, and extracts the target directory path.
        """
        print("🔍 [CONTEXT TARGETER]: Scanning active OS window handles...")
        fallback_dir = "D:/Visual Studio/Cipher-AI/generated_code"
        
        try:
            # 1. Access user32.dll to grab the active foreground window handle memory address
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return fallback_dir

            # 2. Extract the process ID owning that specific window handle thread
            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            
            if pid.value == 0:
                return fallback_dir

            # 3. Instantiate a process profile via psutil to inspect execution scopes
            process = psutil.Process(pid.value)
            proc_name = process.name().lower()
            
            # 4. Fetch the window title text string
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            window_title = buf.value

            print(f"🖥️ [FOREGROUND APPS]: Focused application: '{proc_name}' // Window Title: '{window_title}'")

            # 🌟 PATH EXTRACTION MATRICES
            # Strategy A: If editing in standard tools like VS Code, the absolute path is frequently exposed in the window title string
            path_match = re.search(r'([a-zA-Z]:[\\/][^;\n]+)', window_title)
            if path_match:
                extracted_path = path_match.group(1).replace("\\", "/").strip()
                # Clean trailing editor indicators
                extracted_path = re.sub(r'\s+-\s+.*$', '', extracted_path)
                
                if os.path.exists(extracted_path):
                    target_dir = extracted_path if os.path.isdir(extracted_path) else os.path.dirname(extracted_path)
                    print(f"🎯 [CONTEXT LOCKED]: Dynamically extracted path via window title string metadata -> {target_dir}")
                    HUDServer.push_log(f"🎯 CONTEXT ACQUIRED: Linked to folder path: {os.path.basename(target_dir)}")
                    return target_dir.replace("\\", "/")

            # Strategy B: Fall back to checking the active process's current working directory (CWD) environment state
            try:
                proc_cwd = process.cwd().replace("\\", "/")
                
                # 🛡️ PROTECTED ZONE GATEKEEPER
                # If the fallback path leads to system folders or web browsers, bypass it safely
                ignored_scopes = ["program files", "system32", "appdata", "windows"]
                ignored_apps = ["chrome.exe", "msedge.exe", "firefox.exe", "explorer.exe"]
                
                if any(scope in proc_cwd.lower() for scope in ignored_scopes) or proc_name in ignored_apps:
                    print(f"⚠️ [CONTEXT PROTECTION]: Protected or system directory ignored. Routing to fallback.")
                    return fallback_dir
                
                if os.path.exists(proc_cwd):
                    print(f"🎯 [CONTEXT LOCKED]: Sourced active workspace via process runtime CWD state -> {proc_cwd}")
                    return proc_cwd
            except Exception:
                pass

        except Exception as e:
            print(f"⚠️ [CONTEXT TARGETER CRASH]: Failed to map active window handles: {str(e)}")
            
        return fallback_dir
