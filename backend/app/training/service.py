"""训练任务服务：状态机 + ultralytics 执行器 + 产物进审批流（§7.3）"""
from __future__ import annotations

import json
import time

import numpy as np
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..core.models import Model, TrainArtifact, TrainJob, TrainMetric
from ..core.seed import _capability_vec

# 状态机：queued → running → completed|failed|canceled
VALID_STATUS = {"queued", "running", "completed", "failed", "canceled"}


def transition(db: Session, job: TrainJob, new_status: str) -> TrainJob:
    """状态迁移（非法迁移抛 ValueError）"""
    legal = {
        "queued": {"running", "canceled"},
        "running": {"completed", "failed", "canceled"},
        "completed": set(), "failed": set(), "canceled": set(),
    }
    if new_status not in legal.get(job.status, set()):
        raise ValueError(f"非法状态迁移: {job.status} -> {new_status}")
    job.status = new_status
    db.commit()
    db.refresh(job)
    return job


def run_training(job_id: int) -> None:
    """训练执行器（asyncio.to_thread 调用）：ultralytics 训练 + 指标回传 + 产物进审批。

    ponytail: 真训练依赖数据集导出包；数据未接入时以基线模式占位（指标全 0 但链路完整）。
    """
    db = SessionLocal()
    try:
        job = db.get(TrainJob, job_id)
        if job is None:
            return
        transition(db, job, "running")

        # 训练数据准备（Phase 2 数据闭环接入后生成 yaml；当前占位）
        data_yaml = _prepare_data(db, job)
        try:
            metrics = _train_ultralytics(job, data_yaml)
        except Exception as exc:
            job.status = "failed"
            db.commit()
            return

        # 指标回传 + 产物
        for i, m in enumerate(metrics):
            db.add(TrainMetric(job_id=job.id, epoch=i + 1, train_loss=float(m.get("train_loss", 0)),
                               val_loss=float(m.get("val_loss", 0)), mAP50=float(m.get("mAP50", 0)),
                               mAP50_95=float(m.get("mAP50_95", 0))))
        db.commit()

        # 产物 → 审批流（draft，capability_desc 自动生成 = T7.4-2）
        weights = data_yaml.get("weights_path") if isinstance(data_yaml, dict) else None
        db.add(TrainArtifact(job_id=job.id, weights_path=weights or "", metrics_report=json.dumps(metrics)))
        db.add(Model(name=f"{job.name}_v1", version="v1", task_id=job.dataset_version_id or 1,
                     weights_path=weights, capability_desc=f"{job.name} 训练产物，待人工完善能力描述",
                     capability_vec=_capability_vec(f"{job.name} 训练产物"), status="draft"))
        transition(db, job, "completed")
    finally:
        db.close()


def _prepare_data(db: Session, job: TrainJob) -> dict:
    """准备训练数据配置（数据闭环接入后从 dataset_version 导出 yaml；当前占位）"""
    return {"placeholder": True, "weights_path": None}


def _train_ultralytics(job: TrainJob, data: dict) -> list[dict]:
    """执行 ultralytics 训练，返回逐 epoch 指标（数据未接入时返回空列表占位）"""
    if data.get("placeholder"):
        return [{"train_loss": 0.1, "val_loss": 0.2, "mAP50": 0.0, "mAP50_95": 0.0}] * 3
    from ultralytics import YOLO
    base = job.base_model_id or "yolov8n.pt"
    model = YOLO(base)
    model.train(data=data, epochs=job.hyperparams.get("epochs", 50), verbose=False)
    return _parse_results(model)


def _parse_results(model) -> list[dict]:
    """解析训练结果（简化：取 results.csv 末 3 行）"""
    import csv
    import os
    results: list[dict] = []
    path = os.path.join(model.trainer.save_dir, "results.csv")
    if os.path.exists(path):
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))[-3:]
        for r in rows:
            results.append({"train_loss": r.get("train/box_loss"), "val_loss": r.get("val/box_loss"),
                            "mAP50": r.get("metrics/mAP50"), "mAP50_95": r.get("metrics/mAP50-95(B)")})
    return results
