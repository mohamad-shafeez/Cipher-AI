import os
import shutil
import subprocess
import zipfile
import pathlib
import re
from typing import Optional

class FilesSkill:
    """
    Cipher Skill — Advanced File Manager
    Handles local file operations using Regex NLP parsing for spaces and dynamic locations.
    """
    def __init__(self):
        print(">> File Skills: ONLINE (Advanced NLP & Pathing Active)")
        self.home = pathlib.Path.home()
        self.locations = {
            "desktop": self.home / "Desktop",
            "downloads": self.home / "Downloads",
            "documents": self.home / "Documents",
            "home": self.home
        }

    # ─────────────────────────────────────────
    # FILE OPERATIONS
    # ─────────────────────────────────────────
    def create_file(self, filename: str, location: str = "desktop") -> str:
        try:
            folder = self._resolve_location(location)
            # Ensure it has an extension if none provided
            if "." not in filename:
                filename += ".txt"
            filepath = folder / filename
            filepath.touch()
            return f"Sir, I have created the file {filename} in your {location}."
        except Exception as e:
            return f"I could not create the file. Error: {e}"

    def create_folder(self, foldername: str, location: str = "desktop") -> str:
        try:
            folder = self._resolve_location(location)
            new_folder = folder / foldername
            new_folder.mkdir(parents=True, exist_ok=True)
            return f"Folder '{foldername}' has been created in your {location}."
        except Exception as e:
            return f"I could not create the folder. Error: {e}"

    def delete_item(self, name: str, location: str = "desktop") -> str:
        try:
            folder = self._resolve_location(location)
            filepath = folder / name
            
            if not filepath.exists():
                # Fuzzy matching fallback
                for file in folder.iterdir():
                    if name.lower() in file.name.lower():
                        filepath = file
                        break
            
            if filepath.exists():
                if filepath.is_dir():
                    shutil.rmtree(filepath)
                else:
                    filepath.unlink()
                return f"Sir, I have deleted {filepath.name}."
            return f"I could not find {name} in your {location}."
        except Exception as e:
            return f"Could not delete the item. Error: {e}"

    def list_files(self, location: str = "desktop") -> str:
        try:
            folder = self._resolve_location(location)
            files = [f.name for f in folder.iterdir() if f.name != "desktop.ini"]
            if not files:
                return f"Your {location} is currently empty."
            
            file_count = len(files)
            display_files = ", ".join(files[:5])
            if file_count > 5:
                return f"There are {file_count} items in your {location}. The first few are: {display_files}."
            return f"Files in {location}: {display_files}."
        except Exception as e:
            return f"Could not list files. Error: {e}"

    def open_folder(self, location: str = "desktop") -> str:
        try:
            folder = self._resolve_location(location)
            # Cross-platform safe open (Windows specific explorer call)
            subprocess.Popen(f'explorer "{folder}"')
            return f"Opening your {location} folder now, Sir."
        except Exception as e:
            return f"Could not open the folder. Error: {e}"

    def empty_recycle_bin(self) -> str:
        try:
            subprocess.run(
                ['powershell', '-NoProfile', '-Command', 'Clear-RecycleBin -Force -Confirm:$false'],
                capture_output=True
            )
            return "The recycle bin has been completely emptied, Sir."
        except Exception as e:
            return f"Failed to empty the recycle bin. Error: {e}"

    def find_file(self, filename: str) -> str:
        try:
            # 15 second timeout to prevent system hang
            result = subprocess.run(
                ['where', '/r', str(self.home), filename],
                capture_output=True, text=True, timeout=15
            )
            if result.stdout:
                first_match = result.stdout.strip().split('\n')[0]
                return f"I found {filename}. It is located at: {first_match}"
            return f"I searched your home directory, but could not find {filename}."
        except subprocess.TimeoutExpired:
            return f"Sir, the search for {filename} timed out. Your storage drive is too large to scan quickly."
        except Exception as e:
            return f"Search error: {e}"

    # ─────────────────────────────────────────
    # HELPER
    # ─────────────────────────────────────────
    def _resolve_location(self, loc_str: str) -> pathlib.Path:
        for key in self.locations:
            if key in loc_str.lower():
                return self.locations[key]
        return self.locations["desktop"] # Default

    def _extract_name_and_loc(self, cmd: str, prefix_regex: str) -> tuple[str, str]:
        """Extracts the target name and location using Regex."""
        loc = "desktop"
        for key in self.locations:
            if re.search(r'\b' + key + r'\b', cmd):
                loc = key
                break
        
        # Strip out the location words to isolate the filename
        clean_cmd = re.sub(r'(?:on|in|from|to)\s+(?:my\s+|the\s+)?(?:desktop|downloads|documents|home)', '', cmd).strip()
        
        match = re.search(prefix_regex + r'\s+["\']?([^"\']+)["\']?', clean_cmd)
        name = match.group(1).strip() if match else "new_item"
        return name, loc

    # ─────────────────────────────────────────
    # EXECUTE — NLP VOICE COMMAND ROUTER
    # ─────────────────────────────────────────
    def execute(self, command: str) -> Optional[str]:
        if not command: return None
        cmd = command.lower().strip()

        # 1. Open Folder
        if re.search(r"^(?:open|show)\s+(?:my\s+|the\s+)?(desktop|downloads|documents|folder)", cmd):
            return self.open_folder(cmd)

        # 2. List Files
        if re.search(r"^(?:list|show|what is on|what's on)\s+(?:my\s+|the\s+)?(desktop|downloads|documents|files)", cmd):
            return self.list_files(cmd)

        # 3. Create File
        if re.search(r"(?:create|make|new)\s+(?:a\s+)?file", cmd):
            name, loc = self._extract_name_and_loc(cmd, r"(?:called|named|file)\s*")
            if name == "new_item": name = "new_file.txt"
            return self.create_file(name, loc)

        # 4. Create Folder
        if re.search(r"(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)", cmd):
            name, loc = self._extract_name_and_loc(cmd, r"(?:called|named|folder)\s*")
            if name == "new_item": name = "New_Folder"
            return self.create_folder(name, loc)

        # 5. Delete Item
        if re.search(r"(?:delete|remove|trash)\s+(?:the\s+)?(?:file|folder|item)?", cmd):
            name, loc = self._extract_name_and_loc(cmd, r"(?:delete|remove|file|folder)\s*")
            return self.delete_item(name, loc)

        # 6. Empty Recycle Bin
        if re.search(r"(?:empty|clear)\s+(?:the\s+)?(?:recycle bin|trash)", cmd):
            return self.empty_recycle_bin()

        # 7. Find/Search File
        match = re.search(r"(?:find|search for|where is)\s+(?:the\s+)?(?:file\s+)?(?:called\s+|named\s+)?[\"']?([^\"']+)[\"']?", cmd)
        if match:
            return self.find_file(match.group(1).strip())

        return None