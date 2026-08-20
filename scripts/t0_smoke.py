"""Phase 0 冒烟脚本：启动应用（建表+种子）并验证核心 API 与审批状态机。

用法：conda activate omnisight && python scripts/t0_smoke.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows GBK 控制台兼容
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from backend.app.main import app


def main() -> None:
    with TestClient(app) as c:
        models = c.get("/api/models")
        assert models.status_code == 200
        names = [m["name"] for m in models.json()]
        print(f"GET /api/models -> {models.status_code} {names}")
        assert names == ["helmet_v26", "wheelhub_v18", "fire_smoke_v12"]

        active = c.get("/api/models/active")
        active_names = [m["name"] for m in active.json()]
        print(f"GET /api/models/active -> {active.status_code} {active_names}")
        assert active_names == ["helmet_v26"]

        tasks = c.get("/api/tasks")
        task_names = [t["name"] for t in tasks.json()]
        print(f"GET /api/tasks -> {tasks.status_code} {task_names}")
        assert task_names == ["安全帽检测", "轮毂缺陷检测", "烟火检测"]

        health = c.get("/api/health")
        print(f"GET /api/health -> {health.status_code} {health.json()}")

        # 状态机：active 模型 submit 必须 409
        helmet = models.json()[0]
        r = c.post(f"/api/models/{helmet['id']}/approval",
                   json={"action": "submit", "operator": "admin"})
        print(f"active--submit(应409) -> {r.status_code} {r.json().get('detail')}")
        assert r.status_code == 409

        # pending 模型 reject → rejected
        wheelhub = [m for m in models.json() if m["name"] == "wheelhub_v18"][0]
        r2 = c.post(f"/api/models/{wheelhub['id']}/approval",
                    json={"action": "reject", "operator": "admin", "comment": "测试驳回"})
        print(f"pending--reject -> {r2.status_code} {r2.json()['status']}")
        assert r2.status_code == 200 and r2.json()["status"] == "rejected"

        # 编辑能力描述（重新向量化）
        r3 = c.post(f"/api/models/{wheelhub['id']}/desc",
                    json={"capability_desc": "轮毂表面缺陷检测 v2 描述"})
        print(f"edit desc -> {r3.status_code} {r3.json()['capability_desc'][:16]}")
        assert r3.status_code == 200

        # 审批流水留痕
        ap = c.get(f"/api/models/{wheelhub['id']}/approvals")
        print(f"approvals -> {ap.status_code} count={len(ap.json())}")
        assert ap.status_code == 200 and len(ap.json()) >= 2

        # ── 鉴权框架（T0-7）──
        bad = c.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        print(f"login wrong pwd -> {bad.status_code}")
        assert bad.status_code == 401

        login = c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        print(f"login admin -> {login.status_code} role={login.json()['role']}")
        assert login.status_code == 200 and login.json()["role"] == "admin"
        token = login.json()["access_token"]

        no_token = c.post("/api/models", json={"name": "x", "version": "1", "task_id": 1})
        print(f"create model no token(应401) -> {no_token.status_code}")
        assert no_token.status_code == 401

        with_token = c.post("/api/models", json={"name": "test_m", "version": "1", "task_id": 1},
                            headers={"Authorization": f"Bearer {token}"})
        print(f"create model with admin token -> {with_token.status_code}")
        assert with_token.status_code == 201

        # 清理测试模型（保持种子数据纯净）
        from backend.app.core.database import SessionLocal
        from backend.app.core.models import Model
        _db = SessionLocal()
        _db.query(Model).filter(Model.name == "test_m").delete()
        _db.commit()
        _db.close()
        print("cleaned test_m")

    print("\n✅ Phase 0 冒烟全部通过")


if __name__ == "__main__":
    main()
