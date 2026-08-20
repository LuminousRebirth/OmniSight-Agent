"""实时检测流（§5.3）：摄像头 CRUD/测试 + live start/stop + WS 帧/结果推流"""
from __future__ import annotations

import asyncio
import base64
import time
from uuid import uuid4

import cv2
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import CameraSource as CameraSourceModel
from ..core.models import DetectionStream, Model
from .camera.camera_manager import enumerate_cameras, test_camera
from .camera.camera_source import LocalCameraSource, NetworkCameraSource
from .manager import manager

router = APIRouter(tags=["camera"])

# ponytail: 内存流会话表，重启丢失；Phase 2 持久化到 detection_streams
LIVE_STREAMS: dict[str, dict] = {}


class CameraCreate(BaseModel):
    name: str
    source_type: str  # obs|usb|rtsp
    uri: str
    resolution: str | None = None
    fps: int | None = None


class LiveStartRequest(BaseModel):
    camera_id: int
    model: str | None = None
    resolution_mode: str = "smooth"  # smooth|hd


# ── 摄像头源管理 ────────────────────────────────────────

@router.get("/cameras/enumerate")
def list_devices():
    """本机可用摄像头索引（DirectShow 枚举）"""
    return enumerate_cameras()


@router.post("/cameras", status_code=201)
def create_camera(payload: CameraCreate, db: Session = Depends(get_db)):
    """登记摄像头源"""
    cam = CameraSourceModel(**payload.model_dump(), status="idle", created_by="system")
    db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam


@router.get("/cameras")
def list_cameras(db: Session = Depends(get_db)):
    """摄像头源列表（含实时状态）"""
    live_ids = {s["camera_id"] for s in LIVE_STREAMS.values()}
    return [
        {"id": c.id, "name": c.name, "source_type": c.source_type, "uri": c.uri,
         "resolution": c.resolution, "fps": c.fps, "status": c.status, "live": c.id in live_ids}
        for c in db.query(CameraSourceModel).all()
    ]


@router.post("/cameras/{camera_id}/test")
def test_camera_api(camera_id: int, db: Session = Depends(get_db)):
    """测试采集源连通性"""
    cam = db.get(CameraSourceModel, camera_id)
    if cam is None:
        raise HTTPException(404, "摄像头不存在")
    return test_camera(cam.source_type, cam.uri)


# ── 实时检测流 ──────────────────────────────────────────

@router.post("/detect/live/start")
async def live_start(payload: LiveStartRequest, db: Session = Depends(get_db)):
    """启动实时检测流，返回 stream_id（采集 + 检测 + WS 广播）"""
    cam = db.get(CameraSourceModel, payload.camera_id)
    if cam is None:
        raise HTTPException(404, "摄像头不存在")

    model_name = payload.model
    if model_name is None:
        active = db.query(Model).filter(Model.status == "active").first()
        if active is None:
            raise HTTPException(404, "无 ACTIVE 模型")
        model_name = active.name
    m = db.query(Model).filter(Model.name == model_name).first()
    detector = manager.get(model_name, m.weights_path if m else None)

    source = LocalCameraSource(int(cam.uri)) if cam.source_type == "usb" else NetworkCameraSource(cam.uri)
    if not source.open():
        raise HTTPException(400, "无法打开采集源")

    stream_id = uuid4().hex
    stream = {
        "id": stream_id, "camera_id": cam.id, "model": model_name,
        "detector": detector, "source": source, "running": True,
        "clients": set(), "frames": 0, "alerts": 0,
        "resolution_mode": payload.resolution_mode,
    }
    LIVE_STREAMS[stream_id] = stream
    asyncio.create_task(_stream_loop(stream))

    db.add(DetectionStream(camera_id=cam.id, model_id=m.id if m else None, status="running"))
    db.commit()
    return {"stream_id": stream_id}


async def _stream_loop(stream: dict) -> None:
    """采集循环：读帧 → 检测 → 广播 frame（jpeg base64）/ result 消息"""
    detector = stream["detector"]
    quality = 60 if stream["resolution_mode"] == "hd" else 40

    while stream["running"]:
        frame = await asyncio.to_thread(stream["source"].read_frame)
        if frame is None:
            await asyncio.sleep(0.1)
            continue

        detections = []
        try:
            detections = await asyncio.to_thread(detector.detect, frame)
        except Exception:
            pass
        stream["frames"] += 1
        if detections:
            stream["alerts"] += len(detections)

        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not ok:
            continue
        frame_msg = {"type": "frame", "jpeg": base64.b64encode(buf.tobytes()).decode(),
                     "ts": time.time(), "model": stream["model"],
                     "fps": 0, "resolution": f"{frame.shape[1]}x{frame.shape[0]}"}
        result_msg = {"type": "result",
                      "detections": [
                          {"bbox": list(d.bbox), "confidence": d.confidence,
                           "class_name": d.class_name, "track_id": d.track_id}
                          for d in detections
                      ], "alert_ids": []}

        for ws in list(stream["clients"]):
            try:
                await ws.send_json(frame_msg)
                if detections:
                    await ws.send_json(result_msg)
            except Exception:
                stream["clients"].discard(ws)

    stream["source"].release()
    for ws in list(stream["clients"]):
        try:
            await ws.send_json({"type": "status", "state": "stopped", "detail": "流已停止"})
        except Exception:
            pass
    stream["clients"].clear()


@router.websocket("/detect/live/{stream_id}")
async def live_ws(websocket: WebSocket, stream_id: str):
    """订阅实时检测流（多客户端共享一路采集）"""
    stream = LIVE_STREAMS.get(stream_id)
    if stream is None:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    stream["clients"].add(websocket)
    try:
        await websocket.send_json({"type": "status", "state": "running", "detail": "已连接"})
        while stream["running"]:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        stream["clients"].discard(websocket)


@router.post("/detect/live/{stream_id}/stop")
async def live_stop(stream_id: str):
    """停止实时检测流"""
    stream = LIVE_STREAMS.get(stream_id)
    if stream is None:
        raise HTTPException(404, "流不存在")
    stream["running"] = False
    result = {"frames_processed": stream["frames"], "alerts_count": stream["alerts"]}
    LIVE_STREAMS.pop(stream_id, None)
    return result
