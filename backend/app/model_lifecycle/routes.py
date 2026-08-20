"""模型生命周期 API（§5.1：/api/models*）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.deps import require_roles
from ..core.models import Approval, Model, User
from . import schemas, service

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[schemas.ModelOut])
def list_models(db: Session = Depends(get_db)):
    """全部模型"""
    return db.query(Model).order_by(Model.id).all()


@router.get("/active", response_model=list[schemas.ModelOut])
def list_active(db: Session = Depends(get_db)):
    """仅 ACTIVE（路由候选池）"""
    return db.query(Model).filter(Model.status == "active").all()


@router.post("", response_model=schemas.ModelOut, status_code=201)
def create_model(
    payload: schemas.ModelCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("admin")),  # 写操作鉴权（R8）
):
    """训练产物提交 → draft（需 admin）"""
    model = Model(**payload.model_dump(), status="draft")
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/{model_id}/approvals", response_model=list[schemas.ApprovalOut])
def list_approvals(model_id: int, db: Session = Depends(get_db)):
    """审批流水"""
    if db.get(Model, model_id) is None:
        raise HTTPException(404, "模型不存在")
    return db.query(Approval).filter(Approval.model_id == model_id).order_by(Approval.id).all()


@router.post("/{model_id}/approval", response_model=schemas.ModelOut)
def approve_model(model_id: int, payload: schemas.ApprovalRequest, db: Session = Depends(get_db)):
    """审批动作：submit/approve/reject/edit_desc（非法迁移 409）"""
    model = db.get(Model, model_id)
    if model is None:
        raise HTTPException(404, "模型不存在")
    try:
        return service.apply_approval(db, model, payload.action, payload.operator, payload.comment)
    except service.StateError as exc:
        raise HTTPException(409, str(exc))


@router.post("/{model_id}/desc", response_model=schemas.ModelOut)
def edit_desc(model_id: int, payload: schemas.DescRequest, db: Session = Depends(get_db)):
    """更新能力描述并重新向量化（写 edit_desc 流水留痕）"""
    model = db.get(Model, model_id)
    if model is None:
        raise HTTPException(404, "模型不存在")
    return service.update_desc(db, model, payload.capability_desc, payload.operator)
