"""下载 YOLO-World 权重（yolov8s-world.pt）到 data/：断点续传 + 自动重试。

GitHub 大文件代理通道不稳定：分段续传，断流自动从已下载字节数重开。
用法：conda activate omnisight && python scripts/dl_world.py
"""
import sys
import time
import urllib.request
from pathlib import Path

URL = "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8s-world.pt"
DEST = Path(__file__).resolve().parents[1] / "data" / "yolov8s-world.pt"
PROXY = "http://127.0.0.1:7897"
EXPECTED = 25_900_000  # 完整文件约 25.9MB


def main() -> None:
    proxy = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy)

    while True:
        existing = DEST.stat().st_size if DEST.exists() else 0
        if existing > 25_000_000:
            print(f"完成: {DEST} ({existing} bytes)")
            return
        try:
            req = urllib.request.Request(URL, headers={
                "User-Agent": "Mozilla/5.0", "Range": f"bytes={existing}-",
            })
            with opener.open(req, timeout=90) as resp, open(DEST, "ab") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
            print(f"完成: {DEST} ({DEST.stat().st_size} bytes)")
            return
        except Exception as exc:
            print(f"断流于 {existing/1048576:.1f}MB，2 秒后续传重试...", flush=True)
            time.sleep(2)


if __name__ == "__main__":
    main()
