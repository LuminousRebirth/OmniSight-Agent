"""兜底检测器：权重缺失或加载失败时使用，返回空结果保证链路不中断"""
from __future__ import annotations

import numpy as np

from .base import BaseDetector, Detection


class StubDetector(BaseDetector):
    """输出空检测（无 Detection），调用方据此感知 stub 模式"""

    detector_type = "stub"

    def load_model(self) -> None:
        pass

    def detect(self, image: np.ndarray) -> list[Detection]:
        return []
