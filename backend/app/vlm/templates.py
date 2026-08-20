"""提示词模板引擎（§7.7）：按任务描述 + 检测目标 + 知识依据生成分析提示词"""
from __future__ import annotations


def build_prompt(task_desc: str, class_names: list[str], rag_context: str = "") -> str:
    """生成分析提示词：要求 VLM 输出结构化 JSON（severity/description/action）"""
    targets = "、".join(class_names) if class_names else "检测到的目标"
    return (
        f"你是质检分析专家。任务：{task_desc}\n"
        f"检测到目标：{targets}\n"
        f"知识依据：{rag_context or '无'}\n"
        '请仅输出 JSON：{"severity":"low|medium|high","description":"<成因与说明>","action":"<处置建议>"}'
    )
