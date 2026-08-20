# 02 · B 视觉检测域（Phase 1）

> 对应 PROJECT_SKELETON.md §7.5（检测推理层）、§7.6（自动路由）、§7.12（前端骨架）。
> 交付顺序：T7.5-1 → T7.5-2 → T7.5-3 → T7.5-4 → T7.6-1 → T7.12-1..6 → T7.9-1

## 1. 检测器插件化结构

```
BaseDetector (load_model / detect / warmup / unload)
 ├── UltralyticsDetector   ← 真 YOLO26：加载注册表权重推理（helmet_v26 挂 best.pt）
 ├── ZeroShotDetector      ← YOLO-World 按文本提示词检测任意类别（Phase 1 起内置，权重后装）
 ├── StubDetector          ← 无权重/无 GPU 环境模拟输出，保证链路恒可跑
 └── DetectorManager       ← 注册中心 + 懒加载 + LRU 显存卸载 + 路由分发
```

统一输出 `Detection`（bbox/confidence/class_name/track_id/metadata.detector_type），禁止各写各的。

## 2. 视频流水线（pipeline.py）

```
抽帧 → 跳帧(默认 N=3) → ByteTrack/IoU 跟踪插值 → 时序过滤(连续 M 帧确认)
→ 确认帧触发 告警/VLM/事件（省算力 + 防单帧误报）
```

## 3. 实时采集（camera/）

```
CameraSource 接口 (open/read_frame/release/is_opened/set_property)
 ├── LocalCameraSource    ← Windows DirectShow 枚举(CAP_DSHOW)，按名匹配 OBS Virtual Camera，失败降级 CAP_ANY
 ├── NetworkCameraSource  ← RTSP/RTMP ffmpeg 拉流 + 指数退避重连(1s→2s→4s…上限30s)
 └── CameraManager        ← 枚举/测试/状态
WS 推流：检测后帧 JPEG 编码 10-15fps + 结构化结果；smooth/hd 带宽自适应（降推流质量，检测仍全帧率）；
多用户连同一路流：服务端单实例采集、多路 WS 分发。
```

## 4. 四级自动路由（routing/）

```
第1级 CLIP 粗筛：图片编码 vs ACTIVE 能力向量 → top-3        （毫秒级零成本）
第2级 决策器：CLIP相似度 + 用户文本意图 + 对话上下文 + 长记忆 + 候选能力描述
第3级 YOLO 执行 + 回退：置信度校验 → 全低换候选重试(≤2次)
第4级 零样本兜底：无候选/仍低 → ZeroShotDetector + VLM 描述 → "疑似新类别"引导
```

- Phase 1：粗筛/决策用简化实现（关键词 + 候选遍历），**第 4 级零样本兜底必须真接入**（zero_shot_used=true）
- Phase 2：替换为 ClipEmbedder（open_clip）+ LlmDecider（走 §7.7 Provider）
- 视频/实时：首帧路由一次，后续沿用
- 候选池 = ACTIVE 注册模型 + 内置零样本标记；注册表为空**永不抛错**

## 5. 前端骨架（T7.12）

- 6 页路由：/detect、/chat、/models、/datasets、/training、/agent-builder
- 关键组件：`BboxCanvas`（bbox 叠加/缩放）、WS hooks（训练指标/检测帧/告警三路复用）
- 实时检测页：采集源下拉 → 连接测试 → 开始检测 WS 接流 → 预览区模型/FPS/分辨率 → 告警面板 → 零样本兜底提示卡片

## 6. 验收（Phase 1）

```bash
curl -X POST http://localhost:8000/api/detect/image -F "file=@demo.jpg"   # 有结果
curl -X POST http://localhost:8000/api/detect/video -F "file=@demo.mp4"   # 返回 task_id
curl http://localhost:8000/api/cameras/enumerate                          # 本机设备(含 OBS)
# 前端 /detect 三模式页签可见；scripts/smoke_test.py 通过
```
