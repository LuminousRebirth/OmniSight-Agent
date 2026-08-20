"""T7.5-4 自检：摄像头枚举/CRUD/测试 + live 降级路径（无真实设备时验证错误处理）。

用法：conda activate omnisight && python scripts/camera_check.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    from fastapi.testclient import TestClient
    from backend.app.main import app

    with TestClient(app) as c:
        # 1. 本机设备枚举（无设备时返回空列表，不抛错）
        r = c.get("/api/cameras/enumerate")
        print(f"1. enumerate -> {r.status_code} devices={len(r.json())}")
        assert r.status_code == 200

        # 2. 摄像头源 CRUD
        r = c.post("/api/cameras", json={"name": "测试USB", "source_type": "usb", "uri": "0"})
        print(f"2. create camera -> {r.status_code} id={r.json().get('id')}")
        assert r.status_code == 201
        cam_id = r.json()["id"]

        r = c.get("/api/cameras")
        print(f"3. list cameras -> {r.status_code} count={len(r.json())}")
        assert r.status_code == 200 and len(r.json()) == 1

        # 4. 连接测试（无真实设备 → ok=false 但 200）
        r = c.post(f"/api/cameras/{cam_id}/test")
        print(f"4. test camera -> {r.status_code} {r.json()}")
        assert r.status_code == 200 and r.json()["ok"] is False

        # 5. live start 无设备 → 400（错误处理正确）
        r = c.post("/api/detect/live/start", json={"camera_id": cam_id})
        print(f"5. live start (no device) -> {r.status_code}")
        assert r.status_code == 400

        # 6. 不存在的流 stop/ws → 404/关闭
        r = c.post("/api/detect/live/nonexist/stop")
        print(f"6. stop nonexist -> {r.status_code}")
        assert r.status_code == 404

    print("\n✅ T7.5-4 自检通过")


if __name__ == "__main__":
    main()
