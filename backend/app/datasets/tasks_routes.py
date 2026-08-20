"""任务/数据集 API（§5.4 Phase 2：任务开放化 + 数据集管理）"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import Category, Dataset, TaskType

router = APIRouter(prefix="/tasks", tags=["tasks"])


class CategoryCreate(BaseModel):
    name: str
    aliases: list[str] = []
    description: str | None = None


class TaskCreate(BaseModel):
    name: str
    task_desc: str
    categories: list[CategoryCreate] = []


class CategoryOut(BaseModel):
    id: int
    name: str
    aliases: list
    description: str | None

    model_config = {"from_attributes": True}


class TaskOut(BaseModel):
    id: int
    name: str
    task_desc: str
    status: str
    categories: list[CategoryOut] = []

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    """任务列表（含类别）"""
    tasks = db.query(TaskType).order_by(TaskType.id).all()
    for t in tasks:
        t.categories = db.query(Category).filter(Category.task_id == t.id).all()
    return tasks


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """创建任务（自由开放，无枚举上限）+ 类别"""
    if db.query(TaskType).filter(TaskType.name == payload.name).first():
        raise HTTPException(409, "任务已存在")
    task = TaskType(name=payload.name, task_desc=payload.task_desc, status="active")
    db.add(task)
    db.flush()
    for c in payload.categories:
        db.add(Category(task_id=task.id, name=c.name, aliases=c.aliases, description=c.description))
    db.commit()
    db.refresh(task)
    task.categories = db.query(Category).filter(Category.task_id == task.id).all()
    return task
