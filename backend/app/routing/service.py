"""四级路由服务（§7.6 Phase 1 简化版）。

第1级 CLIP 粗筛 / 第2级 LLM 决策 → Phase 2 换 ClipEmbedder + LlmDecider；
Phase 1 按候选顺序执行 + 置信度校验回退；第4级零样本兜底必须真接入。
轨迹：每步记录到 agent.trace（T7.9-1）。
"""
from __future__ import annotations

import asyncio
import time

import numpy as np
from sqlalchemy.orm import Session

from ..agent.trace import add_step
from ..core.models import Model
from ..detection.manager import manager
from ..detection.zero_shot import ZeroShotDetector

CONF_MIN = 0.3  # 命中最低置信度（低于则换候选/走兜底）


def _record(trace_id: str | None, step: str, detail: str, elapsed_ms: int = 0) -> None:
    if trace_id:
        add_step(trace_id, step, detail, elapsed_ms)


async def _zero_shot_fallback(image: np.ndarray, user_text: str,
                              trace_id: str | None = None) -> tuple[list, str]:
    """第4级：零样本兜底（YOLO-World 按提示词检测，失败返回空不抛错）"""
    prompt = [user_text] if user_text else ["helmet", "no_helmet", "fire", "smoke"]
    detector = ZeroShotDetector(prompt=prompt)
    t0 = time.time()
    try:
        detections = await asyncio.to_thread(detector.detect, image)
    except Exception:
        detections = []
    _record(trace_id, "零样本兜底", f"prompt={prompt}: {len(detections)} 目标",
            int((time.time() - t0) * 1000))
    return detections, f"零样本兜底(prompt={prompt}): {len(detections)} 目标"


async def route_image(image: np.ndarray, user_text: str, db: Session,
                      trace_id: str | None = None) -> dict:
    """对单图执行四级路由，返回 {model, detections, fallback_steps, zero_shot_used}"""
    steps: list[str] = []
    active = db.query(Model).filter(Model.status == "active").all()
    steps.append(f"候选池: {[m.name for m in active] or '空'}")
    _record(trace_id, "候选池", f"{[m.name for m in active] or '空'}")

    # 第3级：按候选顺序执行 + 置信度校验（回退重试 ≤2 个候选）
    for m in active[:3]:
        detector = manager.get(m.name, m.weights_path)
        t0 = time.time()
        detections = await asyncio.to_thread(detector.detect, image)
        elapsed = int((time.time() - t0) * 1000)
        hits = [d for d in detections if d.confidence >= CONF_MIN]
        steps.append(f"尝试 {m.name}: 命中 {len(hits)}")
        _record(trace_id, "尝试", f"{m.name}: 命中 {len(hits)}", elapsed)
        if hits:
            return {"model": m.name, "detections": hits,
                    "fallback_steps": steps, "zero_shot_used": False}

    # 第4级：零样本兜底（永不抛错）
    detections, step = await _zero_shot_fallback(image, user_text, trace_id)
    steps.append(step)
    return {"model": "zero_shot", "detections": detections,
            "fallback_steps": steps, "zero_shot_used": True}
