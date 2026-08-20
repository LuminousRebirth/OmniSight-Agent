/** 对话分析页（T7.12-6 基础版）：上传图片 → 自动路由 → 推理轨迹可视化回放 */
import { useState } from "react";
import { Card, Empty, Input, Tag, Timeline, Upload } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { getTrace, routeImage, type TraceStep } from "../api";
import BboxCanvas from "../components/BboxCanvas";

export default function ChatPage() {
  const [src, setSrc] = useState("");
  const [userText, setUserText] = useState("");
  const [result, setResult] = useState<Awaited<ReturnType<typeof routeImage>> | null>(null);
  const [trace, setTrace] = useState<{ steps: TraceStep[]; total_ms: number } | null>(null);
  const [loading, setLoading] = useState(false);

  const analyze = async (file: File) => {
    setSrc(URL.createObjectURL(file));
    setLoading(true);
    try {
      const r = await routeImage(file, userText);
      setResult(r);
      setTrace(r.trace_id ? await getTrace(r.trace_id) : null);
    } finally {
      setLoading(false);
    }
    return false;
  };

  return (
    <div style={{ padding: 24 }}>
      <Card title="对话分析">
        <Upload.Dragger accept="image/*" showUploadList={false} beforeUpload={analyze} disabled={loading}>
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">上传图片，查看 Agent 分析结论与推理轨迹</p>
        </Upload.Dragger>
        <Input
          style={{ marginTop: 12 }}
          placeholder="补充分析意图（如：检测安全帽）"
          value={userText}
          onChange={(e) => setUserText(e.target.value)}
          allowClear
        />
      </Card>

      {src && (
        <div style={{ marginTop: 16 }}>
          <Card title="分析结果">
            <div style={{ textAlign: "center" }}>
              <BboxCanvas src={src} detections={result?.detections ?? []} />
              <div style={{ marginTop: 12 }}>
                <Tag color="blue">模型：{result?.model}</Tag>
                {result?.zero_shot_used && <Tag color="orange">零样本兜底</Tag>}
                <Tag color={result?.detections.length ? "green" : "default"}>目标：{result?.detections.length ?? 0}</Tag>
              </div>
            </div>
          </Card>

          <Card title="推理轨迹" style={{ marginTop: 16 }}>
            {trace?.steps.length ? (
              <>
                <Timeline
                  items={trace.steps.map((s) => ({
                    color: "blue",
                    children: (
                      <>
                        <b>{s.step}</b> <span className="mono">({s.elapsed_ms}ms)</span>
                        <div style={{ color: "var(--text-secondary)" }}>{s.detail}</div>
                      </>
                    ),
                  }))}
                />
                <Tag className="mono">总耗时 {trace.total_ms}ms</Tag>
              </>
            ) : (
              <Empty description="上传图片后展示多步推理轨迹" />
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
