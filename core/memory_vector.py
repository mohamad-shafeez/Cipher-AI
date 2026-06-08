import chromadb
import os
import uuid

class MemoryVector:
    def __init__(self):
        self.db_dir = "storage"
        self.chroma_dir = os.path.join(self.db_dir, "chroma_db")
        
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        self.client = chromadb.PersistentClient(path=self.chroma_dir)
        self.collection = self.client.get_or_create_collection(name="cipher_cognitive_memory")
        print(">> Memory Vector: ONLINE")

    def remember_fact(self, text_content: str, metadata_dict: dict = None):
        try:
            doc_id = str(uuid.uuid4())
            self.collection.add(
                documents=[text_content],
                metadatas=[metadata_dict or {}],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"[MemoryVector Error] Failed to remember fact: {e}")

    def query_semantic_memory(self, query_text: str, n_results=2) -> list:
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results.get('documents', [[]])[0]
        except Exception as e:
            print(f"[MemoryVector Error] Failed to query memory: {e}")
            return []
