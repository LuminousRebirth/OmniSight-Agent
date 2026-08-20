"""种子数据注入（T0-4）：3 任务 + 3 模型 + 3 用户（幂等，仅空库注入）。

开发账号：admin/operator/viewer，密码均为 admin123（生产环境必须改）。
helmet_v26 挂真实权重（E:\\python_code\\yolo\\...\\best.pt），wheelhub/fire 占位。
"""
from __future__ import annotations

import hashlib
import json

from sqlalchemy.orm import Session

from .models import Category, Model, TaskType, User
from .security import hash_password

SEED_TASKS: list[dict] = [
    {"name": "安全帽检测", "task_desc": "检测工地人员是否佩戴安全帽", "categories": ["helmet", "no_helmet"]},
    {"name": "轮毂缺陷检测", "task_desc": "检测轮毂表面划痕/压痕/污渍", "categories": ["scratch", "dent", "stain"]},
    {"name": "烟火检测", "task_desc": "检测火焰与烟雾", "categories": ["fire", "smoke"]},
]

HELMET_WEIGHTS = r"E:\python_code\yolo\runs\models\ppe\HHW_noperson\finetune-4\weights\best.pt"

SEED_MODELS: list[dict] = [
    {
        "name": "helmet_v26", "version": "v26", "task": "安全帽检测",
        "weights_path": HELMET_WEIGHTS, "status": "active",
        "capability_desc": "工地安全帽佩戴检测：检出 helmet（佩戴）与 no_helmet（未佩戴）两类，适用于施工/工厂场景，imgsz 960。",
    },
    {
        "name": "wheelhub_v18", "version": "v18", "task": "轮毂缺陷检测",
        "weights_path": None, "status": "pending",
        "capability_desc": "轮毂表面缺陷检测：划痕/压痕/污渍，待训练产物接入。",
    },
    {
        "name": "fire_smoke_v12", "version": "v12", "task": "烟火检测",
        "weights_path": None, "status": "draft",
        "capability_desc": "火焰与烟雾检测，适用于消防监控场景，待训练产物接入。",
    },
]

SEED_USERS: list[dict] = [
    {"username": "admin", "role": "admin"},
    {"username": "operator", "role": "operator"},
    {"username": "viewer", "role": "viewer"},
]

DEFAULT_PASSWORD = "admin123"


def _capability_vec(text: str) -> list[float]:
    """能力描述 → 确定性 64 维向量（Phase 0 骨架；Phase 2 换 CLIP 向量化工厂）"""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [b / 255.0 for b in digest[:64]]


def seed_all(db: Session) -> bool:
    """注入种子数据；已存在任务则跳过（幂等）。返回是否执行了注入。"""
    if db.query(TaskType).count() > 0:
        return False

    # 任务 + 类别
    task_ids: dict[str, int] = {}
    for t in SEED_TASKS:
        task = TaskType(name=t["name"], task_desc=t["task_desc"], status="active")
        db.add(task)
        db.flush()
        task_ids[t["name"]] = task.id
        for cat_name in t["categories"]:
            db.add(Category(task_id=task.id, name=cat_name, aliases=[cat_name]))

    # 模型（挂任务）
    for m in SEED_MODELS:
        db.add(Model(
            name=m["name"], version=m["version"],
            task_id=task_ids[m["task"]],
            weights_path=m["weights_path"],
            capability_desc=m["capability_desc"],
            capability_vec=_capability_vec(m["capability_desc"]),
            status=m["status"],
        ))

    # 用户（bcrypt 哈希，统一走 security.hash_password）
    for u in SEED_USERS:
        db.add(User(username=u["username"], password_hash=hash_password(DEFAULT_PASSWORD), role=u["role"]))

    db.commit()
    return True


def seed_report(db: Session) -> str:
    """种子数据概览（启动日志用）"""
    tasks = db.query(TaskType).all()
    models = db.query(Model).all()
    users = db.query(User).all()
    return f"tasks={len(tasks)} models={len(models)} users={len(users)} (seeded={json.dumps([m.name for m in models])})"
