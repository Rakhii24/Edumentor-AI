from typing import List, Dict, Any, Callable
from pathlib import Path
import numpy as np
import faiss
import pickle
from edumentor.config import settings


class VectorStore:
    def __init__(self, collection_name: str = "edumentor"):
        self.collection_name = collection_name

        # Directory to store FAISS index + metadata
        self.store_dir = Path(settings.chroma_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.store_dir / "faiss.index"
        self.meta_path = self.store_dir / "metadata.pkl"

        self.embed_fn: Callable[[List[str]], List[List[float]]] = self._init_embedder()

        # Load or initialize FAISS index
        self._load_or_create_index()

    # -----------------------------
    # Embeddings
    # -----------------------------
    def _init_embedder(self) -> Callable[[List[str]], List[List[float]]]:
        try:
            from fastembed import TextEmbedding
            model = TextEmbedding()

            def _embed(texts: List[str]) -> List[List[float]]:
                return [
                    np.asarray(vec, dtype=np.float32)
                    for vec in model.embed(texts)
                ]

            return _embed
        except Exception:
            # Fallback embedder (only if fastembed fails)
            def _noembed(texts: List[str]) -> List[List[float]]:
                return [np.zeros(1536, dtype=np.float32) for _ in texts]

            return _noembed

    # -----------------------------
    # FAISS index handling (FIXED)
    # -----------------------------
    def _load_or_create_index(self):
        if self.index_path.exists() and self.meta_path.exists():
            # ✅ Load existing index
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            # 🔥 FIX: detect embedding dimension dynamically
            test_vec = self.embed_fn(["dimension check"])[0]
            dim = len(test_vec)

            self.index = faiss.IndexFlatL2(dim)
            self.metadata: List[Dict[str, Any]] = []

    def _save(self):
        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    # -----------------------------
    # Public API
    # -----------------------------
    def add_documents(self, docs: List[Dict[str, Any]]) -> int:
        if not docs:
            return 0

        texts = [d["text"] for d in docs]
        embeddings = np.array(self.embed_fn(texts), dtype=np.float32)

        # FAISS dimension is now guaranteed to match
        self.index.add(embeddings)

        for d in docs:
            self.metadata.append(
                {
                    "text": d["text"],
                    "metadata": d.get("metadata", {}),
                }
            )

        self._save()
        return len(docs)

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        qemb = np.array(self.embed_fn([query_text]), dtype=np.float32)
        _, indices = self.index.search(qemb, top_k)

        results: List[Dict[str, Any]] = []
        for idx in indices[0]:
            if idx == -1:
                continue
            results.append(self.metadata[idx])

        return results


# -----------------------------
# Utility helpers (UNCHANGED)
# -----------------------------

def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> List[str]:
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))

        if end == len(words):
            break

        start = end - chunk_overlap
        if start < 0:
            start = 0

    return chunks


def build_doc_entries(
    source_path: Path,
    page: int,
    text: str,
    title: str
) -> List[Dict[str, Any]]:
    chunks = chunk_text(text)
    docs: List[Dict[str, Any]] = []

    for idx, chunk in enumerate(chunks):
        docs.append(
            {
                "id": f"{source_path.name}-{page}-{idx}",
                "text": chunk,
                "metadata": {
                    "title": title,
                    "source": str(source_path),
                    "page": page,
                },
            }
        )

    return docs
