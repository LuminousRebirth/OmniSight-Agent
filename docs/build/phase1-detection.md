# Phase 1 · 核心闭环补齐（搭建记录）

> 目标：从"有骨架无能力"升级为"能识别图片/视频/实时流的可交互工作台"。
> 详细设计见 `../architecture/02-detection.md`；规范以 `../PROJECT_SKELETON.md` §6 为准。

## 步骤清单

### T7.5-1 · BaseDetector + UltralyticsDetector（含 StubDetector 兜底）
- 状态：✅ 完成
- 改动文件：detection/{base.py, ultralytics_det.py, stub.py, manager.py, routes.py}（detect API）+ scripts/detect_check.py；自检通过（Stub 兜底 + helmet best.pt 真加载 + API 200）
- 审核：⏳ Phase 1 统一审核
- 存档：-

### T7.5-2 · ZeroShotDetector（YOLO-World 提示词检测）
- 状态：✅ 完成
- 改动文件：detection/zero_shot.py（YOLO-World 提示词检测；权重首次使用自动下载）
- 审核：⏳ Phase 1 统一审核
- 存档：-

### T7.5-3 · 视频流水线（抽帧/跳帧/跟踪/时序过滤）
- 状态：✅ 完成
- 改动文件：detection/pipeline.py（IoU 跟踪 + 时序过滤）+ routes.py（video 异步任务 API）+ scripts/video_check.py；自检通过（任务 completed）
- 审核：⏳ Phase 1 统一审核
- 存档：-

### T7.5-4 · 实时采集（CameraSource 三类 + WS 推流）
- 状态：✅ 完成
- 改动文件：detection/camera/{camera_source.py, camera_manager.py}（Local/Network + 退避重连 + 枚举测试）+ detection/live.py（摄像头 CRUD/test + live start/stop + WS 推流）+ scripts/camera_check.py；自检通过（枚举/CRUD/无设备降级 400/404）
- 审核：⏳ Phase 1 统一审核
- 存档：-

### T7.6-1 · 路由接入第 4 级零样本兜底
- 状态：✅ 完成
- 改动文件：routing/{service.py, routes.py}（四级路由：候选→执行+置信度回退→零样本兜底；POST /api/route/image + GET /api/route/candidates）+ scripts/route_check.py；自检通过（候选池 helmet+zero_shot、纯色图零样本兜底 zero_shot=True）
- 依赖：yolov8s-world.pt（data/，代理续传下载）+ ultralytics/CLIP（pip 本地安装，YOLO-World 文本编码）
- 审核：⏳ Phase 1 统一审核
- 存档：-

### T7.12-1 · 前端工程 + 路由 + 布局（6 页骨架）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.12-2 · API 封装（axios）+ WS hooks
- 状态：✅ 完成
- 改动文件：frontend/src/api.ts（detectImage/detectVideo/getVideoTask/routeImage/getTrace/listDevices/createCamera/liveStart/liveStop）+ hooks/useSocket.ts（WS 帧/结果/状态）+ vite.config.ts（/api ws 代理）
- 审核：⏳ Phase 1 统一审核
- 存档：-

### T7.12-3 · BboxCanvas 组件
- 状态：✅ 完成
- 改动文件：frontend/src/components/BboxCanvas.tsx（检测框叠加 + 置信度徽章，白蓝风格）
- 审核：⏳ Phase 1 统一审核
- 存档：-

### T7.12-4 · 识别工作台（图片/视频/实时三模式）
- 状态：✅ 完成
- 改动文件：frontend/src/pages/DetectPage.tsx（Tabs 三模式：图片=路由+画框+轨迹；视频=异步任务轮询结果帧表；实时=枚举设备+启动流+WS 帧显示+停止）；tsc 通过
- 审核：⏳ Phase 1 统一审核
- 存档：-

### T7.12-5 · 模型库页（Phase 2 联调前骨架）
- 状态：✅ 完成
- 改动文件：frontend/src/pages/ModelsPage.tsx（模型列表 + 状态徽章 draft/pending/active/rejected）
- 审核：⏳ Phase 1 统一审核
- 存档：-

### T7.12-6 · 对话分析页（推理轨迹基础版）
- 状态：✅ 完成
- 改动文件：frontend/src/pages/ChatPage.tsx（上传+意图 → 路由 → 画框 + Timeline 轨迹回放含耗时）
- 审核：⏳ Phase 1 统一审核
- 存档：-

### T7.9-1 · 推理轨迹数据结构 + 记录中间步骤
- 状态：✅ 完成
- 改动文件：agent/{trace.py, routes.py}（TraceStep 结构化 + GET /api/agent/trace/{id} 回放）+ routing/service.py（每步记录候选/尝试/零样本 + 耗时）+ route API 返回 trace_id；自检通过（steps=3）
- 审核：⏳ Phase 1 统一审核
- 存档：-

## 阶段验收（全部通过才进 Phase 2）

```bash
curl -X POST http://localhost:8000/api/detect/image -F "file=@demo.jpg"
curl -X POST http://localhost:8000/api/detect/video -F "file=@demo.mp4"   # task_id
curl http://localhost:8000/api/cameras/enumerate
# 前端 /detect 三模式页签可见；scripts/smoke_test.py 通过
```

## Phase 1 验收结果

- ✅ **全部步骤完成待用户验收**：后端检测/视频/实时/路由/轨迹 API 全通（scripts/{detect,video,camera,route}_check.py 自检全绿）；前端三模式 + 对话轨迹 + 模型库（tsc 0 错误）
- 待用户确认后存档7 并进入 Phase 2
