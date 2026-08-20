"""模型审批状态机 + 注册表查询（§7.4 骨架，T7.4-1）。

状态机：draft --submit--> pending --approve--> active
                              --reject--> rejected
非法迁移抛 StateError（上层转 409）；全程写 approvals 留痕。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..core.models import Approval, Model, now_utc
from ..core.seed import _capability_vec


class StateError(Exception):
    """状态机非法迁移"""


# 动作 -> {当前状态: 目标状态}
TRANSITIONS: dict[str, dict[str, str]] = {
    "submit": {"draft": "pending"},
    "approve": {"pending": "active"},
    "reject": {"pending": "rejected"},
}


def apply_approval(
    db: Session, model: Model, action: str, operator: str, comment: str | None
) -> Model:
    """执行审批动作；非法迁移抛 StateError"""
    if action in TRANSITIONS:
        mapping = TRANSITIONS[action]
        if model.status not in mapping:
            raise StateError(f"非法迁移: {model.status} --{action}--> ?")
        model.status = mapping[model.status]
        if action == "approve":
            model.approved_by = operator
            model.approved_at = now_utc()
    elif action == "edit_desc":
        pass  # 描述编辑走 /desc 端点（不改变状态）
    else:
        raise StateError(f"未知动作: {action}")

    db.add(Approval(model_id=model.id, action=action, operator=operator, comment=comment))
    db.commit()
    db.refresh(model)
    return model


def update_desc(db: Session, model: Model, capability_desc: str, operator: str = "system") -> Model:
    """更新能力描述并重新向量化（路由质量源头）；写 edit_desc 审批流水留痕"""
    model.capability_desc = capability_desc
    model.capability_vec = _capability_vec(capability_desc)
    db.add(Approval(model_id=model.id, action="edit_desc", operator=operator, comment=None))
    db.commit()
    db.refresh(model)
    return model
