"""OpenAI 兼容 VLM Provider（GPT-4o / 任意 OpenAI 兼容中转，§7.7）"""
from __future__ import annotations

import base64
import json

import httpx

from ..core.config import settings
from .provider import FusedResult, ProviderUnavailable, VLMProvider


def parse_fused(content: str) -> FusedResult:
    """解析 VLM 输出 JSON（容忍 markdown 代码块包裹）；解析失败降级默认值"""
    try:
        text = content.strip()
        if "```" in text:
            text = text.split("```")[1].lstrip("json").strip()
        data = json.loads(text)
        return FusedResult(
            detections=[], severity=data.get("severity", "medium"),
            description=data.get("description", ""), action=data.get("action", ""),
        )
    except Exception:
        return FusedResult(detections=[], severity="medium",
                           description=content[:200], action="")


class OpenAICompatProvider(VLMProvider):
    """OpenAI 兼容 chat/completions 接口（图片 base64 + 文本）"""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        self.model = model or "gpt-4o"
        if not self.api_key:
            raise ProviderUnavailable("缺少 OpenAI API Key")

    def analyze(self, image: bytes, prompt: str) -> FusedResult:
        b64 = base64.b64encode(image).decode()
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": prompt},
            ]}]},
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return parse_fused(content)
