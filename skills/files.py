# skills/files.py
import os
import shutil
import subprocess
import zipfile
import pathlib
import datetime
import config

class FileSkills:
    def __init__(self):
        print(">> File Skills: ONLINE")
        self.home = pathlib.Path.home()
        self.desktop = self.home / "Desktop"
        self.downloads = self.home / "Downloads"
        self.documents = self.home / "Documents"

    # ─────────────────────────────────────────
    # FILE OPERATIONS
    # ─────────────────────────────────────────
    def create_file(self, filename, location="desktop"):
        try:
            folder = self._resolve_location(location)
            filepath = folder / filename
            filepath.touch()
            return f"Created {filename} on your {location}."
        except Exception as e:
            return f"Could not create file: {e}"

    def create_folder(self, foldername, location="desktop"):
        try:
            folder = self._resolve_location(location)
            new_folder = folder / foldername
            new_folder.mkdir(parents=True, exist_ok=True)
            return f"Created folder {foldername} on your {location}."
        except Exception as e:
            return f"Could not create folder: {e}"

    def delete_file(self, filename, location="desktop"):
        try:
            folder = self._resolve_location(location)
            filepath = folder / filename
            if filepath.exists():
                if filepath.is_dir():
                    shutil.rmtree(filepath)
                else:
                    filepath.unlink()
                return f"Deleted {filename}."
            return f"Could not find {filename}."
        except Exception as e:
            return f"Could not delete: {e}"

    def rename_file(self, old_name, new_name, location="desktop"):
        try:
            folder = self._resolve_location(location)
            old_path = folder / old_name
            new_path = folder / new_name
            old_path.rename(new_path)
            return f"Renamed {old_name} to {new_name}."
        except Exception as e:
            return f"Could not rename: {e}"

    def move_file(self, filename, from_location, to_location):
        try:
            from_folder = self._resolve_location(from_location)
            to_folder = self._resolve_location(to_location)
            src = from_folder / filename
            dst = to_folder / filename
            shutil.move(str(src), str(dst))
            return f"Moved {filename} to {to_location}."
        except Exception as e:
            return f"Could not move: {e}"

    def copy_file(self, filename, from_location, to_location):
        try:
            from_folder = self._resolve_location(from_location)
            to_folder = self._resolve_location(to_location)
            src = from_folder / filename
            dst = to_folder / filename
            shutil.copy2(str(src), str(dst))
            return f"Copied {filename} to {to_location}."
        except Exception as e:
            return f"Could not copy: {e}"

    def list_files(self, location="desktop"):
        try:
            folder = self._resolve_location(location)
            files = [f.name for f in folder.iterdir()]
            if not files:
                return f"No files found on {location}."
            return f"Files on {location}: {', '.join(files[:5])}{'and more.' if len(files) > 5 else '.'}"
        except Exception as e:
            return f"Could not list files: {e}"

    def open_folder(self, location="desktop"):
        try:
            folder = self._resolve_location(location)
            subprocess.Popen(f'explorer "{folder}"')
            return f"Opening {location} folder."
        except Exception as e:
            return f"Could not open folder: {e}"

    def zip_file(self, filename, location="desktop"):
        try:
            folder = self._resolve_location(location)
            filepath = folder / filename
            zip_path = folder / f"{filename}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.write(filepath, filename)
            return f"Zipped {filename} successfully."
        except Exception as e:
            return f"Could not zip: {e}"

    def unzip_file(self, filename, location="desktop"):
        try:
            folder = self._resolve_location(location)
            zip_path = folder / filename
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(folder)
            return f"Unzipped {filename} successfully."
        except Exception as e:
            return f"Could not unzip: {e}"

    def empty_recycle_bin(self):
        try:
            subprocess.run(
                ['powershell', '-Command', 'Clear-RecycleBin -Force'],
                capture_output=True
            )
            return "Recycle bin emptied."
        except Exception as e:
            return f"Could not empty recycle bin: {e}"

    def find_file(self, filename):
        try:
            result = subprocess.run(
                ['where', '/r', str(self.home), filename],
                capture_output=True, text=True
            )
            if result.stdout:
                return f"Found {filename} at: {result.stdout.split()[0]}"
            return f"Could not find {filename}."
        except Exception as e:
            return f"Search error: {e}"

    # ─────────────────────────────────────────
    # HELPER
    # ─────────────────────────────────────────
    def _resolve_location(self, location):
        locations = {
            "desktop": self.desktop,
            "downloads": self.downloads,
            "documents": self.documents,
            "home": self.home,
        }
        return locations.get(location.lower(), self.desktop)

    # ─────────────────────────────────────────
    # EXECUTE — VOICE COMMAND ROUTER
    # ─────────────────────────────────────────
    def execute(self, command):
        command_lower = command.lower()

        # Open folder
        if any(w in command_lower for w in ["open desktop", "open downloads", "open documents", "open folder"]):
            for loc in ["desktop", "downloads", "documents"]:
                if loc in command_lower:
                    return self.open_folder(loc)
            return self.open_folder("desktop")

        # List files
        if any(w in command_lower for w in ["list files", "show files", "what's on"]):
            for loc in ["desktop", "downloads", "documents"]:
                if loc in command_lower:
                    return self.list_files(loc)
            return self.list_files("desktop")

        # Create file
        if any(w in command_lower for w in ["create file", "new file", "make file"]):
            words = command_lower.split()
            for i, w in enumerate(words):
                if w in ["called", "named"]:
                    filename = words[i+1] if i+1 < len(words) else "newfile.txt"
                    return self.create_file(filename)
            return self.create_file("newfile.txt")

        # Create folder
        if any(w in command_lower for w in ["create folder", "new folder", "make folder"]):
            words = command_lower.split()
            for i, w in enumerate(words):
                if w in ["called", "named"]:
                    foldername = words[i+1] if i+1 < len(words) else "NewFolder"
                    return self.create_folder(foldername)
            return self.create_folder("NewFolder")

        # Delete
        if any(w in command_lower for w in ["delete file", "remove file", "delete folder"]):
            words = command_lower.split()
            for i, w in enumerate(words):
                if w in ["called", "named", "file", "folder"]:
                    if i+1 < len(words):
                        return self.delete_file(words[i+1])

        # Zip
        if "zip" in command_lower and "unzip" not in command_lower:
            words = command_lower.split()
            for i, w in enumerate(words):
                if w == "zip" and i+1 < len(words):
                    return self.zip_file(words[i+1])

        # Unzip
        if "unzip" in command_lower or "extract" in command_lower:
            words = command_lower.split()
            for i, w in enumerate(words):
                if w in ["unzip", "extract"] and i+1 < len(words):
                    return self.unzip_file(words[i+1])

        # Empty recycle bin
        if any(w in command_lower for w in ["empty recycle", "clear recycle", "empty trash"]):
            return self.empty_recycle_bin()

        # Find file
        if any(w in command_lower for w in ["find file", "search file", "where is"]):
            words = command_lower.split()
            if words:
                return self.find_file(words[-1])

        return None