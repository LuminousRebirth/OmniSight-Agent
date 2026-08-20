"""Milvus 向量库封装（Lite 本地文件，可升级 Standalone；接口稳定便于替换）"""
from __future__ import annotations

from pathlib import Path

from pymilvus import MilvusClient

from .vectorizer import DIM

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


class VectorStore:
    """knowledge_chunks 集合：id 对齐 KnowledgeChunk.id，内容冗余存储便于检索回显"""

    def __init__(self, collection: str = "knowledge_chunks"):
        self.client = MilvusClient(str(DATA_DIR / "milvus.db"))
        self.collection = collection
        if not self.client.has_collection(collection):
            self.client.create_collection(collection, dimension=DIM, metric_type="COSINE")
        self.client.load_collection(collection)  # 检索前必须 load

    def upsert(self, chunk_id: int, vector: list[float], content: str, doc_id: int) -> None:
        self.client.upsert(self.collection, [
            {"id": chunk_id, "vector": vector, "content": content, "doc_id": doc_id},
        ])

    def search(self, vector: list[float], top_k: int) -> list[dict]:
        res = self.client.search(self.collection, data=[vector], limit=top_k,
                                 output_fields=["content", "doc_id"])
        return [{"chunk_id": h["id"], "content": h["entity"]["content"],
                 "doc_id": h["entity"]["doc_id"], "score": 1 - h["distance"]}  # 余弦相似度
                for h in res[0]]

    def delete_by_doc(self, doc_id: int) -> None:
        self.client.delete(self.collection, filter=f"doc_id == {doc_id}")


store = VectorStore()
