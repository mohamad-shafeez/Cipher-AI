import os
import re
import requests # For Ollama integration

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

class DocumentIntelSkill:
    def __init__(self):
        self.output_dir = "generated_code"
        self.context_memory = ""
        self.loaded_file = ""
        self.ollama_url = "http://localhost:11434/api/generate"
        print(">> Document Intelligence Skill: ONLINE (OCR & NLP Active)")

    def _resolve_path(self, filename):
        if os.path.exists(filename): return filename
        vault_path = os.path.join(self.output_dir, filename)
        return vault_path if os.path.exists(vault_path) else None

    def _extract_text(self, path):
        ext = path.rsplit('.', 1)[-1].lower()
        text = ""
        try:
            if ext == 'pdf' and PyPDF2:
                with open(path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() or ""
            elif ext == 'docx' and docx:
                doc = docx.Document(path)
                text = "\n".join([p.text for p in doc.paragraphs])
            return text.strip()
        except Exception as e:
            print(f"[DocumentIntel Error] {e}")
            return ""

    def _query_llm(self, question, context):
        """Uses Phi-3.5 to answer questions based on the document text."""
        prompt = f"Context from document: {context[:3000]}\n\nQuestion: {question}\n\nAnswer concisely as Cipher:"
        payload = {"model": "phi3.5", "prompt": prompt, "stream": False}
        try:
            res = requests.post(self.ollama_url, json=payload, timeout=30)
            return res.json().get("response", "Sir, I couldn't process an answer.")
        except:
            return "Sir, my neural link to the analysis engine is currently timed out."

    def execute(self, command: str) -> str | None:
        try:
            if not command: return None
            cmd = command.lower().strip()

            # --- TRIGGER 1: LOADING A DOCUMENT ---
            if "read" in cmd and (".pdf" in cmd or ".docx" in cmd):
                match = re.search(r"([\w\-. ]+\.(pdf|docx))", cmd)
                if not match: return "Sir, please specify the document name clearly."
                
                filename = match.group(1).strip()
                path = self._resolve_path(filename)
                
                if not path:
                    return f"Sir, I could not find '{filename}' in the root or generated code directory."

                print(f">> [DocumentIntel] Extracting intelligence from: {filename}...")
                text = self._extract_text(path)
                
                if text:
                    self.context_memory = text
                    self.loaded_file = filename
                    return f"Sir, I have analyzed {filename}. I am ready for your questions regarding its content."
                return "Sir, the document appears to be empty or encrypted."

            # --- TRIGGER 2: ASKING ABOUT LOADED DOCUMENT ---
            # If a document is loaded, and the user asks a question
            if self.context_memory and any(w in cmd for w in ["what", "how", "summarize", "explain", "who"]):
                print(f">> [DocumentIntel] Analyzing loaded context for: {self.loaded_file}...")
                return self._query_llm(cmd, self.context_memory)

            return None

        except Exception as e:
            print(f"[DocumentIntel Error] {e}")
            return None