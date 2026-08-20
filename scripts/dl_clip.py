"""下载并解压 ultralytics/CLIP 源码（GitHub codeload zip，绕开 git 客户端）。

用法：conda activate omnisight && python scripts/dl_clip.py
"""
import io
import sys
import zipfile
from pathlib import Path

import httpx

URL = "https://codeload.github.com/ultralytics/CLIP/zip/refs/heads/main"
DEST_DIR = Path(__file__).resolve().parents[1] / "data" / "clip_src"


def main() -> None:
    r = httpx.get(URL, follow_redirects=True, timeout=180)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extractall(DEST_DIR)
    print(f"解压完成: {DEST_DIR} ({len(r.content)} bytes)")


if __name__ == "__main__":
    main()
