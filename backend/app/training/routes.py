"""训练中心 API（§5.5：任务 CRUD + 指标 + 停止）"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import TrainJob, TrainMetric
from .service import run_training, transition

router = APIRouter(prefix="/training", tags=["training"])

# ponytail: 内存训练任务表（asyncio），重启丢失；Phase 3 换 Celery
TRAIN_TASKS: dict[int, asyncio.Task] = {}


class JobCreate(BaseModel):
    name: str
    dataset_version_id: int
    base_model_id: int | None = None
    hyperparams: dict = {}


class JobOut(BaseModel):
    id: int
    name: str
    dataset_version_id: int
    base_model_id: int | None
    status: str
    created_by: str

    model_config = {"from_attributes": True}


@router.post("/jobs", response_model=JobOut, status_code=201)
async def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    """提交训练任务（异步执行，返回 job_id）"""
    job = TrainJob(name=payload.name, dataset_version_id=payload.dataset_version_id,
                   base_model_id=payload.base_model_id, hyperparams=payload.hyperparams,
                   gpu_ids=[], status="queued", created_by="system")
    db.add(job)
    db.commit()
    db.refresh(job)
    TRAIN_TASKS[job.id] = asyncio.create_task(asyncio.to_thread(run_training, job.id))
    return job


@router.get("/jobs", response_model=list[JobOut])
def list_jobs(status: str | None = None, db: Session = Depends(get_db)):
    """训练任务列表（可按状态过滤）"""
    q = db.query(TrainJob)
    if status:
        q = q.filter(TrainJob.status == status)
    return q.order_by(TrainJob.id.desc()).all()


@router.get("/jobs/{job_id}/metrics")
def job_metrics(job_id: int, db: Session = Depends(get_db)):
    """指标曲线数据"""
    rows = db.query(TrainMetric).filter(TrainMetric.job_id == job_id).order_by(TrainMetric.epoch).all()
    return {"job_id": job_id, "metrics": [
        {"epoch": m.epoch, "train_loss": m.train_loss, "val_loss": m.val_loss,
         "mAP50": m.mAP50, "mAP50_95": m.mAP50_95} for m in rows
    ]}


@router.post("/jobs/{job_id}/stop")
def stop_job(job_id: int, db: Session = Depends(get_db)):
    """停止训练（queued/running → canceled）"""
    job = db.get(TrainJob, job_id)
    if job is None:
        raise HTTPException(404, "任务不存在")
    task = TRAIN_TASKS.pop(job_id, None)
    if task is not None:
        task.cancel()
    try:
        return transition(db, job, "canceled")
    except ValueError as exc:
        raise HTTPException(409, str(exc))
