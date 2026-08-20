"""Phase 2 基础自检（T7.1）：任务开放化 + 数据集 CRUD。

用法：conda activate omnisight && python scripts/phase2_check.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from backend.app.main import app


def main() -> None:
    with TestClient(app) as c:
        # 1. 创建任务（§6 Phase 2 验收命令）
        r = c.post("/api/tasks", json={
            "name": "包装缺陷", "task_desc": "识别包装破损/污渍/压痕",
            "categories": [{"name": "broken"}, {"name": "stain"}, {"name": "dent"}],
        })
        print(f"1. create task -> {r.status_code} {r.json()['name']} "
              f"cats={[x['name'] for x in r.json()['categories']]}")
        assert r.status_code == 201 and len(r.json()["categories"]) == 3
        task_id = r.json()["id"]

        # 2. 重名任务 409
        r2 = c.post("/api/tasks", json={"name": "包装缺陷", "task_desc": "x"})
        print(f"2. dup task -> {r2.status_code}")
        assert r2.status_code == 409

        # 3. 数据集创建 + 列表
        r3 = c.post("/api/datasets", json={"name": "包装v1", "task_id": task_id})
        print(f"3. create dataset -> {r3.status_code} status={r3.json()['status']}")
        assert r3.status_code == 201
        ds_id = r3.json()["id"]

        r4 = c.get("/api/datasets")
        print(f"4. list datasets -> {r4.status_code} count={len(r4.json())}")
        assert r4.status_code == 200 and len(r4.json()) >= 1

        # 5. 素材分页（空）
        r5 = c.get(f"/api/datasets/{ds_id}/items")
        print(f"5. items -> {r5.status_code} total={r5.json()['total']}")
        assert r5.status_code == 200 and r5.json()["total"] == 0

    print("\n✅ T7.1-1 自检通过")


if __name__ == "__main__":
    main()
