"""Agent API（Phase 2：对话窗口 + 推理轨迹回放）"""
from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import Model, TaskType
from ..detection.manager import manager
from ..vlm.factory import get_provider
from ..vlm.templates import build_prompt
from .trace import get_trace

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatResponse(BaseModel):
    reply: str
    trace_id: str | None = None
    detections: list[dict] = []


@router.get("/trace/{trace_id}")
def trace_api(trace_id: str):
    """推理轨迹回放（每步：决策依据/模型/命中/耗时）"""
    trace = get_trace(trace_id)
    if trace is None:
        raise HTTPException(404, "轨迹不存在")
    return trace


@router.post("/chat", response_model=ChatResponse)
async def chat(
    text: str = Form(""),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Agent 对话：带图 → 检测 + VLM 分析；纯文本 → 系统问答"""
    if file is None:
        return ChatResponse(reply="我是 OmniSight Agent，上传图片可进行智能检测分析，或问我系统状态（如：有哪些模型？）。")

    data = await file.read()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "图片解码失败")

    # 1. 检测（ACTIVE 模型）
    active = db.query(Model).filter(Model.status == "active").first()
    if active is None:
        raise HTTPException(404, "无 ACTIVE 模型")
    detections = manager.get(active.name, active.weights_path).detect(img)

    # 2. VLM 分析（无 key 自动降级规则兜底）
    task = db.get(TaskType, active.task_id)
    prompt = build_prompt(task.task_desc if task else text,
                          [d.class_name for d in detections])
    fused = get_provider().analyze(data, prompt)

    target_summary = "、".join({d.class_name for d in detections}) or "未检出目标"
    reply = (
        f"【{active.name} 分析结果】\n"
        f"检测目标：{target_summary}（{len(detections)} 个）\n"
        f"严重度：{fused.severity}\n"
        f"分析：{fused.description}\n"
        f"处置建议：{fused.action}"
    )
    return ChatResponse(
        reply=reply,
        detections=[{"bbox": list(d.bbox), "confidence": d.confidence,
                     "class_name": d.class_name} for d in detections],
    )
