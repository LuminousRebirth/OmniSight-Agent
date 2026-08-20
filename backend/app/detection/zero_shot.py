"""零样本检测器：YOLO-World 按文本提示词检测任意类别（未训练类别兜底，§7.5）"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .base import BaseDetector, Detection

DEFAULT_WEIGHTS = str(Path(__file__).resolve().parents[3] / "data" / "yolov8s-world.pt")


class ZeroShotDetector(BaseDetector):
    """YOLO-World 提示词检测；权重缺失时降级为空结果（不抛错）"""

    detector_type = "zero_shot"

    def __init__(self, weights: str = DEFAULT_WEIGHTS, prompt: list[str] | None = None,
                 conf: float = 0.25):
        self.weights = weights
        self.prompt = prompt or []
        self.conf = conf
        self.model = None

    def load_model(self) -> None:
        from ultralytics import YOLO  # 延迟导入
        self.model = YOLO(self.weights)
        if self.prompt:
            self.model.set_classes(self.prompt)

    def detect(self, image: np.ndarray) -> list[Detection]:
        if self.model is None:
            self.load_model()
        result = self.model.predict(image, conf=self.conf, verbose=False)[0]
        return [
            Detection(
                bbox=tuple(float(v) for v in box.xyxy[0].tolist()),
                confidence=float(box.conf[0]),
                class_name=self.model.names[int(box.cls[0])],
                metadata={"detector_type": "zero_shot"},
            )
            for box in result.boxes
        ]
