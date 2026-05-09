import os
import base64
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

class FileVaultSkill:
    def __init__(self):
        self.vault_dir = "generated_code"
        self.key_file = os.path.join(self.vault_dir, ".vault_salt")
        if not os.path.exists(self.vault_dir):
            os.makedirs(self.vault_dir)
        print(">> File Vault Skill: ONLINE (AES-256 Active)")

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _get_salt(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(16)
            with open(self.key_file, 'wb') as f:
                f.write(salt)
            return salt

    def _process_vault(self, filename, password, action="lock"):
        try:
            salt = self._get_salt()
            key = self._derive_key(password, salt)
            fernet = Fernet(key)
            
            filepath = os.path.join(self.vault_dir, filename)
            if not os.path.exists(filepath):
                return f"Sir, I could not find the file {filename} in the vault."

            with open(filepath, 'rb') as f:
                data = f.read()

            if action == "lock":
                processed_data = fernet.encrypt(data)
                msg = f"Sir, {filename} has been encrypted and locked."
            else:
                processed_data = fernet.decrypt(data)
                msg = f"Sir, {filename} has been decrypted and is now accessible."

            with open(filepath, 'wb') as f:
                f.write(processed_data)
            return msg

        except Exception as e:
            return f"Sir, the operation failed. Perhaps the password was incorrect?"

    def execute(self, command: str) -> str | None:
        try:
            if not command:
                return None

            cmd = command.lower().strip()
            
            # --- TRIGGER DETECTION ---
            is_lock = "lock file" in cmd or "encrypt file" in cmd
            is_unlock = "unlock file" in cmd or "decrypt file" in cmd
            
            if not (is_lock or is_unlock):
                return None

            # --- DATA EXTRACTION ---
            # Syntax: "lock file [FILENAME] with password [PASSWORD]"
            parts = re.search(r"(lock|unlock|encrypt|decrypt) file (.*) with password (.*)", cmd)
            
            if not parts:
                return "Sir, please use the format: lock file [name] with password [password]."

            action_type = "lock" if is_lock else "unlock"
            filename = parts.group(2).strip()
            password = parts.group(3).strip()

            print(f">> [FileVault] {action_type.upper()} request for: {filename}")
            
            return self._process_vault(filename, password, action=action_type)

        except Exception as e:
            print(f"[FileVault Error] {e}")
            return None