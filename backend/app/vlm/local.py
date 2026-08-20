"""本地 Qwen2.5-VL Provider（可选装，§7.7 双通道本地侧）"""
from __future__ import annotations

from .provider import FusedResult, ProviderUnavailable, VLMProvider


class LocalQwenVLProvider(VLMProvider):
    """本地多模态模型；依赖未安装时抛 ProviderUnavailable 触发降级"""

    def __init__(self):
        try:
            import qwen_vl  # noqa: F401  本地 VLM 推理后端（可后装）
        except ImportError:
            raise ProviderUnavailable("本地 Qwen2.5-VL 未安装（pip install qwen-vl 后启用）")

    def analyze(self, image: bytes, prompt: str) -> FusedResult:
        raise ProviderUnavailable("本地 VLM 推理尚未实现（配置 API Key 走云端）")
