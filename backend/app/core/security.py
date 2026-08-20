"""鉴权工具（T0-7）：JWT 签发/校验 + bcrypt 密码哈希。

直接使用 bcrypt 库（passlib 与 bcrypt 4.x 不兼容，见 IMPLEMENTATION_NOTES）。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings


def hash_password(password: str) -> str:
    """bcrypt 哈希"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """校验密码"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(username: str, role: str) -> str:
    """签发 JWT（sub=用户名, role=角色）"""
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    """校验并解析 JWT（无效/过期抛 jwt 异常）"""
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
