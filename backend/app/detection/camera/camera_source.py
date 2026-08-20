"""采集源抽象：open/read_frame/release（§7.5）"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class CameraSource(ABC):
    """采集源统一接口"""

    @abstractmethod
    def open(self) -> bool:
        """打开采集源，返回是否成功"""

    @abstractmethod
    def read_frame(self) -> np.ndarray | None:
        """读取一帧（BGR）；失败/断开返回 None"""

    @abstractmethod
    def release(self) -> None:
        """释放采集源"""


class LocalCameraSource(CameraSource):
    """本机摄像头（Windows DirectShow，CAP_DSHOW 失败降级 CAP_ANY）"""

    def __init__(self, index: int = 0):
        self.index = index
        self.cap = None

    def open(self) -> bool:
        import cv2
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.index, cv2.CAP_ANY)  # 驱动兼容降级
        return bool(self.cap.isOpened())

    def read_frame(self) -> np.ndarray | None:
        if self.cap is None:
            return None
        ok, frame = self.cap.read()
        return frame if ok else None

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None


class NetworkCameraSource(CameraSource):
    """网络流（RTSP/RTMP）：断流指数退避重连（1s→2s→…→30s）"""

    def __init__(self, uri: str):
        self.uri = uri
        self.cap = None
        self._backoff = 1.0

    def open(self) -> bool:
        import cv2
        self.cap = cv2.VideoCapture(self.uri)
        if self.cap.isOpened():
            self._backoff = 1.0
        return bool(self.cap.isOpened())

    def read_frame(self) -> np.ndarray | None:
        if self.cap is None or not self.cap.isOpened():
            self._reconnect()
            return None
        ok, frame = self.cap.read()
        if not ok:
            self.release()
            self._reconnect()
            return None
        return frame

    def _reconnect(self) -> None:
        import time
        time.sleep(self._backoff)
        self._backoff = min(self._backoff * 2, 30.0)
        self.open()

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None
