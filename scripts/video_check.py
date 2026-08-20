"""T7.5-3 自检：视频流水线 + 异步任务 API（Stub 路径）。

用法：conda activate omnisight && python scripts/video_check.py
"""
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np

TMP = Path(__file__).resolve().parents[1] / "data" / "_test.mp4"


def main() -> None:
    # 生成 30 帧测试视频
    writer = cv2.VideoWriter(str(TMP), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 240))
    for _ in range(30):
        writer.write(np.full((240, 320, 3), 128, np.uint8))
    writer.release()

    # 1. 流水线（Stub 路径）
    from backend.app.detection.pipeline import process_video
    from backend.app.detection.stub import StubDetector
    res = process_video(str(TMP), StubDetector(), jump_n=3, confirm_m=2)
    assert res == []
    print("1. pipeline stub OK")

    # 2. API 异步视频任务
    from fastapi.testclient import TestClient
    from backend.app.main import app
    with TestClient(app) as c:
        with open(TMP, "rb") as f:
            r = c.post("/api/detect/video", files={"file": ("t.mp4", f.read(), "video/mp4")})
        assert r.status_code == 200
        tid = r.json()["task_id"]
        status = "queued"
        for _ in range(30):
            t = c.get(f"/api/detect/tasks/{tid}").json()
            status = t["status"]
            if status in ("completed", "failed"):
                break
            time.sleep(0.2)
        print(f"2. api video task -> {status}")
        assert status == "completed"

    TMP.unlink(missing_ok=True)
    print("\n✅ T7.5-3 自检通过")


if __name__ == "__main__":
    main()
