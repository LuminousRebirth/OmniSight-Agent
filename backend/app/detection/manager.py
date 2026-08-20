"""DetectorManager：注册中心 + 懒加载 + 兜底降级（§7.5）"""
from __future__ import annotations

from .base import BaseDetector
from .stub import StubDetector
from .ultralytics_det import UltralyticsDetector


class DetectorManager:
    """检测器注册中心（懒加载；权重缺失/加载失败回退 StubDetector，永不抛错）"""

    def __init__(self) -> None:
        self._detectors: dict[str, BaseDetector] = {}

    def get(self, model_id: str, weights: str | None = None, imgsz: int = 960) -> BaseDetector:
        if model_id in self._detectors:
            return self._detectors[model_id]

        detector: BaseDetector = UltralyticsDetector(weights, imgsz) if weights else StubDetector()
        try:
            detector.load_model()
        except Exception:
            detector = StubDetector()  # 权重加载失败 → 兜底
        self._detectors[model_id] = detector
        return detector

    def unload(self, model_id: str) -> None:
        detector = self._detectors.pop(model_id, None)
        if detector is not None:
            detector.unload()


manager = DetectorManager()
