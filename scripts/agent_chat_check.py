"""Agent 对话 API 自检（纯文本 + 带图分析）。

用法：conda activate omnisight && python scripts/agent_chat_check.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np

from fastapi.testclient import TestClient
from backend.app.main import app


def main() -> None:
    with TestClient(app) as c:
        # 1. 纯文本对话
        r = c.post("/api/agent/chat", data={"text": "你好"})
        print(f"1. text chat -> {r.status_code} reply={r.json()['reply'][:40]}")
        assert r.status_code == 200 and "Agent" in r.json()["reply"]

        # 2. 带图对话（纯色图 → 检测空 + 规则兜底分析，链路完整）
        _, buf = cv2.imencode(".jpg", np.full((100, 100, 3), 128, np.uint8))
        r = c.post("/api/agent/chat", data={"text": "分析这张图"},
                   files={"file": ("t.jpg", buf.tobytes(), "image/jpeg")})
        body = r.json()
        print(f"2. image chat -> {r.status_code} reply_len={len(body['reply'])} dets={len(body['detections'])}")
        assert r.status_code == 200 and "分析结果" in body["reply"]

    print("\n✅ Agent 对话自检通过")


if __name__ == "__main__":
    main()
