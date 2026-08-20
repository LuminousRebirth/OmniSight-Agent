"""推理轨迹（§7.9 T7.9-1 基础版）：结构化记录路由/检测中间步骤，可回放。

ponytail: 内存存储（重启丢失）；Phase 4 多 Agent 编排时持久化。
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from uuid import uuid4

TRACES: dict[str, dict] = {}


@dataclass
class TraceStep:
    """单步记录：做了什么 / 结果如何 / 耗时"""
    step: str          # 步骤名：候选池|尝试|零样本兜底
    detail: str        # 说明（如模型名 + 命中数）
    elapsed_ms: int = 0


def new_trace() -> str:
    """创建空 trace，返回 trace_id"""
    trace_id = uuid4().hex
    TRACES[trace_id] = {"steps": [], "started_at": time.time()}
    return trace_id


def add_step(trace_id: str, step: str, detail: str, elapsed_ms: int = 0) -> None:
    """追加一步记录"""
    trace = TRACES.get(trace_id)
    if trace is not None:
        trace["steps"].append(asdict(TraceStep(step, detail, elapsed_ms)))


def get_trace(trace_id: str) -> dict | None:
    """读取完整轨迹（含总耗时）"""
    trace = TRACES.get(trace_id)
    if trace is None:
        return None
    return {
        "trace_id": trace_id,
        "steps": trace["steps"],
        "total_ms": int((time.time() - trace["started_at"]) * 1000),
    }
