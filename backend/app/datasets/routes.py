"""任务/数据集 API（Phase 0 最小版：GET /api/tasks 供验收；Phase 2 按 §5.4 完善）"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import Category, TaskType

router = APIRouter(prefix="/tasks", tags=["tasks"])


class CategoryOut(BaseModel):
    id: int
    name: str
    aliases: list

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
