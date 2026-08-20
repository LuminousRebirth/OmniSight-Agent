"""T7.8 自检：RAG 入库/检索/待确认转正（Milvus Lite + DB 双写）。

用法：conda activate omnisight && python scripts/rag_check.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    from fastapi.testclient import TestClient
    from backend.app.main import app

    with TestClient(app) as c:
        # 1. 知识入库（规范文档）
        r = c.post("/api/rag/knowledge", json={
            "doc_type": "regulation", "title": "高处作业安全规范",
            "content": "高处作业必须佩戴安全帽 系挂安全带 严禁抛掷工具 作业前检查脚手架",
        })
        print(f"1. ingest -> {r.status_code} id={r.json().get('id')}")
        assert r.status_code == 201
        doc_id = r.json()["id"]

        # 2. 混合检索（命中安全帽相关）
        r = c.post("/api/rag/search", json={"query_text": "高处作业 安全帽", "top_k": 3})
        print(f"2. search -> {r.status_code} hits={len(r.json()['results'])}")
        assert r.status_code == 200 and len(r.json()["results"]) >= 1
        assert "安全帽" in r.json()["results"][0]["content"]

        # 3. 删除（含向量）
        r = c.delete(f"/api/rag/knowledge/{doc_id}")
        print(f"3. delete -> {r.status_code} {r.json()}")
        assert r.status_code == 200

        # 4. 待确认区 → 转正
        r = c.post("/api/rag/cases/pending", json={
            "image_path": "data/tmp_1.jpg", "task_id": 1,
            "detection_json": {"class_name": "no_helmet"},
            "vlm_result": {"severity": "high"},
        })
        print(f"4. pending -> {r.status_code} id={r.json().get('id')}")
        assert r.status_code == 201
        pid = r.json()["id"]

        r = c.post(f"/api/rag/cases/{pid}/confirm",
                   json={"operator": "admin", "human_decision": "确认未戴安全帽，高风险"})
        print(f"5. confirm -> {r.status_code} decision={r.json().get('human_decision')}")
        assert r.status_code == 200

        # 6. 重复转正 → 404（已消费）
        r = c.post(f"/api/rag/cases/{pid}/confirm", json={"operator": "admin", "human_decision": "x"})
        print(f"6. re-confirm -> {r.status_code}")
        assert r.status_code == 404

    print("\n✅ T7.8 自检通过")


if __name__ == "__main__":
    main()
