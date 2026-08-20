"""VLM 分析 API（§5.6：POST /api/analysis/image 全链路）"""
from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.models import Model, TaskType
from ..detection.manager import manager
from .factory import PROVIDERS, get_provider
from .templates import build_prompt

router = APIRouter(prefix="/analysis", tags=["analysis"])


class DetectionOut(BaseModel):
    bbox: list[float]
    confidence: float
    class_name: str
    track_id: int | None = None
    metadata: dict = {}


class FusedOut(BaseModel):
    """FusedResult 响应（§3.4）"""
    detections: list[DetectionOut]
    severity: str
    description: str
    action: str
    references: list[str]


@router.post("/image", response_model=FusedOut)
async def analyze_image(
    file: UploadFile = File(...),
    user_text: str = Form(""),
    db: Session = Depends(get_db),
):
    """全链路：ACTIVE 模型检测 → prompt 模板 → VLM 分析 → 融合输出"""
    data = await file.read()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "图片解码失败")

    # 1. 检测（ACTIVE 模型）
    active = db.query(Model).filter(Model.status == "active").first()
    if active is None:
        raise HTTPException(404, "无 ACTIVE 模型")
    detections = manager.get(active.name, active.weights_path).detect(img)

    # 2. prompt（任务描述 + 类别；RAG 依据由 T7.8 接入后补充）
    task = db.get(TaskType, active.task_id)
    prompt = build_prompt(task.task_desc if task else user_text,
                          [d.class_name for d in detections])

    # 3. VLM 分析（无 key 自动降级规则兜底）
    fused = get_provider().analyze(data, prompt)
    fused.detections = detections  # 合并检测结果
    return fused


@router.get("/providers")
def list_providers():
    """Provider 列表与当前配置"""
    return {
        "available": list(PROVIDERS),
        "default": settings.vlm_default,
        "fallback": settings.vlm_fallback,
    }
