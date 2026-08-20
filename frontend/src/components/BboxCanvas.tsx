/** 检测画布：图片 + 检测框叠加（白蓝风格，框按原图尺寸百分比定位自适应缩放） */
import { useState } from "react";
import type { Detection } from "../api";

interface Props {
  src: string;
  detections: Detection[];
}

export default function BboxCanvas({ src, detections }: Props) {
  const [size, setSize] = useState<{ w: number; h: number } | null>(null);
  const pct = (v: number, total: number) => `${(v / total) * 100}%`;

  return (
    <div style={{ position: "relative", display: "inline-block", maxWidth: "100%" }}>
      <img
        src={src}
        alt="检测目标"
        onLoad={(e) => setSize({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })}
        style={{ maxWidth: "100%", display: "block", borderRadius: 8 }}
      />
      {size && detections.map((d, i) => {
        const [x1, y1, x2, y2] = d.bbox;
        return (
          <div key={i} style={{
            position: "absolute", left: pct(x1, size.w), top: pct(y1, size.h),
            width: pct(x2 - x1, size.w), height: pct(y2 - y1, size.h),
            border: "2px solid var(--primary)", borderRadius: 4, boxSizing: "border-box",
          }}>
            <span style={{
              position: "absolute", top: -22, left: -2,
              background: "var(--primary)", color: "#fff", fontSize: 12,
              padding: "1px 6px", borderRadius: 4, whiteSpace: "nowrap",
            }}>
              {d.class_name} {(d.confidence * 100).toFixed(0)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
