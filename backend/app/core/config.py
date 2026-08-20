"""全局配置（pydantic-settings + .env，项目根 .env 文件）。

前缀 OMNI_：环境变量 OMNI_SECRET_KEY 等可覆盖默认值。
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # 安全
    secret_key: str = "omnisight-dev-secret-change-me"
    token_expire_minutes: int = 720  # 12h

    # VLM Provider（Phase 2）：默认 + 降级顺序
    vlm_default: str = "dashscope"
    vlm_fallback: str = "local"
    dashscope_api_key: str = ""  # 通义千问 VL（.env: OMNI_DASHSCOPE_API_KEY）
    openai_api_key: str = ""     # GPT-4o / 兼容中转（.env: OMNI_OPENAI_API_KEY）
    openai_base_url: str = "https://api.openai.com/v1"

    # 存储
    data_dir: str = str(PROJECT_ROOT / "data")

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "env_prefix": "OMNI_"}


settings = Settings()
