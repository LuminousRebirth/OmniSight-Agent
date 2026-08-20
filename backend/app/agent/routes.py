"""Agent API（Phase 1 基础：推理轨迹查询回放）"""
from fastapi import APIRouter, HTTPException

from ..agent.trace import get_trace

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/trace/{trace_id}")
def trace_api(trace_id: str):
    """推理轨迹回放（每步：决策依据/模型/命中/耗时）"""
    trace = get_trace(trace_id)
    if trace is None:
        raise HTTPException(404, "轨迹不存在")
    return trace
