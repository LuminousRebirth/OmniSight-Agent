"""数据库引擎与会话管理（SQLite 起步，可换 PostgreSQL）。

- 数据库文件：<项目根>/data/omnilight.db（data/ 已 gitignore）
- 对外提供：engine / SessionLocal / init_db() / get_db()（FastAPI 依赖注入）
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

# 项目根 = backend/app/core/ 向上 3 级
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "omnilight.db"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},  # FastAPI 多线程访问 SQLite
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """创建全部表（幂等：已存在则跳过）"""
    Base.metadata.create_all(engine)


def get_db():
    """FastAPI 依赖：每请求一个会话，用后关闭"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
