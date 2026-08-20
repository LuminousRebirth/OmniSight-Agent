"""模型生命周期 API schemas（§5.1 契约，Pydantic 响应模型）"""
from pydantic import BaseModel


class ModelCreate(BaseModel):
    """训练产物提交"""
    name: str
    version: str
    task_id: int
    weights_path: str | None = None
    capability_desc: str | None = None


class ModelOut(BaseModel):
    id: int
    name: str
    version: str
    task_id: int
    weights_path: str | None
    capability_desc: str | None
    status: str
    approved_by: str | None
    approved_at: str | None

    model_config = {"from_attributes": True}


class ApprovalRequest(BaseModel):
    """审批动作：submit|approve|reject|edit_desc"""
    action: str
    operator: str
    comment: str | None = None


class DescRequest(BaseModel):
    """更新能力描述（编辑后重新向量化）"""
    capability_desc: str
    operator: str = "system"  # 留痕用，默认 system


class ApprovalOut(BaseModel):
    id: int
    model_id: int
    action: str
    operator: str
    comment: str | None
    created_at: str

    model_config = {"from_attributes": True}
