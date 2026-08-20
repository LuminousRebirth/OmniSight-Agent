"""视频流水线：抽帧 → 跳帧检测 → IoU 跟踪 → 时序过滤（§7.5）。

跳帧（每 jump_n 帧检测一次）省算力；连续 confirm_m 帧命中同一目标才确认，
防止单帧误报；跟踪用 IoU 匹配（简化版，Phase 2 可换 ByteTrack）。
"""
from __future__ import annotations

import cv2
import numpy as np

from .base import BaseDetector, Detection


def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    """两个 bbox 的 IoU"""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union > 0 else 0.0


class _Track:
    """简易跟踪目标：IoU 匹配 + 连续命中计数（hits 单调递增，==confirm_m 只触发一次输出）"""

    def __init__(self, det: Detection):
        self.det = det
        self.hits = 1  # 首次出现计 1 次命中

    def update(self, det: Detection) -> None:
        self.det = det
        self.hits += 1


def process_video(path: str, detector: BaseDetector,
                  jump_n: int = 3, confirm_m: int = 2,
                  iou_thr: float = 0.5) -> list[dict]:
    """处理视频，返回时序确认的检测帧 [{frame_no, detections: [Detection]}]"""
    cap = cv2.VideoCapture(path)
    tracks: list[_Track] = []
    results: list[dict] = []
    frame_no = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_no % jump_n == 0:
            dets = detector.detect(frame)
            # IoU 匹配现有 track；未匹配的建新 track
            unmatched = list(dets)
            for t in tracks:
                best = max(unmatched, key=lambda d: _iou(t.det.bbox, d.bbox), default=None)
                if best is not None and _iou(t.det.bbox, best.bbox) >= iou_thr:
                    t.update(best)
                    unmatched.remove(best)
            tracks.extend(_Track(d) for d in unmatched)
            # 达到确认阈值的 track 输出一次
            confirmed = [t.det for t in tracks if t.hits == confirm_m]
            if confirmed:
                results.append({"frame_no": frame_no, "detections": confirmed})
        frame_no += 1

    cap.release()
    return results
