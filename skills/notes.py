import sqlite3
import os

class NotesSkill:
    def __init__(self):
        # Save the database in the skills folder or base directory
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.db")
        self._init_db()
        print(">> Notes Skill: ONLINE")

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Notes Skill] Initialization Error: {e}")

    def execute(self, command: str) -> str | None:
        try:
            if not command:
                return None

            cmd = command.lower().strip()
            
            # --- TRIGGER DETECTION ---
            is_save = any(w in cmd for w in ["save note", "take note", "create note"])
            is_list = any(w in cmd for w in ["list notes", "my notes", "show notes", "read notes"])
            is_delete = "delete note" in cmd

            if not (is_save or is_list or is_delete):
                return None # Not a notes command, pass to next skill

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # SAVE NOTE
            if is_save:
                # Extract content by removing the trigger verbs
                content = cmd
                for word in ["save note", "take note", "create note", "that"]:
                    content = content.replace(word, "").strip()
                
                if not content:
                    conn.close()
                    return "Sir, what exactly should I write in the note?"
                
                cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
                conn.commit()
                conn.close()
                return f"Sir, I have saved the note: {content}."

            # LIST NOTES
            elif is_list:
                cursor.execute("SELECT id, content FROM notes")
                notes = cursor.fetchall()
                conn.close()
                if not notes:
                    return "Sir, your notepad is currently empty."
                
                response = "Sir, here are your saved notes: "
                # Format into a clean list for the speaker
                note_list = [f"Note {n[0]}: {n[1]}" for n in notes]
                return response + ". ".join(note_list)

            # DELETE NOTE
            elif is_delete:
                # Find the ID number in the command
                words = cmd.split()
                note_id = None
                for word in words:
                    if word.isdigit():
                        note_id = int(word)
                        break

                if note_id is None:
                    conn.close()
                    return "Sir, please specify the ID number of the note you wish to delete."

                cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                conn.commit()
                found = cursor.rowcount > 0
                conn.close()
                
                if not found:
                    return f"Sir, I couldn't find a note with ID {note_id}."
                return f"Sir, note {note_id} has been purged from the database."

            return None

        except Exception as e:
            print(f"[Notes Skill Error] {e}")
            return None