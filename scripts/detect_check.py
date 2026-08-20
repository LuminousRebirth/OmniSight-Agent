"""T7.5-1 自检：Stub 兜底 + YOLO26 真推理（helmet best.pt）+ detect API。

用法：conda activate omnisight && python scripts/detect_check.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np

HELMET_WEIGHTS = r"E:\python_code\yolo\runs\models\ppe\HHW_noperson\finetune-4\weights\best.pt"


def main() -> None:
    from backend.app.detection.manager import manager

    # 1. Stub 兜底：无权重路径不抛错
    stub = manager.get("no-weights")
    assert stub.detector_type == "stub"
    assert stub.detect(np.zeros((100, 100, 3), np.uint8)) == []
    print("1. stub fallback OK")

    # 2. YOLO26 真权重加载与推理（纯色图，大概率无目标，验证链路可用）
    yolo = manager.get("helmet_v26", HELMET_WEIGHTS)
    assert yolo.detector_type == "yolo"
    res = yolo.detect(np.full((960, 1280, 3), 128, np.uint8))
    print(f"2. yolo26 load+infer OK (detections on blank: {len(res)})")

    # 3. detect API（默认 ACTIVE 模型 = helmet_v26）
    from fastapi.testclient import TestClient
    from backend.app.main import app

    _, buf = cv2.imencode(".jpg", np.full((100, 100, 3), 200, np.uint8))
    with TestClient(app) as c:
        r = c.post("/api/detect/image", files={"file": ("t.jpg", buf.tobytes(), "image/jpeg")})
        body = r.json()
        print(f"3. api /detect/image -> {r.status_code} model={body['model']} stub={body['stub']} dets={len(body['detections'])}")
        assert r.status_code == 200 and body["model"] == "helmet_v26"

    print("\n✅ T7.5-1 自检通过")


if __name__ == "__main__":
    main()
