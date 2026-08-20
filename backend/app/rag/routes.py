"""RAG API（§5.7：知识入库/检索/待确认区/转正）"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import PendingCase
from .service import delete_doc, hybrid_search, ingest_doc, promote_case

router = APIRouter(prefix="/rag", tags=["rag"])


class KnowledgeCreate(BaseModel):
    doc_type: str  # regulation|case_source|alert_plan
    title: str
    content: str
    created_by: str = "system"


class SearchRequest(BaseModel):
    query_text: str
    top_k: int = 5


class PendingCreate(BaseModel):
    image_path: str
    task_id: int | None = None
    detection_json: dict = {}
    vlm_result: dict = {}
    auto_generated_by: str = "agent"


class ConfirmRequest(BaseModel):
    operator: str
    human_decision: str


@router.post("/knowledge", status_code=201)
def create_knowledge(payload: KnowledgeCreate, db: Session = Depends(get_db)):
    """知识文档入库（分块 + 向量化，Milvus 与 DB 双写）"""
    doc = ingest_doc(db, payload.doc_type, payload.title, payload.content, payload.created_by)
    return {"id": doc.id, "title": doc.title, "doc_type": doc.doc_type}


@router.delete("/knowledge/{doc_id}")
def remove_knowledge(doc_id: int, db: Session = Depends(get_db)):
    """删除知识文档（含向量）"""
    delete_doc(db, doc_id)
    return {"ok": True}


@router.post("/search")
def search(payload: SearchRequest, db: Session = Depends(get_db)):
    """混合检索（向量 + 关键词）"""
    return {"results": hybrid_search(db, payload.query_text, payload.top_k)}


@router.post("/cases/pending", status_code=201)
def create_pending(payload: PendingCreate, db: Session = Depends(get_db)):
    """Agent 自动结论写入待确认区（未确认不入正式案例库）"""
    pc = PendingCase(**payload.model_dump())
    db.add(pc)
    db.commit()
    db.refresh(pc)
    return pc


@router.post("/cases/{pending_id}/confirm")
def confirm_case(pending_id: int, payload: ConfirmRequest, db: Session = Depends(get_db)):
    """人工确认 → 转正入 cases（R9 硬规则）"""
    try:
        case = promote_case(db, pending_id, payload.human_decision, payload.operator)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return {"id": case.id, "image_path": case.image_path, "human_decision": case.human_decision}
