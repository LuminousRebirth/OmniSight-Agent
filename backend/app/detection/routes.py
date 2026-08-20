"""检测 API（§5.3：/api/detect/image、/api/detect/video、/api/detect/tasks/{id}）"""
from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import Model
from .manager import manager
from .pipeline import process_video

router = APIRouter(prefix="/detect", tags=["detect"])

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

# ponytail: 视频任务内存存储，进程重启即丢失；Phase 2 换 Celery/DB 持久化
VIDEO_TASKS: dict[str, dict] = {}


def _pick_model(db: Session, model: str | None) -> str:
    """选择模型名：缺省取 ACTIVE 模型"""
    if model is None:
        active = db.query(Model).filter(Model.status == "active").first()
        if active is None:
            raise HTTPException(404, "无 ACTIVE 模型")
        model = active.name
    return model


class DetectionOut(BaseModel):
    bbox: list[float]
    confidence: float
    class_name: str
    track_id: int | None = None
    metadata: dict = {}


class DetectImageResponse(BaseModel):
    model: str
    detections: list[DetectionOut]
    stub: bool = False  # True = 走了 StubDetector 兜底


@router.post("/image", response_model=DetectImageResponse)
async def detect_image(
    file: UploadFile = File(...),
    model: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """单图检测：缺省用 ACTIVE 模型（helmet_v26）"""
    data = await file.read()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "图片解码失败")

    model_name = _pick_model(db, model)
    m = db.query(Model).filter(Model.name == model_name).first()
    detector = manager.get(model_name, m.weights_path if m else None)
    detections = detector.detect(img)

    return DetectImageResponse(
        model=model_name,
        detections=[
            DetectionOut(
                bbox=list(d.bbox), confidence=d.confidence, class_name=d.class_name,
                track_id=d.track_id, metadata=d.metadata,
            )
            for d in detections
        ],
        stub=detector.detector_type == "stub",
    )


@router.post("/video")
async def detect_video(
    file: UploadFile = File(...),
    model: str | None = Form(None),
    jump_n: int = Form(3),
    db: Session = Depends(get_db),
):
    """视频检测：异步处理，返回 task_id（跳帧 jump_n，默认 3）"""
    model_name = _pick_model(db, model)
    m = db.query(Model).filter(Model.name == model_name).first()

    path = DATA_DIR / f"tmp_{uuid4().hex}.mp4"
    path.write_bytes(await file.read())

    task_id = uuid4().hex
    VIDEO_TASKS[task_id] = {"status": "queued", "model": model_name, "frames_total": 0, "results": []}
    asyncio.create_task(_run_video(task_id, str(path), model_name, m.weights_path if m else None, jump_n))
    return {"task_id": task_id}


async def _run_video(task_id: str, path: str, model_name: str, weights: str | None, jump_n: int) -> None:
    task = VIDEO_TASKS[task_id]
    task["status"] = "running"
    try:
        detector = manager.get(model_name, weights)
        results = await asyncio.to_thread(process_video, path, detector, jump_n)
        task["results"] = [
            {"frame_no": r["frame_no"],
             "detections": [d.__dict__ | {"bbox": list(d.bbox)} for d in r["detections"]]}
            for r in results
        ]
        task["status"] = "completed"
    except Exception as exc:
        task["status"] = "failed"
        task["error"] = str(exc)
    finally:
        Path(path).unlink(missing_ok=True)


@router.get("/tasks/{task_id}")
def get_video_task(task_id: str):
    """查询视频检测任务进度/结果"""
    task = VIDEO_TASKS.get(task_id)
    if task is None:
        raise HTTPException(404, "任务不存在")
    return task
