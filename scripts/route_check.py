"""T7.6-1 自检：四级路由 API（helmet 命中路径 + 零样本兜底路径 + candidates）。

用法：conda activate omnisight && python scripts/route_check.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np


def main() -> None:
    from fastapi.testclient import TestClient
    from backend.app.main import app

    with TestClient(app) as c:
        # 1. 候选池
        r = c.get("/api/route/candidates")
        names = [x["model"] for x in r.json()]
        print(f"1. candidates -> {r.status_code} {names}")
        assert r.status_code == 200 and "helmet_v26" in names and "zero_shot" in names

        # 2. 纯色图 → 无命中 → 零样本兜底（zero_shot_used=True，恒有结果不抛错）
        _, buf = cv2.imencode(".jpg", np.full((100, 100, 3), 128, np.uint8))
        r = c.post("/api/route/image", files={"file": ("t.jpg", buf.tobytes(), "image/jpeg")},
                   data={"session_id": "s1", "user_text": "检测安全帽"})
        body = r.json()
        print(f"2. blank -> {r.status_code} model={body['model']} zero_shot={body['zero_shot_used']} steps={len(body['fallback_steps'])}")
        assert r.status_code == 200 and body["zero_shot_used"] is True
        assert any("候选池" in s for s in body["fallback_steps"])

        # 3. 推理轨迹回放（T7.9-1）
        tid = body["trace_id"]
        assert tid is not None
        tr = c.get(f"/api/agent/trace/{tid}")
        print(f"3. trace -> {tr.status_code} steps={len(tr.json()['steps'])} total_ms={tr.json()['total_ms']}")
        assert tr.status_code == 200 and len(tr.json()["steps"]) >= 2

    print("\n✅ T7.6-1 自检通过")


if __name__ == "__main__":
    main()
