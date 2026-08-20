# AGENTS.md — 项目执行入口（Codex / Claude Code / DeepSeek 自动读取）

> 本文档是各编码智能体（harness）进入本项目的第一站。**读完本文件后，立即通读 `PROJECT_SKELETON.md`（从 0 构建文档 v2.1）再动手。**

## 项目一句话

**YOLO + 多模态 Agent 多功能图片/视频识别检测工作台**：用户上传任意图片/视频/接实时摄像头，系统自动路由到已审批的 YOLO 模型做检测，VLM 做语义分析，RAG 提供知识依据，Agent 编排全过程；**不绑定预定义数据集**——未知类别走零样本兜底（YOLO-World/CLIP），人工确认后自动转正为新任务并训练注册。

四要素：**YOLO = 视觉通路，VLM = 分析大脑，RAG = 经验记忆，Agent = 调度中枢**。

## 执行规则（与构建文档 §1 一致，全部硬性）

1. **从 0 构建**：本仓库无任何既有代码，所有模块按 `PROJECT_SKELETON.md` 从 0 实现，不得假设已有能力。
2. **按构建文档 §6 阶段顺序执行**（Phase 0 → 1 → 2 → 3 → 4），禁止跳阶段。
3. **每阶段完成必须运行该阶段验收命令并全部通过**，才能进入下一阶段。
4. **schema 与 API 以构建文档 §4/§5 为准**，不得臆造字段/端点。
5. 检测结果统一 `Detection` 结构；长任务一律返回 `task_id`（构建文档 §3.4）。
6. 写操作必须鉴权/审批；只有人工确认结果可入 RAG 案例库。
7. 遇到歧义：查构建文档 §3/§4/§5/§7 → 仍不确定则在 `IMPLEMENTATION_NOTES.md` 记录假设并继续，不阻塞。
8. 每个模块完成后，在 `README.md` 标记 ✅ 并同步 `PROJECT_SKELETON.md` §6 勾选框。

## 环境与命令速查

```bash
# 依赖清单在项目根目录
pip install -r requirements.txt

# 启动后端（端口 8000；Phase 0 后启动即建表并注入种子数据：helmet_v26/wheelhub_v18/fire_smoke_v12）
cd backend && python run.py
# API 文档: http://localhost:8000/docs

# 启动前端（Phase 0 骨架后）
cd frontend && npm install && npm run dev   # http://localhost:5173

# Phase 0 验收冒烟（确认骨架与种子数据正常）
curl http://localhost:8000/api/models
curl http://localhost:8000/api/models/active
curl http://localhost:8000/api/agent/memory
```

## 常用路径

| 内容 | 位置 |
|------|------|
| 从 0 构建文档（唯一权威，按此实现） | `PROJECT_SKELETON.md` |
| 项目概览 + 构建进度（随构建更新 ✅） | `README.md` |
| 改进与扩展方案（27 项，按优先级插入阶段 2/3） | `IMPROVEMENT_PLAN.md` |
| 构建假设/决策记录（自建，逐任务追加） | `IMPLEMENTATION_NOTES.md` |
| 后端源码（Phase 0 起逐模块构建） | `backend/app/{core,model_lifecycle,routing,detection,agent,datasets,training,vlm,rag,alerts,mcp,system}/` |
| 本地数据（SQLite 等） | `data/` |

## 交付顺序提醒

- **Phase 0**：项目骨架 + 全量建表（28 张）+ 种子数据 + 鉴权框架 + 前端工程初始化
- **Phase 1**：真 YOLO 检测器 + ZeroShotDetector + 视频流水线 + 实时采集（OBS/USB/RTSP）+ 前端 6 页骨架
- **Phase 2**：任务开放化 + 数据集/标注/训练/VLM/RAG + 路由生产化（CLIP/LlmDecider）
- **Phase 3**：告警分级去重 + 工单闭环 + 漂移检测
- **Phase 4**：MCP 工具网关 + 多 Agent 编排 + Agent 构建画布 + 外部连接器

> 每个功能模块的具体实现规格（功能定义、为什么这么设计、文件、接口、验收点）都在 `PROJECT_SKELETON.md` §7，直接照做。
