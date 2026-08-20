"""自动路由 API（§5.2：POST /api/route/image、GET /api/route/candidates）"""
from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..agent.trace import new_trace
from ..core.database import get_db
from ..core.models import Model
from .service import route_image

router = APIRouter(prefix="/route", tags=["route"])


class DetectionOut(BaseModel):
    bbox: list[float]
    confidence: float
    class_name: str
    track_id: int | None = None
    metadata: dict = {}


class RouteResponse(BaseModel):
    model: str
    detections: list[DetectionOut]
    fallback_steps: list[str]
    zero_shot_used: bool
    trace_id: str | None = None  # 推理轨迹 id（GET /api/agent/trace/{id} 回放）


@router.post("/image", response_model=RouteResponse)
async def route_image_api(
    file: UploadFile = File(...),
    session_id: str = Form("s1"),
    user_text: str = Form(""),
    db: Session = Depends(get_db),
):
    """上传图片自动路由：选模型 → 检测 → 零样本兜底（恒有结果，不抛错）"""
    data = await file.read()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "图片解码失败")

    trace_id = new_trace()
    result = await route_image(img, user_text, db, trace_id)
    return RouteResponse(
        model=result["model"],
        detections=[
            DetectionOut(bbox=list(d.bbox), confidence=d.confidence,
                         class_name=d.class_name, track_id=d.track_id, metadata=d.metadata)
            for d in result["detections"]
        ],
        fallback_steps=result["fallback_steps"],
        zero_shot_used=result["zero_shot_used"],
        trace_id=trace_id,
    )


@router.get("/candidates")
def route_candidates(db: Session = Depends(get_db)):
    """路由候选池（ACTIVE 模型 + 内置零样本标记）"""
    models = db.query(Model).filter(Model.status == "active").all()
    return [
        {"model": m.name, "task_id": m.task_id, "capability_desc": m.capability_desc}
        for m in models
    ] + [{"model": "zero_shot", "zero_shot": True}]
