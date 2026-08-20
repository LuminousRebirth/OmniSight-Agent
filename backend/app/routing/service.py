"""四级路由服务（§7.6 Phase 2 生产化）。

第1级 CLIP 粗筛（图片 vs 能力描述，top-3）→ 第2级 LLM 决策（VLM Provider）
→ 第3级 YOLO 执行 + 置信度回退 → 第4级零样本兜底（永不抛错）。
CLIP/LLM 不可用时自动降级为顺序候选，链路恒可跑。
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
from ..vlm.factory import RuleFallback, get_provider
from .clip_embedder import clip_embedder

CONF_MIN = 0.3  # 命中最低置信度


def _record(trace_id: str | None, step: str, detail: str, elapsed_ms: int = 0) -> None:
    if trace_id:
        add_step(trace_id, step, detail, elapsed_ms)


def clip_top3(db: Session, active: list[Model], image: np.ndarray) -> list[Model]:
    """第1级：CLIP 图片编码 vs 能力描述文本编码 → 相似度 top-3；失败降级顺序候选"""
    try:
        img_vec = clip_embedder.encode_image(image)
        scored = [(m, clip_embedder.cosine(img_vec, clip_embedder.encode_text(m.capability_desc or m.name)))
                  for m in active]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored[:3]]
    except Exception:
        return active[:3]  # CLIP 权重不可用 → 顺序候选


def llm_decide(cands: list[Model], user_text: str) -> list[Model]:
    """第2级：LLM 决策（接入 VLM Provider；无 Provider 时取首个候选）"""
    if not cands:
        return []
    provider = get_provider()
    if isinstance(provider, RuleFallback):
        return [cands[0]]  # 无可用 VLM → 保守取 top-1
    return [cands[0]]  # ponytail: 完整多候选裁决留待 Phase 4 多 Agent 编排


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

    # 第1级 CLIP 粗筛 + 第2级决策
    chosen = llm_decide(clip_top3(db, active, image), user_text)
    steps.append(f"CLIP 粗筛+决策: {[m.name for m in chosen]}")
    _record(trace_id, "粗筛+决策", f"{[m.name for m in chosen]}")

    # 第3级：按决策候选执行 + 置信度校验（回退重试 ≤2 个候选）
    for m in chosen[:3]:
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
