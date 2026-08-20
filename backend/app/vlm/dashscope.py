"""通义千问 VL Provider（DashScope 兼容模式 = OpenAI 接口，§7.7）"""
from __future__ import annotations

from ..core.config import settings
from .openai_compat import OpenAICompatProvider


class DashScopeProvider(OpenAICompatProvider):
    """DashScope 通义千问 VL（复用 OpenAI 兼容调用，仅换 base_url/model）"""

    def __init__(self):
        super().__init__(
            api_key=settings.dashscope_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-vl-max",
        )
