import time
import os
import pygetwindow as gw

class GlobalWorkspaceWatcher:
    def __init__(self):
        # A matrix of search roots where you keep your development files
        self.search_roots = [
            r"D:\Visual Studio",
            r"D:",
            r"C:\Users\MOHAMAD SHAFEEZ\Desktop",
            r"C:\Users\MOHAMAD SHAFEEZ\Documents"
        ]
        self.current_project_name = None
        self.current_project_path = None
        self.current_active_file = None

    def locate_absolute_path(self, folder_name):
        """Locates the absolute directory path of a project folder across multiple system roots."""
        # Clean up any VS Code modified indicator dots
        folder_name = folder_name.replace("● ", "").strip()
        
        for root in self.search_roots:
            potential_path = os.path.join(root, folder_name)
            if os.path.isdir(potential_path):
                return potential_path
        return None

    def scan_active_window(self):
        try:
            active_window = gw.getActiveWindow()
            if not active_window:
                return

            window_title = active_window.title

            # Detect active VS Code instances globally
            if "Visual Studio Code" in window_title:
                parts = window_title.split(" - ")
                
                if len(parts) >= 2:
                    project_name = parts[-2].strip()
                    active_file = parts[0].strip() if len(parts) > 2 else None

                    # If the project context switched, find its absolute home path on your PC
                    if project_name != self.current_project_name:
                        resolved_path = self.locate_absolute_path(project_name)
                        
                        if resolved_path:
                            self.current_project_name = project_name
                            self.current_project_path = resolved_path
                            self.current_active_file = active_file
                            
                            print("\n" + "="*60)
                            print(f"🌍 [CIPHER GLOBAL WORKSPACE RESOLVER ACTIVATED]")
                            print(f"📁 Mapped Project : {self.current_project_name}")
                            print(f"📍 Resolved Path  : {self.current_project_path}")
                            print(f"📄 Focused File   : {self.current_active_file}")
                            print("="*60 + "\n")
                            
        except Exception as e:
            pass

    def start_loop(self):
        print("📡 [WATCHDOG] Cipher Global Workspace Watcher is running in ABSOLUTE mode...")
        print("💡 You can now open files anywhere in your dev roots (D:\\, D:\\Visual Studio, Desktop, etc.)")
        while True:
            self.scan_active_window()
            time.sleep(1.2)  # High-responsiveness loop with zero CPU footprint

if __name__ == "__main__":
    watcher = GlobalWorkspaceWatcher()
    watcher.start_loop()