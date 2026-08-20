"""文本向量化（Phase 2 起步：确定性哈希 128 维；Phase 3 可换 bge-m3）"""
from __future__ import annotations

import hashlib

DIM = 128


def encode_text(text: str) -> list[float]:
    """词哈希频次向量 + L2 归一化（确定性，同一文本同向量）"""
    vec = [0.0] * DIM
    for token in text.split():
        vec[int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % DIM] += 1.0
    norm = sum(v * v for v in vec) ** 0.5
    return [v / norm for v in vec] if norm else vec
