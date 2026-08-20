"""真 YOLO26 检测器：基于 ultralytics 权重推理（.pt/.onnx）"""
from __future__ import annotations

import numpy as np

from .base import BaseDetector, Detection


class UltralyticsDetector(BaseDetector):
    """加载 ultralytics 权重（YOLO26）执行检测；类别名取自权重自带 names"""

    detector_type = "yolo"

    def __init__(self, weights: str, imgsz: int = 960, conf: float = 0.25):
        self.weights = weights
        self.imgsz = imgsz
        self.conf = conf
        self.model = None

    def load_model(self) -> None:
        from ultralytics import YOLO  # 延迟导入：未安装 ultralytics 时避免模块加载失败
        self.model = YOLO(self.weights)

    def detect(self, image: np.ndarray) -> list[Detection]:
        if self.model is None:
            self.load_model()
        result = self.model.predict(image, imgsz=self.imgsz, conf=self.conf, verbose=False)[0]
        return [
            Detection(
                bbox=tuple(float(v) for v in box.xyxy[0].tolist()),
                confidence=float(box.conf[0]),
                class_name=self.model.names[int(box.cls[0])],
                metadata={"detector_type": "yolo"},
            )
            for box in result.boxes
        ]
