import os
import PyPDF2
from docx import Document

class StudyVaultSkill:
    def __init__(self):
        self.notes_dir = "D:/BCA_Notes" # Point this to your actual notes folder
        os.makedirs(self.notes_dir, exist_ok=True)
        print(">> Study Vault RAG: ONLINE (Academic Intel Active)")

    def _read_pdf(self, path):
        text = ""
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
        return text

    def _read_docx(self, path):
        doc = Document(path)
        return " ".join([p.text for p in doc.paragraphs])

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()
        if not any(t in cmd for t in ["study", "notes", "syllabus", "exam"]):
            return None

        # Logic to find relevant files
        files = [f for f in os.listdir(self.notes_dir) if f.endswith(('.pdf', '.docx'))]
        if not files:
            return "Sir, the Study Vault is empty. Please place your BCA notes in D:/BCA_Notes."

        print(f">> [StudyVault] Scanning {len(files)} files for academic context...")
        
        # Simple RAG: Find the file with the most keyword matches
        # In the future, we can upgrade this to full ChromaDB vector search
        best_match = None
        highest_score = 0
        
        # Basic keyword scan
        keywords = cmd.split()
        for filename in files:
            score = sum(1 for word in keywords if word in filename.lower())
            if score > highest_score:
                highest_score = score
                best_match = filename

        if best_match:
            path = os.path.join(self.notes_dir, best_match)
            content = self._read_pdf(path) if path.endswith('.pdf') else self._read_docx(path)
            # Send context to Agent Core for answering
            return f"FOUND_CONTEXT: {content[:1000]} | FILE: {best_match}"

        return "Sir, I couldn't find a specific file in your vault matching that query."