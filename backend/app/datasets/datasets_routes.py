"""数据集 API（§5.4 Phase 2：创建/素材分页；上传抽帧见 upload 模块）"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import Dataset, ImageItem

router = APIRouter(prefix="/datasets", tags=["datasets"])


class DatasetCreate(BaseModel):
    name: str
    task_id: int


class DatasetOut(BaseModel):
    id: int
    name: str
    task_id: int
    version: str | None
    status: str

    model_config = {"from_attributes": True}


@router.post("", response_model=DatasetOut, status_code=201)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
    """创建数据集（草稿）"""
    ds = Dataset(name=payload.name, task_id=payload.task_id, status="draft")
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


@router.get("", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    """数据集列表"""
    return db.query(Dataset).order_by(Dataset.id.desc()).all()


@router.get("/{dataset_id}/items")
def list_items(dataset_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
               db: Session = Depends(get_db)):
    """分页素材列表"""
    if db.get(Dataset, dataset_id) is None:
        raise HTTPException(404, "数据集不存在")
    items = (db.query(ImageItem).filter(ImageItem.dataset_id == dataset_id)
             .offset((page - 1) * size).limit(size).all())
    total = db.query(ImageItem).filter(ImageItem.dataset_id == dataset_id).count()
    return {"page": page, "size": size, "total": total,
            "items": [{"id": i.id, "storage_path": i.storage_path,
                       "width": i.width, "height": i.height} for i in items]}
