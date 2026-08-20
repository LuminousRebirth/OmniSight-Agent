/** 后端 API 封装（axios） */
import axios from "axios";

export interface Detection {
  bbox: [number, number, number, number]; // x1,y1,x2,y2 像素坐标
  confidence: number;
  class_name: string;
  track_id?: number | null;
  metadata: Record<string, unknown>;
}

export interface DetectImageResult {
  model: string;
  detections: Detection[];
  stub: boolean;
}

export interface RouteResult extends DetectImageResult {
  fallback_steps: string[];
  zero_shot_used: boolean;
  trace_id?: string | null;
}

export interface VideoTask {
  status: "queued" | "running" | "completed" | "failed";
  model: string;
  frames_total: number;
  results: { frame_no: number; detections: Detection[] }[];
  error?: string;
}

export interface CameraSourceItem {
  id: number;
  name: string;
  source_type: string;
  uri: string;
  resolution?: string | null;
  fps?: number | null;
  status?: string | null;
  live: boolean;
}

export interface TraceStep {
  step: string;
  detail: string;
  elapsed_ms: number;
}

/** 图片检测：POST /api/detect/image */
export async function detectImage(file: File): Promise<DetectImageResult> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await axios.post<DetectImageResult>("/api/detect/image", form);
  return data;
}

/** 视频检测（异步）：返回 task_id */
export async function detectVideo(file: File, jumpN = 3): Promise<{ task_id: string }> {
  const form = new FormData();
  form.append("file", file);
  form.append("jump_n", String(jumpN));
  const { data } = await axios.post("/api/detect/video", form);
  return data;
}

/** 视频检测任务轮询 */
export async function getVideoTask(taskId: string): Promise<VideoTask> {
  const { data } = await axios.get(`/api/detect/tasks/${taskId}`);
  return data;
}

/** 自动路由（四级，含零样本兜底） */
export async function routeImage(file: File, userText = ""): Promise<RouteResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("user_text", userText);
  const { data } = await axios.post<RouteResult>("/api/route/image", form);
  return data;
}

/** 推理轨迹回放 */
export async function getTrace(traceId: string): Promise<{ trace_id: string; steps: TraceStep[]; total_ms: number }> {
  const { data } = await axios.get(`/api/agent/trace/${traceId}`);
  return data;
}

/** 本机摄像头枚举 */
export async function listDevices(): Promise<{ index: number; name: string; is_obs: boolean }[]> {
  const { data } = await axios.get("/api/cameras/enumerate");
  return data;
}

/** 已登记摄像头源列表 */
export async function listCameras(): Promise<CameraSourceItem[]> {
  const { data } = await axios.get("/api/cameras");
  return data;
}

/** 登记摄像头源 */
export async function createCamera(name: string, sourceType: string, uri: string): Promise<CameraSourceItem> {
  const { data } = await axios.post("/api/cameras", { name, source_type: sourceType, uri });
  return data;
}

/** 启动实时检测流 */
export async function liveStart(cameraId: number, resolutionMode = "smooth"): Promise<{ stream_id: string }> {
  const { data } = await axios.post("/api/detect/live/start", { camera_id: cameraId, resolution_mode: resolutionMode });
  return data;
}

/** 停止实时检测流 */
export async function liveStop(streamId: string): Promise<{ frames_processed: number; alerts_count: number }> {
  const { data } = await axios.post(`/api/detect/live/${streamId}/stop`);
  return data;
}
