"""摄像头管理：本机设备枚举 + 连接测试（§7.5）"""
from __future__ import annotations

import cv2


def enumerate_cameras() -> list[dict]:
    """DirectShow 枚举本机摄像头索引（含 OBS 虚拟摄像头）"""
    devices: list[dict] = []
    for index in range(8):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            name = cap.getBackendName() or f"Camera {index}"
            devices.append({"index": index, "name": name, "is_obs": "OBS" in name})
        cap.release()
    return devices


def test_camera(source_type: str, uri: str) -> dict:
    """测试采集源：返回 ok / resolution / fps / error"""
    from .camera_source import LocalCameraSource, NetworkCameraSource

    source = LocalCameraSource(int(uri)) if source_type == "usb" else NetworkCameraSource(uri)
    if not source.open():
        return {"ok": False, "error": "无法打开采集源"}
    frame = source.read_frame()
    if frame is None:
        source.release()
        return {"ok": False, "error": "无法读取帧"}
    h, w = frame.shape[:2]
    source.release()
    return {"ok": True, "resolution": f"{w}x{h}", "fps": 0}
