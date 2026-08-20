"""检测器插件基类 + 统一输出结构（§3.4 契约）"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Detection:
    """检测输出统一结构，所有检测器必须返回此结构"""
    bbox: tuple[float, float, float, float]   # x1,y1,x2,y2（像素坐标）
    confidence: float
    class_name: str
    track_id: int | None = None
    metadata: dict = field(default_factory=dict)  # 含 detector_type: yolo|zero_shot|stub


class BaseDetector(ABC):
    """检测器插件基类：加载、推理、卸载"""

    detector_type: str = "base"

    @abstractmethod
    def load_model(self) -> None:
        """加载模型（首次调用时懒加载）"""

    @abstractmethod
    def detect(self, image: np.ndarray) -> list[Detection]:
        """对单帧图像推理，返回 Detection 列表"""

    def unload(self) -> None:
        """释放显存（默认空实现）"""
