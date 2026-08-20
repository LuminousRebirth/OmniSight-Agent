"""T7.3 自检：训练任务状态机 + 异步执行 + 产物进审批流。

用法：conda activate omnisight && python scripts/training_check.py
"""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from backend.app.main import app


def main() -> None:
    with TestClient(app) as c:
        # 1. 提交训练任务
        r = c.post("/api/training/jobs", json={
            "name": "包装缺陷训练", "dataset_version_id": 1,
            "hyperparams": {"epochs": 2},
        })
        print(f"1. create job -> {r.status_code} status={r.json().get('status')}")
        assert r.status_code == 201 and r.json()["status"] == "queued"
        job_id = r.json()["id"]

        # 2. 轮询至完成（占位模式秒级完成）
        status = "queued"
        for _ in range(20):
            r = c.get("/api/training/jobs")
            job = next((j for j in r.json() if j["id"] == job_id), None)
            if job:
                status = job["status"]
            if status in ("completed", "failed", "canceled"):
                break
            time.sleep(0.3)
        print(f"2. job status -> {status}")
        assert status == "completed"

        # 3. 指标回传
        r = c.get(f"/api/training/jobs/{job_id}/metrics")
        print(f"3. metrics -> {r.status_code} rows={len(r.json()['metrics'])}")
        assert r.status_code == 200 and len(r.json()["metrics"]) >= 1

        # 4. 产物自动进审批流（models 出现新 draft）
        r = c.get("/api/models")
        drafts = [m for m in r.json() if m["status"] == "draft"]
        print(f"4. models -> {r.status_code} drafts={len(drafts)}")
        assert r.status_code == 200 and len(drafts) >= 1

        # 5. 非法状态迁移（completed 后 stop → 409）
        r = c.post(f"/api/training/jobs/{job_id}/stop")
        print(f"5. stop completed job -> {r.status_code}")
        assert r.status_code == 409

    print("\n✅ T7.3 自检通过")


if __name__ == "__main__":
    main()
