/** 识别工作台：图片 / 视频 / 实时 三模式，检测结果下方集成多模态 AI 智能分析 */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Button, Card, Empty, List, Select, Space, Spin, Table, Tabs, Tag, Typography, Upload,
} from "antd";
import { InboxOutlined, ThunderboltOutlined } from "@ant-design/icons";
import {
  analyzeImage, createCamera, detectVideo, getVideoTask, listDevices,
  liveStart, liveStop, routeImage, type AnalysisResult, type Detection,
} from "../api";
import { useSocket } from "../hooks/useSocket";
import BboxCanvas from "../components/BboxCanvas";

/** AI 分析结论卡片（三模式复用：severity / 分析 / 处置建议） */
function AnalysisCard({ result }: { result: AnalysisResult }) {
  const sevColor = (s: string) => (s === "high" ? "red" : s === "medium" ? "orange" : "green");
  return (
    <Card size="small" style={{ marginTop: 12, background: "var(--primary-soft)", borderColor: "#BFDBFE" }}
      title={<Space><ThunderboltOutlined style={{ color: "var(--primary)" }} />多模态 AI 智能分析</Space>}>
      <Space wrap>
        <Tag color={sevColor(result.severity)}>严重度：{result.severity}</Tag>
        <Tag>检测目标：{result.detections.length}</Tag>
      </Space>
      <Typography.Paragraph style={{ marginTop: 8, marginBottom: 4 }}>
        <b>分析：</b>{result.description || "（未配置 VLM API Key，由规则兜底）"}
      </Typography.Paragraph>
      <Typography.Paragraph style={{ marginBottom: 0 }}>
        <b>处置建议：</b>{result.action}
      </Typography.Paragraph>
    </Card>
  );
}

/** ── 图片模式：路由检测 → 画框 + AI 分析 ── */
function ImageTab() {
  const [src, setSrc] = useState("");
  const [result, setResult] = useState<Awaited<ReturnType<typeof routeImage>> | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);

  const onUpload = async (file: File) => {
    setSrc(URL.createObjectURL(file));
    setLoading(true);
    try {
      setResult(await routeImage(file, "检测安全帽"));
    } finally {
      setLoading(false);
    }
    analyzeImage(file).then(setAnalysis).catch(() => setAnalysis(null));
    return false;
  };

  return (
    <Card>
      <Upload.Dragger accept="image/*" showUploadList={false} beforeUpload={onUpload} disabled={loading}>
        <p className="ant-upload-drag-icon"><InboxOutlined /></p>
        <p className="ant-upload-text">点击或拖拽图片上传，自动路由检测（YOLO26 + 零样本兜底）</p>
      </Upload.Dragger>
      {src && (
        <div style={{ marginTop: 16 }}>
          <div style={{ textAlign: "center" }}>
            <BboxCanvas src={src} detections={result?.detections ?? []} />
            <div style={{ marginTop: 12 }}>
              <Tag color="blue">模型：{result?.model}</Tag>
              {result?.zero_shot_used && <Tag color="orange">零样本兜底</Tag>}
              <Tag color={result?.detections.length ? "green" : "default"}>目标：{result?.detections.length ?? 0}</Tag>
            </div>
          </div>
          {analysis && <AnalysisCard result={analysis} />}
          {result?.fallback_steps && (
            <List size="small" header="推理轨迹" style={{ marginTop: 12 }}
              dataSource={result.fallback_steps}
              renderItem={(s, i) => <List.Item><span className="mono">{i + 1}. {s}</span></List.Item>} />
          )}
        </div>
      )}
    </Card>
  );
}

/** ── 视频模式：异步任务 → 确认帧 + AI 分析 ── */
function VideoTab() {
  const [taskId, setTaskId] = useState("");
  const [task, setTask] = useState<Awaited<ReturnType<typeof getVideoTask>> | null>(null);

  const onUpload = async (file: File) => {
    const { task_id } = await detectVideo(file);
    setTaskId(task_id);
    setTask(null);
    return false;
  };

  useEffect(() => {
    if (!taskId) return;
    const timer = setInterval(async () => {
      const t = await getVideoTask(taskId);
      setTask(t);
      if (t.status === "completed" || t.status === "failed") clearInterval(timer);
    }, 1500);
    return () => clearInterval(timer);
  }, [taskId]);

  return (
    <Card>
      <Upload.Dragger accept="video/*" showUploadList={false} beforeUpload={onUpload}>
        <p className="ant-upload-drag-icon"><InboxOutlined /></p>
        <p className="ant-upload-text">上传视频，异步检测（跳帧抽检 + 时序过滤）</p>
      </Upload.Dragger>
      {task && (
        <div style={{ marginTop: 16 }}>
          <Space>
            <Tag className="mono">任务：{taskId.slice(0, 8)}</Tag>
            <Tag color={task.status === "completed" ? "green" : task.status === "failed" ? "red" : "blue"}>
              {task.status}
            </Tag>
          </Space>
          {task.status === "running" && <Spin style={{ marginLeft: 8 }} />}
          <Table style={{ marginTop: 12 }} size="small" rowKey="frame_no" pagination={{ pageSize: 5 }}
            dataSource={task.results ?? []}
            columns={[
              { title: "帧号", dataIndex: "frame_no", width: 100,
                render: (v: number) => <span className="mono">{v}</span> },
              { title: "目标", dataIndex: "detections",
                render: (dets: Detection[]) => dets.map((d, i) => (
                  <Tag key={i} color="blue" className="mono">{d.class_name} {(d.confidence * 100).toFixed(0)}%</Tag>
                )) },
            ]} />
          {task.status === "completed" && task.analysis && <AnalysisCard result={task.analysis as AnalysisResult} />}
        </div>
      )}
    </Card>
  );
}

