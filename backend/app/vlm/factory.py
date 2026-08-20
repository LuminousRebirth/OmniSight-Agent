"""VLM Provider 工厂：按配置构造 + 逐级降级（§7.7 双通道设计）"""
from __future__ import annotations

from ..core.config import settings
from .dashscope import DashScopeProvider
from .local import LocalQwenVLProvider
from .openai_compat import OpenAICompatProvider
from .provider import FusedResult, ProviderUnavailable, VLMProvider

PROVIDERS: dict[str, type[VLMProvider]] = {
    "dashscope": DashScopeProvider,
    "openai": OpenAICompatProvider,
    "local": LocalQwenVLProvider,
}


class RuleFallback(VLMProvider):
    """无可用 Provider 的规则兜底（不抛错，提示配置）"""

    def analyze(self, image: bytes, prompt: str) -> FusedResult:
        return FusedResult(
            detections=[], severity="medium",
            description="未配置可用的 VLM Provider（请配置 OMNI_DASHSCOPE_API_KEY 或 OMNI_OPENAI_API_KEY）",
            action="人工复核",
        )


def get_provider() -> VLMProvider:
    """按 vlm_default + vlm_fallback 顺序构造；不可用逐级降级；全失败返回规则兜底"""
    order = [settings.vlm_default, *settings.vlm_fallback.split(",")]
    for name in order:
        cls = PROVIDERS.get(name.strip())
        if cls is None:
            continue
        try:
            return cls()
        except ProviderUnavailable:
            continue
    return RuleFallback()
