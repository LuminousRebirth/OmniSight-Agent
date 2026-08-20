"""VLM Provider 抽象 + 统一输出（§3.4 FusedResult）+ 降级异常"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..detection.base import Detection


class ProviderUnavailable(Exception):
    """Provider 不可用（无密钥/断连），factory 据此降级下一个"""


@dataclass
class FusedResult:
    """VLM 融合结果（YOLO 框 + VLM 语义，references 强制携带依据防幻觉）"""
    detections: list[Detection]
    severity: str                    # low|medium|high
    description: str
    action: str
    references: list[str] = field(default_factory=list)


class VLMProvider(ABC):
    """多模态分析抽象：输入图 + 提示词，输出结构化结论"""

    @abstractmethod
    def analyze(self, image: bytes, prompt: str) -> FusedResult:
        """对单张图片（bytes，jpg/png）执行语义分析"""
