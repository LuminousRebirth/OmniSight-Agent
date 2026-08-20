"""T7.7 自检：VLM Provider 降级链 + prompt 模板 + 分析 API。

用法：conda activate omnisight && python scripts/vlm_check.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np


def main() -> None:
    # 1. Provider 降级链（无 API key → RuleFallback 不抛错）
    from backend.app.vlm.factory import get_provider
    from backend.app.vlm.provider import FusedResult
    p = get_provider()
    fused = p.analyze(b"", "test")
    print(f"1. provider fallback -> {type(p).__name__} severity={fused.severity}")
    assert isinstance(fused, FusedResult)

    # 2. prompt 模板
    from backend.app.vlm.templates import build_prompt
    prompt = build_prompt("安全帽检测", ["no_helmet"], "GB 规范：必须佩戴")
    print(f"2. prompt -> {'JSON' in prompt and '安全帽' in prompt}")
    assert "JSON" in prompt and "安全帽" in prompt

    # 3. VLM 输出解析（容忍 markdown 包裹）
    from backend.app.vlm.openai_compat import parse_fused
    r = parse_fused('```json\n{"severity":"high","description":"未戴安全帽","action":"立即整改"}\n```')
    print(f"3. parse_fused -> {r.severity}/{r.action}")
    assert r.severity == "high" and r.action == "立即整改"

    # 4. 分析 API 全链路（纯色图 → 规则兜底 200）
    from fastapi.testclient import TestClient
    from backend.app.main import app
    _, buf = cv2.imencode(".jpg", np.full((100, 100, 3), 128, np.uint8))
    with TestClient(app) as c:
        r = c.post("/api/analysis/image", files={"file": ("t.jpg", buf.tobytes(), "image/jpeg")},
                   data={"user_text": "检测安全帽"})
        body = r.json()
        print(f"4. analysis api -> {r.status_code} severity={body['severity']} dets={len(body['detections'])}")
        assert r.status_code == 200 and body["severity"] in ("low", "medium", "high")

        r2 = c.get("/api/analysis/providers")
        print(f"5. providers -> {r2.status_code} {r2.json()['available']}")
        assert r2.status_code == 200 and "dashscope" in r2.json()["available"]

    print("\n✅ T7.7 自检通过")


if __name__ == "__main__":
    main()
