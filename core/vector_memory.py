import os
import requests
import chromadb
import config
from core.lan_swarm import LANSwarm  # <-- Bring in the swarm coordinator

class VectorMemory:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "..", ".cipher_memory")
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.chroma_client.get_or_create_collection(name="codebase_embeddings")
        self.model = getattr(config, "LLM_MODEL", "qwen2.5-coder:1.5b")

    def _get_embedding(self, text: str) -> list:
        """Generates raw vector tokens via the distributed LAN Swarm network."""
        try:
            # 🌟 DISTRIBUTED UPGRADE: Dispatch embeddings generation to secondary LAN nodes if alive
            response = LANSwarm.dispatch_inference(
                target_endpoint="/api/embeddings",
                payload={"model": self.model, "prompt": text},
                local_timeout=30
            )
            if response.status_code == 200:
                return response.json().get("embedding", [])
        except Exception as e:
            print(f"⚠️ [VECTOR EMBEDDING ERROR]: {str(e)}")
        return []

    def index_file(self, filepath: str, code_content: str):
        if not code_content.strip():
            return
        normalized_path = filepath.replace("\\", "/")
        filename = os.path.basename(normalized_path)
        vector = self._get_embedding(code_content)
        if not vector:
            return
        self.collection.upsert(
            ids=[normalized_path],
            embeddings=[vector],
            metadatas=[{"filename": filename, "path": normalized_path}],
            documents=[code_content]
        )
        print(f"🧠 [VECTOR MEMORY INDEXED]: Semantic signature cached for {filename}")

    def semantic_search(self, error_context: str, limit: int = 2) -> list:
        query_vector = self._get_embedding(error_context)
        if not query_vector:
            return []
        results = self.collection.query(query_embeddings=[query_vector], n_results=limit)
        context_blocks = []
        if results and results['documents'] and results['documents'][0]:
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                context_blocks.append({"path": metadata["path"], "content": doc})
        return context_blocks