/** ── 实时模式：WS 帧流 + "分析当前帧" ── */
function LiveTab() {
  const [devices, setDevices] = useState<{ index: number; name: string }[]>([]);
  const [streamId, setStreamId] = useState("");
  const [frameSrc, setFrameSrc] = useState("");
  const [lastJpeg, setLastJpeg] = useState("");
  const [liveDets, setLiveDets] = useState<Detection[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const enumerate = async () => setDevices(await listDevices());

  const onMessage = useCallback((msg: Record<string, unknown>) => {
    if (msg.type === "frame") {
      setFrameSrc(`data:image/jpeg;base64,${msg.jpeg}`);
      setLastJpeg(msg.jpeg as string);
      setAnalysis(null);
    } else if (msg.type === "result") {
      setLiveDets(msg.detections as Detection[]);
    }
  }, []);

  const { connected } = useSocket(streamId ? `ws://${location.host}/api/detect/live/${streamId}` : null, onMessage);

  const start = async (index: number) => {
    const camItem = await createCamera(`USB ${index}`, "usb", String(index));
    const { stream_id } = await liveStart(camItem.id);
    setStreamId(stream_id);
    setElapsed(0);
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
  };

  const stop = async () => {
    if (streamId) await liveStop(streamId);
    setStreamId("");
    setFrameSrc("");
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const analyzeCurrent = async () => {
    if (!lastJpeg || analyzing) return;
    setAnalyzing(true);
    try {
      const bin = atob(lastJpeg);
      const arr = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
      const file = new File([arr], "frame.jpg", { type: "image/jpeg" });
      setAnalysis(await analyzeImage(file));
    } finally {
      setAnalyzing(false);
    }
  };

  useEffect(() => () => { if (timerRef.current) clearInterval(timerRef.current); }, []);

  return (
    <Card>
      <Space wrap>
        <Button onClick={enumerate}>枚举本机设备</Button>
        {devices.length > 0 && (
          <Select style={{ width: 260 }} placeholder="选择摄像头"
            options={devices.map((d) => ({ value: d.index, label: `${d.index}: ${d.name}` }))}
            onSelect={(v) => start(v)} />
        )}
        {streamId && <Button danger onClick={stop}>停止</Button>}
        {lastJpeg && <Button icon={<ThunderboltOutlined />} onClick={analyzeCurrent} loading={analyzing}>
          分析当前帧
        </Button>}
        <Tag color={connected ? "green" : "default"}>{connected ? `连接中 · ${elapsed}s` : "未连接"}</Tag>
      </Space>
      {!devices.length && <Empty style={{ marginTop: 24 }} description="点击「枚举本机设备」查看可用摄像头（无设备则不可用）" />}
      {frameSrc && (
        <div style={{ marginTop: 16 }}>
          <div style={{ textAlign: "center", background: "var(--text)", borderRadius: 8, padding: 8 }}>
            <img src={frameSrc} alt="实时检测帧" style={{ maxWidth: "100%", maxHeight: 380, borderRadius: 6 }} />
            <div style={{ marginTop: 8 }}>
              {liveDets.map((d, i) => (
                <Tag key={i} color="blue" className="mono">{d.class_name} {(d.confidence * 100).toFixed(0)}%</Tag>
              ))}
              {!liveDets.length && <span style={{ color: "#94A3B8" }}>等待目标...</span>}
            </div>
          </div>
          {analysis && <AnalysisCard result={analysis} />}
        </div>
      )}
    </Card>
  );
}

export default function DetectPage() {
  return (
    <div style={{ padding: 24 }}>
      <Tabs items={[
        { key: "image", label: "图片检测", children: <ImageTab /> },
        { key: "video", label: "视频检测", children: <VideoTab /> },
        { key: "live", label: "实时检测", children: <LiveTab /> },
      ]} />
    </div>
  );
}
