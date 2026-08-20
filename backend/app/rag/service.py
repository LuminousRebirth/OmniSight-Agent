"""RAG 服务：分块入库 + 混合检索 + 待确认转正（§7.8）"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..core.models import Case, KnowledgeChunk, KnowledgeDoc, PendingCase
from .store import store
from .vectorizer import encode_text

CHUNK_SIZE = 500


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """按固定长度分块（可换语义分块）"""
    return [text[i:i + size] for i in range(0, len(text), size)]


def ingest_doc(db: Session, doc_type: str, title: str, content: str,
               created_by: str = "system") -> KnowledgeDoc:
    """文档入库：分块 + 向量化（Milvus 与 DB 双写，chunk id 对齐）"""
    doc = KnowledgeDoc(doc_type=doc_type, title=title, content=content, created_by=created_by)
    db.add(doc)
    db.flush()
    for i, chunk in enumerate(chunk_text(content)):
        c = KnowledgeChunk(doc_id=doc.id, chunk_index=i, content=chunk, embedding=encode_text(chunk))
        db.add(c)
        db.flush()
        store.upsert(c.id, c.embedding, chunk, doc.id)
    db.commit()
    return doc


def _keyword_hits(db: Session, query_text: str) -> dict[int, float]:
    """简化 BM25：查询词在 chunk 内容中的重合比例（0~1）"""
    words = set(query_text.split())
    if not words:
        return {}
    scores: dict[int, float] = {}
    for c in db.query(KnowledgeChunk).all():
        overlap = len(words & set(c.content.split())) / len(words)
        if overlap > 0:
            scores[c.id] = overlap
    return scores


def hybrid_search(db: Session, query_text: str, top_k: int = 5) -> list[dict]:
    """混合检索：Milvus 向量（0.6）+ 关键词重合（0.4）合并取 top_k"""
    qv = encode_text(query_text)
    merged: dict[int, dict] = {}
    for h in store.search(qv, top_k * 2):
        merged[h["chunk_id"]] = {"content": h["content"], "doc_id": h["doc_id"],
                                 "score": 0.6 * h["score"]}
    for chunk_id, s in _keyword_hits(db, query_text).items():
        if chunk_id in merged:
            merged[chunk_id]["score"] += 0.4 * s
        else:
            c = db.get(KnowledgeChunk, chunk_id)
            if c:
                merged[chunk_id] = {"content": c.content, "doc_id": c.doc_id, "score": 0.4 * s}
    ranked = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    return [{"content": r["content"], "doc_id": r["doc_id"], "score": round(r["score"], 4)}
            for r in ranked[:top_k]]


def delete_doc(db: Session, doc_id: int) -> None:
    """删除文档（DB 级联 + Milvus 同步）"""
    store.delete_by_doc(doc_id)
    doc = db.get(KnowledgeDoc, doc_id)
    if doc:
        db.delete(doc)
        db.commit()


def promote_case(db: Session, pending_id: int, human_decision: str, operator: str) -> Case:
    """待确认案例转正入库（§7.8 权限硬规则：仅人工确认可入 cases）"""
    pc = db.get(PendingCase, pending_id)
    if pc is None:
        raise ValueError("待确认案例不存在")
    case = Case(image_path=pc.image_path, task_id=pc.task_id,
                detection_json=pc.detection_json, vlm_result=pc.vlm_result,
                human_decision=human_decision, confirmed_by=operator)
    db.add(case)
    db.delete(pc)
    db.commit()
    return case
