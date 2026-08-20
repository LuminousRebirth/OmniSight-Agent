"""FastAPI 依赖：当前用户解析 + 角色校验（T0-7，供全模块复用）。

用法：
    @router.post("/xxx")
    def op(user: User = Depends(require_roles("admin"))): ...
"""
from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.models import User
from ..core.security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    """从 Authorization: Bearer <token> 解析当前用户；无效抛 401"""
    if cred is None:
        raise HTTPException(401, "未认证")
    try:
        payload = decode_token(cred.credentials)
    except Exception:
        raise HTTPException(401, "token 无效或已过期")
    user = db.query(User).filter(User.username == payload["sub"]).first()
    if user is None:
        raise HTTPException(401, "用户不存在")
    return user


def require_roles(*roles: str):
    """角色门禁：不在允许角色内抛 403（写操作鉴权用）"""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, f"越权：需要角色 {'/'.join(roles)}")
        return user
    return checker
