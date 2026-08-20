# Phase 1 · 核心闭环补齐（搭建记录）

> 目标：从"有骨架无能力"升级为"能识别图片/视频/实时流的可交互工作台"。
> 详细设计见 `../architecture/02-detection.md`；规范以 `../PROJECT_SKELETON.md` §6 为准。

## 步骤清单

### T7.5-1 · BaseDetector + UltralyticsDetector（含 StubDetector 兜底）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.5-2 · ZeroShotDetector（YOLO-World 提示词检测）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.5-3 · 视频流水线（抽帧/跳帧/跟踪/时序过滤）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.5-4 · 实时采集（CameraSource 三类 + WS 推流）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.6-1 · 路由接入第 4 级零样本兜底
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.12-1 · 前端工程 + 路由 + 布局（6 页骨架）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.12-2 · API 封装（axios）+ WS hooks
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.12-3 · BboxCanvas 组件
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.12-4 · 识别工作台（图片/视频/实时三模式）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.12-5 · 模型库页（Phase 2 联调前骨架）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.12-6 · 对话分析页（推理轨迹基础版）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.9-1 · 推理轨迹数据结构 + 记录中间步骤
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

## 阶段验收（全部通过才进 Phase 2）

```bash
curl -X POST http://localhost:8000/api/detect/image -F "file=@demo.jpg"
curl -X POST http://localhost:8000/api/detect/video -F "file=@demo.mp4"   # task_id
curl http://localhost:8000/api/cameras/enumerate
# 前端 /detect 三模式页签可见；scripts/smoke_test.py 通过
```
