import pickle
import os
import re
from typing import List, Dict, Any, Optional

class BM25Store:
    def __init__(self, index_path: str = "var/bm25_index.pkl"):
        self.index_path = index_path
        self.corpus: List[List[str]] = []
        self.doc_ids: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.index = None
        self._load()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[\w']+", text.lower())

    def _load(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
                self.corpus = data["corpus"]
                self.doc_ids = data["doc_ids"]
                self.metadatas = data["metadatas"]
                from rank_bm25 import BM25Okapi
                self.index = BM25Okapi(self.corpus)

    def save(self):
        os.makedirs(os.path.dirname(self.index_path) if os.path.dirname(self.index_path) else ".", exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({"corpus": self.corpus, "doc_ids": self.doc_ids, "metadatas": self.metadatas}, f)

    def add_documents(self, texts: List[str], doc_ids: List[str], metadatas: List[Dict[str, Any]]):
        from rank_bm25 import BM25Okapi
        tokenized = [self._tokenize(t) for t in texts]
        self.corpus.extend(tokenized)
        self.doc_ids.extend(doc_ids)
        self.metadatas.extend(metadatas)
        self.index = BM25Okapi(self.corpus)
        self.save()

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        if not self.index or not self.corpus:
            return []
        tokenized_query = self._tokenize(query)
        scores = self.index.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [{
            "id": self.doc_ids[i],
            "content": " ".join(self.corpus[i]),
            "metadata": self.metadatas[i],
            "score": float(scores[i])
        } for i in top_indices if scores[i] > 0]

bm25_store = BM25Store()
