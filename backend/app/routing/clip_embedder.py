"""CLIP 图片/文本编码（§7.6 生产化粗筛；复用 ultralytics/CLIP fork，懒加载 + 失败降级）"""
from __future__ import annotations

import numpy as np


class ClipEmbedder:
    """CLIP 双塔编码：图片与能力描述同一向量空间比较（余弦相似度）"""

    def __init__(self) -> None:
        self._model = None
        self._preprocess = None

    def _load(self) -> None:
        if self._model is None:
            import clip
            import torch  # noqa: F401  确保 torch 已加载
            self._model, self._preprocess = clip.load("ViT-B/32", device="cpu")

    def encode_image(self, image_bgr: np.ndarray) -> np.ndarray:
        """BGR 图像 → 512 维向量"""
        self._load()
        import torch
        from PIL import Image
        img = self._preprocess(Image.fromarray(image_bgr[..., ::-1])).unsqueeze(0)  # BGR→RGB
        with torch.no_grad():
            return self._model.encode_image(img).numpy()[0]

    def encode_text(self, text: str) -> np.ndarray:
        """文本 → 512 维向量"""
        self._load()
        import clip
        import torch
        tokens = clip.tokenize([text])
        with torch.no_grad():
            return self._model.encode_text(tokens).numpy()[0]

    def cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        """余弦相似度"""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


clip_embedder = ClipEmbedder()
