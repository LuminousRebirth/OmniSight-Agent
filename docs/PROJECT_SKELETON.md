# YOLO + 多模态 Agent 多功能识别检测工作台 · 从 0 构建文档（Agent Edition v2.1）

> **读者对象**：Codex / Claude Code / DeepSeek 等 **AI 编码智能体（harness）**，人类工程师配合阅读。
> **定位**：这是一份**从 0 构建整个系统**的完整蓝图与执行规范——**不假设任何既有代码**。每个功能模块都写清了**构建什么、为什么这么设计、怎么实现、怎么验收**，可直接照做。
> **执行方式**：按 **§6 阶段顺序**逐任务构建；**每完成一个阶段必须运行该阶段末尾的验收命令并全部通过**，才可进入下一阶段。
> **权威性**：本文档是构建的唯一权威规范。所有数据库表、API 端点、代码结构以本文档为准，不得臆造。
> **入口文件**：`AGENTS.md` 已被各 harness 自动读取，指向本文档；先读 `AGENTS.md`，再按本文档执行。

---

## 1. 构建契约（先读，全部硬性）

以下规则适用于**整个构建过程**，违反任一条即视为执行失败：

| # | 规则 |
|---|------|
| R1 | **从 0 构建**：本系统无任何既有代码，全部模块按本文档从 0 实现；模块之间只依赖本文档定义的接口（§3.4 统一结构 / §5 API / §4 数据模型），不得引入未声明的耦合 |
| R2 | **顺序执行**：必须按 §6 Phase 0 → 1 → 2 → 3 → 4 依次构建，禁止跳阶段、禁止并行改跨模块文件 |
| R3 | **阶段验收**：每个阶段完成后运行该阶段验收命令，**全部通过才可进入下一阶段**；失败则修复到通过为止 |
| R4 | **schema 唯一权威**：所有数据库表、字段、类型、约束以 **§4 数据模型**为准，不得臆造字段名；需要新增字段时在 §4 表中追加并注明"v2.1 新增" |
| R5 | **API 契约唯一权威**：所有端点路径、方法、请求体、响应结构、错误码以 **§5 API 契约**为准；响应必须用 Pydantic 模型定义，禁止返回裸 dict |
| R6 | **统一结构**：检测结果一律用 §3.4 的 `Detection` / `FusedResult` 结构；异步任务一律"提交返回 `task_id` + 轮询/订阅"模式 |
| R7 | **类型与文档**：所有 Python 代码带类型注解 + 模块级 docstring；函数超过 20 行必须写说明注释；关键决策写进 `IMPLEMENTATION_NOTES.md`（根目录，自建） |
| R8 | **权限门禁**：写操作（训练/入库/部署/审批/告警分发）必须鉴权；审批流状态机非法迁移必须硬拦截 |
| R9 | **知识质量**：只有"人工确认过"的结果能写入 RAG 案例库；Agent 自动结论只进待确认区（§7.8 入库权限控制） |
| R10 | **留痕**：审批、路由决策、工具调用、记忆沉淀全部写审计日志/记忆表 |
| R11 | **歧义处理**：先查本文档 §3/§4/§5/§7；仍不确定时，**在 `IMPLEMENTATION_NOTES.md` 记录假设并继续**，不得阻塞、不得回头问人 |
| R12 | **进度同步**：每个模块构建完成后，在 `README.md` 对应模块后标记 ✅ 并勾选 §6 对应任务框 |

---

## 2. 构建范围总览（要构建什么）

### 2.1 目标系统（一句话）

一套 **"YOLO + Agent（多模态 AI）"多功能识别检测工作台**：用户上传任意图片/视频/接实时摄像头，系统自动判断该用哪个已注册的 YOLO 模型做检测，结合多模态 LLM 给出带知识依据的分析结论，触发告警时直接给出处置方案；**不绑定任何预定义数据集/场景**——任何可训练任务都能接入，未知输入走零样本兜底（不抛锚），人工确认后自动转正为新任务并训练注册。

### 2.2 为什么做成这个形态（设计动机）

| 动机 | 对应设计 |
|------|----------|
| 单个检测器解决不了真实问题：工地/质检/消防需要多类模型并存 | 插件化检测层 + 模型注册表（§7.4/7.5） |
| 用户是质检员/安全员，不该关心"该选哪个模型" | 自动路由（§7.6） |
| YOLO 只给坐标，业务要的是"这是什么问题、怎么处理" | VLM 多模态分析（§7.7） |
| VLM 会幻觉、新人没经验，结论需要依据 | RAG 知识中枢（§7.8） |
| 业务会冒出新类别，不能每次都改代码加模型 | 零样本兜底 + 未知转正闭环（§7.5/7.6） |
| 检测结果要变成可处置的动作，不能只停在"画个框" | 告警/工单闭环（§7.11） |

### 2.3 四要素（贯穿全部设计的核心思想）

| 要素 | 角色 | 一句话职责 |
|------|------|-----------|
| **YOLO** | 视觉通路 | 毫秒级逐帧检测，提供像素级坐标，只把"候选帧"触发给 VLM（省钱、实时） |
| **VLM** | 分析大脑 | 对检测结果做语义分析：严重度、成因、处置建议（云端+本地双通道） |
| **RAG** | 经验记忆 | 规范条文/历史案例/模型档案/告警预案，给 VLM 提供依据、给路由提供经验 |
| **Agent** | 调度中枢 | 编排"路由→检测→分析→报告→告警"全链路，跨会话长记忆让系统越用越懂业务 |

### 2.4 13 个功能模块清单（全部从 0 构建）

| 模块 | 一句话功能 | 构建阶段 |
|------|-----------|----------|
| 7.1 数据集管理 | 任意任务的训练数据：上传/抽帧/去重/划分/版本/导出 | Phase 2 |
| 7.2 标注与主动学习 | 标注工作台 + 不确定性采样 + SAM 半自动标注 | Phase 2 |
| 7.3 训练中心 | 异步训练任务、实时指标、产物自动进审批流 | Phase 2 |
| 7.4 模型生命周期 | 审批状态机 + 能力描述向量化 + 注册表（只认 ACTIVE） | Phase 0 骨架 / Phase 2 完善 |
| 7.5 检测推理层 | 插件化检测器 + 视频流水线 + 实时采集 + 零样本兜底 | Phase 1 |
| 7.6 Agent 自动路由 | 四级路由：CLIP 粗筛 → 决策 → 执行回退 → 零样本兜底 | Phase 1/2 |
| 7.7 多模态分析 VLM | Provider 抽象双通道 + 按任务生成 prompt 模板 | Phase 2 |
| 7.8 RAG 知识中枢 | 四类知识源 + 混合检索 + 入库权限控制 | Phase 2 |
| 7.9 Agent 编排与长记忆 | 多 Agent 编排 + 跨会话长记忆 + 推理轨迹 | Phase 1 基础 / Phase 4 完善 |
| 7.10 MCP 工具网关 | 六组工具 + 最小权限挂载 + 审计 | Phase 1 鉴权 / Phase 4 网关 |
| 7.11 告警与工单 | 分级去重 + 多通道推送 + 工单闭环 | Phase 3 |
| 7.12 Web 前端 | 6 页面工作台（React）+ 实时检测页 + Agent 画布 | Phase 1 骨架起 |
| 7.13 部署与运维 | 健康检查 + 漂移检测 + 容器化 | Phase 3+ |

### 2.5 五阶段交付物（构建顺序）

| 阶段 | 交付物 |
|------|--------|
| Phase 0 | 项目骨架 + 全量建表 + 种子数据 + 基础服务启动（§6.0） |
| Phase 1 | 真 YOLO 检测 + 零样本兜底 + 视频/实时流水线 + 前端 6 页骨架 + 鉴权框架 |
| Phase 2 | 任务开放化 + 数据集/标注/训练/VLM/RAG 五大能力 + 路由生产化（CLIP/LLM） |
| Phase 3 | 告警分级去重 + 多通道推送 + 工单闭环 + 漂移检测 + 运维 |
| Phase 4 | MCP 工具网关 + 多 Agent 编排 + Agent 构建画布 + 外部连接器 |

---

## 3. 目标架构

### 3.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│ 前端层  Web 工作台（React 18 + Vite + TS）                     │
│  数据集管理 │ 训练中心 │ 模型库 │ 识别工作台 │ Agent构建 │ 对话分析 │
├─────────────────────────────────────────────────────────────┤
│ API 层  FastAPI REST + WebSocket（训练进度/检测结果/实时帧推送） │
├─────────────────────────────────────────────────────────────┤
│ Agent 编排层                                                  │
│  Agent 构建/执行 │ 自动路由决策 │ 对话长记忆 │ MCP 工具网关     │
├─────────────────────────────────────────────────────────────┤
│ 能力层                                                        │
│  检测推理(插件化+零样本) │ 训练调度 │ 数据集/标注 │ VLM分析(双通道)│
│  RAG知识中枢 │ 告警/工单 │ 模型生命周期(审批注册)               │
├─────────────────────────────────────────────────────────────┤
│ 数据层                                                        │
│  PostgreSQL(元数据,起步SQLite) │ MinIO/S3 │ Milvus/ES(向量)    │
│  Redis(队列/缓存) │ 本地文件系统(数据集原始文件)                 │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 技术栈（版本以安装时最新稳定版为准）

| 层 | 选型 | 用途 |
|----|------|------|
| 前端 | React 18 + Vite + TypeScript | SPA；ECharts 指标曲线；ReactFlow Agent 画布；Ant Design 管理组件 |
| 后端 | FastAPI + Uvicorn | REST + WebSocket + OpenAPI |
| 训练 | Ultralytics YOLO + PyTorch | 训练/导出/部署一体 |
| 任务队列 | Celery + Redis（Phase 1 可用 asyncio 后台任务 + task_id 模拟） | 长任务异步化 |
| 视频采集 | OpenCV VideoCapture + ffmpeg/PyAV | USB/OBS 虚拟摄像头/RTSP 拉流 |
| 元数据库 | PostgreSQL（起步 SQLite） | 模型/数据集/任务/告警/记忆 |
| 对象存储 | MinIO（S3 协议，起步本地文件系统） | 图像/权重/标注文件 |
| 向量库 | Milvus 或 ES+向量插件（起步 numpy 内存实现） | 模型能力/记忆/知识向量 |
| 图像编码 | CLIP（open_clip） | 路由粗筛/按图搜案例/案例入库/零样本相似度（四处复用） |
| 零样本检测 | YOLO-World / GroundingDINO + SAM | 文本提示词检测未训练类别；SAM 掩膜/裁剪 |
| 文本编码 | bge-m3；重排 bge-reranker | 中文文档检索 top-50 → 重排 top-5 |
| VLM | 云端（通义千问VL/GPT-4o）+ 本地（Qwen2.5-VL） | Provider 抽象双通道 |

### 3.3 设计原则（贯穿所有模块）

1. **插件化**：检测器=插件（新类型零侵入）；模型=注册表条目（新模型零改路由）；VLM=Provider（云端/本地零感知切换）
2. **异步化**：一切超过秒级的操作返回 `task_id`
3. **权限门禁**：写操作必须审批或鉴权；MCP 工具最小权限挂载
4. **留痕可审计**：审批/路由/工具调用/记忆沉淀全部落日志
5. **知识质量优先**：只有人工确认的结果进 RAG 案例库
6. **多功能定位**：不绑定预定义数据集/场景；任何可训练任务都能接入；未知输入用零样本兜底不抛锚

### 3.4 跨模块统一结构（代码级契约）

```python
# 检测输出（所有检测器必须返回此结构，禁止各写各的）
@dataclass
class Detection:
    bbox: tuple[float, float, float, float]   # x1,y1,x2,y2（归一化或像素，由配置统一）
    confidence: float
    class_name: str
    track_id: int | None = None
    metadata: dict = field(default_factory=dict)  # 必须含 detector_type: "yolo"|"zero_shot"

# VLM 融合结果（YOLO 框 + VLM 语义）
@dataclass
class FusedResult:
    detections: list[Detection]
    severity: str            # low|medium|high
    description: str
    action: str
    references: list[str]    # RAG 引用来源（防幻觉）

# 异步任务统一返回
# POST /api/xxx  →  200 {"task_id": "..."}，随后 GET /api/xxx/tasks/{task_id} 轮询或 WS 订阅
```

错误码约定：`400` 参数错误（附 message 字段）、`401` 未认证、`403` 越权、`404` 不存在、`409` 状态机非法迁移、`422` schema 校验失败（FastAPI 默认）。

---

## 4. 数据模型（唯一权威，全部本次构建，可直接转 DDL）

> 表清单总览（PostgreSQL 起步 SQLite，Phase 0 一次性建齐）：

| 组 | 表 | 说明 |
|----|-----|------|
| 任务 | task_types / categories | 多功能定位基石（§4.1） |
| 数据集 | datasets / image_items / annotations / dataset_versions | §4.2 |
| 训练 | train_jobs / train_metrics / train_artifacts | §4.3 |
| 模型 | models / approvals | §4.4 |
| 检测 | camera_sources / detection_streams | §4.5 |
| Agent | conversations / messages / memories / memory_events | §4.6 |
| RAG | knowledge_docs / knowledge_chunks / cases / cases_pending | §4.7 |
| 告警 | alerts / alert_dispatches / tickets | §4.8 |
| 系统 | users / roles / audit_logs / mcp_tool_audit | §4.9 |

### 4.1 任务组（多功能定位基石）

**task_types**（任务 = 一类检测目标，自由创建，无枚举上限）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| name | TEXT | NOT NULL UNIQUE | 任务名，如"包装缺陷检测" |
| task_desc | TEXT | NOT NULL | 自由文本任务描述（路由/模板/能力描述共用） |
| status | TEXT | DEFAULT 'active' | active/inactive |

**categories**（类别字典，供标注与零样本提示词复用）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| task_id | INTEGER | FK→task_types.id | 所属任务 |
| name | TEXT | NOT NULL | 类别名，如"划痕" |
| aliases | TEXT | DEFAULT '[]' | JSON 别名数组（零样本提示词展开用） |
| description | TEXT | | 类别描述 |

### 4.2 数据集组

**datasets**：`id PK, name NOT NULL, task_id FK→task_types, version TEXT, status TEXT DEFAULT 'draft'`
**image_items**：`id PK, dataset_id FK, storage_path NOT NULL, width INT, height INT, source_video_id INT NULL`
**annotations**：`id PK, image_id FK, bbox TEXT NOT NULL  -- JSON [x1,y1,x2,y2], class_id FK→categories, is_confirmed INT DEFAULT 0, annotator TEXT, confirmed_by TEXT`
**dataset_versions**：`id PK, dataset_id FK, version_no TEXT, split_ratio TEXT  -- JSON {"train":0.8,"val":0.1,"test":0.1}, train_ids TEXT, val_ids TEXT, test_ids TEXT, created_at TEXT`

### 4.3 训练组

**train_jobs**：`id PK, name TEXT, dataset_version_id FK, base_model_id FK→models NULL, hyperparams TEXT  -- JSON, gpu_ids TEXT  -- JSON, status TEXT DEFAULT 'queued'  -- queued|running|completed|failed|canceled, created_by TEXT, created_at TEXT`
**train_metrics**：`id PK, job_id FK, epoch INT, train_loss REAL, val_loss REAL, mAP50 REAL, mAP50_95 REAL`
**train_artifacts**：`id PK, job_id FK, weights_path TEXT, metrics_report TEXT, created_at TEXT`

### 4.4 模型组

**models**：`id PK, name TEXT, version TEXT, task_id FK→task_types, weights_path TEXT, capability_desc TEXT, capability_vec TEXT  -- JSON 向量, status TEXT  -- draft|pending|active|rejected, approved_by TEXT, approved_at TEXT`
**approvals**：`id PK, model_id FK, action TEXT  -- submit|approve|reject|edit_desc, operator TEXT, comment TEXT, created_at TEXT`

### 4.5 检测组

**camera_sources**：`id PK, name TEXT, source_type TEXT  -- obs|usb|rtsp, uri TEXT  -- 设备名或地址, resolution TEXT, fps INT, status TEXT, created_by TEXT`
**detection_streams**：`id PK, camera_id FK, model_id FK NULL, started_at TEXT, ended_at TEXT NULL, frames_processed INT DEFAULT 0, alerts_count INT DEFAULT 0, status TEXT  -- running|stopped|error`

### 4.6 Agent 组

**conversations**：`id PK, session_id TEXT UNIQUE, title TEXT, created_at TEXT, updated_at TEXT`
**messages**：`id PK, session_id FK, role TEXT  -- user|assistant|tool, content TEXT, created_at TEXT`
**memories**：`id PK, session_id TEXT, memory_type TEXT  -- route_decision|preference|business_conclusion|approval, content TEXT, importance REAL DEFAULT 0.5, embedding TEXT  -- JSON 向量, created_at TEXT`
**memory_events**：`id PK, session_id TEXT, event_type TEXT, payload TEXT  -- JSON, created_at TEXT`

### 4.7 RAG 组

**knowledge_docs**：`id PK, doc_type TEXT  -- regulation|case_source|alert_plan, title TEXT, content TEXT, created_by TEXT, created_at TEXT`
**knowledge_chunks**：`id PK, doc_id FK, chunk_index INT, content TEXT, embedding TEXT  -- JSON 向量`
**cases**（历史案例库，人工确认后写入）：`id PK, image_path TEXT, task_id FK NULL  -- 不限任务, detection_json TEXT, vlm_result TEXT, human_decision TEXT, confirmed_by TEXT, created_at TEXT`
**cases_pending**（待确认区）：字段同 cases + `auto_generated_by TEXT`

### 4.8 告警组

**alerts**：`id PK, source TEXT  -- model/detector 名, level TEXT  -- tip|warning|emergency, target_type TEXT, track_id INT NULL, evidence_image TEXT, message TEXT, status TEXT  -- open|ack|closed`
**alert_dispatches**：`id PK, alert_id FK, channel TEXT  -- ws|wecom|sms, status TEXT, retry_count INT DEFAULT 0`
**tickets**：`id PK, alert_id FK, assignee TEXT, status TEXT  -- open|assigned|processing|review|closed, priority TEXT, due_at TEXT, resolution TEXT, reviewed_by TEXT`

### 4.9 系统组

**users**：`id PK, username UNIQUE, password_hash TEXT, role TEXT  -- admin|operator|viewer, created_at TEXT`
**roles**：`id PK, role_name UNIQUE, permissions TEXT  -- JSON 数组`
**audit_logs**：`id PK, actor TEXT, action TEXT, target TEXT, detail TEXT, created_at TEXT`
**mcp_tool_audit**：`id PK, agent_id TEXT, tool TEXT, args TEXT, result_status TEXT, created_at TEXT`

### 4.10 存储分工

| 数据 | 存储 |
|------|------|
| 元数据（结构化） | PostgreSQL（起步 SQLite） |
| 图像/权重/标注文件 | MinIO / 本地文件系统（`data/`） |
| 向量（能力/记忆/知识） | Milvus 或 ES 向量索引（起步 numpy 内存实现，封装在向量化工厂，接口对齐便于替换） |
| 任务队列/实时指标 | Redis |
| 审计日志 | PostgreSQL + 对象存储归档 |

---

## 5. API 契约（唯一权威，全部从 0 交付）

> 统一前缀 `/api/*`；鉴权 JWT + 角色（admin/operator/viewer），Phase 1 先实现鉴权框架与种子用户，模块级校验可逐步加。所有响应用 Pydantic 模型。

### 5.1 模型生命周期（Phase 0 骨架 + Phase 2 完善）

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/models` | 训练产物提交 | 草稿 Model |
| POST | `/api/models/{id}/approval` | `{"action":"submit\|approve\|reject\|edit_desc","operator","comment"}` | 更新后 Model；非法迁移 409 |
| GET | `/api/models` | - | 全部模型 |
| GET | `/api/models/active` | - | 仅 ACTIVE（路由候选池） |
| GET | `/api/models/{id}/approvals` | - | 审批流水 |
| POST | `/api/models/{id}/desc` | `{"capability_desc"}` | 更新能力描述并**重新向量化** |

### 5.2 自动路由（Phase 1 交付四级，Phase 2 生产化）

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/route/image` | multipart: file + session_id + user_text | `{model, detections[], fallback_steps[], zero_shot_used: bool}` |
| GET | `/api/route/candidates` | - | 候选池（ACTIVE + 零样本标记） |

Phase 1 交付四级路由（含第 4 级零样本兜底，`zero_shot_used=true`）；Phase 2 将粗筛与决策器替换为 `ClipEmbedder` 与 `LlmDecider`。

### 5.3 检测与实时（Phase 1 交付）

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/detect/image` | multipart: file + model(可选) | `{detections[], model}` |
| POST | `/api/detect/video` | multipart: file + model + jump_n(默认3) | `{"task_id"}` |
| GET | `/api/detect/tasks/{task_id}` | - | `{status, frames_total, results[{frame_no, detections[]}]}` |
| GET | `/api/cameras/enumerate` | - | `[{index, name, is_obs}]`（DirectShow 枚举） |
| POST | `/api/cameras` | `{"name","source_type","uri"}` | CameraSource |
| GET | `/api/cameras` | - | 摄像头源列表（含状态） |
| POST | `/api/cameras/{id}/test` | - | `{ok, resolution, fps, error?}` |
| POST | `/api/detect/live/start` | `{"camera_id","model"?,"resolution_mode":"smooth\|hd"}` | `{"stream_id"}` |
| POST | `/api/detect/live/{stream_id}/stop` | - | `{frames_processed, alerts_count}` |
| WS | `/api/detect/live/{stream_id}` | - | 帧消息 + 结果消息（见下） |

WS 消息格式（服务端→客户端）：
```json
{"type":"frame","jpeg":"<base64>","ts":1234.5,"model":"helmet_v26","fps":12.5,"resolution":"1280x720"}
{"type":"result","detections":[{"bbox":[..],"confidence":0.9,"class_name":"no_helmet","track_id":3}],"alert_ids":[7]}
{"type":"status","state":"connecting|running|reconnecting|stopped|error","detail":"..."}
```

### 5.4 任务类型 / 数据集 / 标注（Phase 2 交付）

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/tasks` | `{"name","task_desc","categories":[{"name","aliases","description"}]}` | TaskType（含类别） |
| GET | `/api/tasks` | - | 任务列表 |
| POST | `/api/datasets` | `{"name","task_id"}` | Dataset |
| POST | `/api/datasets/{id}/upload` | multipart: files（图片/视频） | `{"task_id"}`（异步抽帧去重） |
| GET | `/api/datasets/{id}/items` | ?page&size | 分页素材 |
| POST | `/api/datasets/{id}/cluster-preview` | - | 未知图片聚类分组（"疑似新类别"引导） |
| PUT | `/api/annotations/{id}` | `{"bbox","class_id"}` | Annotation |
| POST | `/api/annotations/batch` | `[{image_id,bbox,class_id}]` | 批量保存 |
| POST | `/api/annotations/{id}/confirm` | `{"operator"}` | 确认（进入训练集/案例库原料） |
| POST | `/api/datasets/{id}/split` | `{"ratio":{"train":0.8,"val":0.1,"test":0.1}}` | 划分 |
| POST | `/api/datasets/{id}/versions` | - | 新版本（不可变） |
| GET | `/api/datasets/{id}/export` | ?fmt=yolo | 训练数据包（yaml+images/labels） |
| POST | `/api/datasets/{id}/active-learn` | - | `{"task_id"}` 不确定性样本挑选 |
| GET | `/api/datasets/{id}/active-learn/{task_id}/samples` | - | 待标注样本（含不确定性分） |

### 5.5 训练中心（Phase 2 交付）

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/training/jobs` | `{"name","dataset_version_id","base_model_id"?,"hyperparams"}` | `{"job_id"}` |
| GET | `/api/training/jobs` | ?status | 任务列表 |
| GET | `/api/training/jobs/{id}/metrics` | - | 指标曲线数据 |
| POST | `/api/training/jobs/{id}/stop` | - | 停止 |
| WS | `/api/training/jobs/{id}/stream` | - | `{"epoch","train_loss","mAP50",...}` |

训练完成后自动：生成 `capability_desc` 草稿 → 调 `POST /api/models` 进入审批流（§5.1）。

### 5.6 多模态分析 VLM（Phase 2 交付）

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/analysis/image` | multipart: file + user_text | FusedResult |
| GET | `/api/analysis/providers` | - | Provider 列表/当前 |
| POST | `/api/analysis/report` | `{"image_ids"[]}` | 报告（可对接腾讯文档导出） |

### 5.7 RAG（Phase 2 交付）

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/rag/knowledge` | multipart 或 JSON（doc_type/title/content） | 分块入库 |
| POST | `/api/rag/search` | `{"query_text"?,"query_image"?,"top_k":5}` | 混合检索结果 |
| POST | `/api/rag/cases/pending` | 自动结论 | 写入待确认区 |
| POST | `/api/rag/cases/{id}/confirm` | `{"operator","human_decision"}` | 转正入库 + 可同步 RAG/记忆 |
| DELETE | `/api/rag/knowledge/{id}` | - | 删除（含向量） |

### 5.8 Agent 对话（Phase 1 基础版 + Phase 4 完善）

`POST /api/agent/chat`、`GET /api/agent/sessions/{sid}/context`、`POST /api/agent/memory/search`、`POST /api/agent/events/{type}`、`GET /api/agent/trace/{id}` —— `/chat` 的编排链路在 Phase 1 后接入真实检测与 VLM；`/trace` 返回多 Agent 步骤回放。

### 5.9 告警与工单（Phase 3 交付）

| 方法 | 路径 | 请求 | 响应 |
|------|------|------|------|
| POST | `/api/alerts/{id}/dispatch` | `{"channel"}` | 手动/重发 |
| GET | `/api/alerts` | ?level&status&page | 列表 |
| POST | `/api/tickets` | `{"alert_id","assignee","priority"}` | Ticket |
| PUT | `/api/tickets/{id}` | `{"action":"process\|review\|close","resolution"?}` | 流转 |
| WS | `/api/alerts/stream` | - | 实时告警 |

### 5.10 MCP 网关（Phase 4 交付）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/mcp/tools/list` | 工具清单（含描述） |
| POST | `/api/mcp/agents/{agent_id}/tools` | 配置 Agent 工具子集（最小权限） |
| GET | `/api/mcp/audit` | 工具调用审计 |

MCP 工具分组（自建 MCP Server，命名空间）：`detect.*`（detect_image/detect_video/get_models）、`train.*`（start_training/training_status/stop_training）、`knowledge.*`（knowledge_search/case_add/case_confirm）、`alert.*`（alert_dispatch/ticket_create/ticket_status）、`ops.*`（model_deploy/health_check/list_devices）、`report.*`（docs_report/export_report）。**初期工具总数 ≤10**。

---

## 6. 构建阶段（核心执行骨架）

> 每个阶段 = 目标 + 任务（任务编号引用 §7 实现规格，如 `T7.5-2` = §7.5 第 2 个任务）+ 验收命令。
> **验收命令失败即阶段失败**，修复重跑通过后才继续。

### Phase 0 · 项目骨架与全量建表

**目标**：从空目录搭建出可运行的后端骨架 + 全部数据表 + 种子数据，前端工程可启动。这是后续所有阶段的底座。

- [ ] T0-1 初始化目录结构：`backend/app/{core,model_lifecycle,routing,detection,agent,datasets,training,vlm,rag,alerts,mcp,system}`、`frontend/`、`data/`、`scripts/`、`infra/`
- [ ] T0-2 编写 `requirements.txt`（根目录，FastAPI/uvicorn/sqlalchemy/ultralytics/open_clip_torch/opencv-python/…）并 `pip install`
- [ ] T0-3 实现 `backend/app/core/database.py`：按 **§4 一次性建齐全部 28 张表**（SQLite 起步，连接层封装便于换 PostgreSQL）
- [ ] T0-4 实现 `backend/run.py` + `backend/app/main.py`：FastAPI 装配 + 注册全部路由 + 启动注入种子数据（3 个示例任务：安全帽/轮毂/烟火；3 个示例模型：helmet_v26(active)/wheelhub_v18(pending)/fire_smoke_v12(draft)；种子用户 admin/operator/viewer）
- [ ] T0-5 创建 `IMPLEMENTATION_NOTES.md`（记录构建假设与决策，后续每个任务追加）
- [ ] T0-6 初始化 `frontend/` 骨架（Vite + React + TS），`npm run dev` 可启动
- [ ] T0-7 实现鉴权框架（JWT + 角色校验依赖，供全模块复用）
- [ ] T7.4-1 模型生命周期骨架：审批状态机 + 注册表 + 能力描述向量化 + 审批/路由 API（建表见 T0-3，种子数据见 T0-4）

**验收**：
```bash
pip install -r requirements.txt && cd backend && python run.py   # 启动无报错，日志显示建表 + 种子数据
curl http://localhost:8000/docs                                   # OpenAPI 可用
curl http://localhost:8000/api/models                              # 期望：helmet_v26(active)/wheelhub_v18(pending)/fire_smoke_v12(draft)
curl http://localhost:8000/api/models/active                       # 期望：仅 helmet_v26
curl http://localhost:8000/api/tasks                               # 期望：安全帽/轮毂/烟火 三个种子任务
# 前端：cd frontend && npm run dev，http://localhost:5173 返回 Vite 页面
```

### Phase 1 · 核心闭环补齐（检测能力 + 前端骨架）

**目标**：从"有骨架无能力"升级为"能识别图片/视频/实时流的可交互工作台"。
**前置**：Phase 0 ✅
- [ ] T7.5-1 实现 `BaseDetector` 及 ultralytics 真实现（加载权重推理）
- [ ] T7.5-2 实现 `ZeroShotDetector`（YOLO-World/GroundingDINO，文本提示词）
- [ ] T7.5-3 实现视频文件流水线（抽帧→跳帧→ByteTrack→时序过滤）
- [ ] T7.5-4 实现实时采集（`CameraSource` 抽象 + OBS/USB/RTSP 三类 + 指数退避重连 + WS 推流）
- [ ] T7.6-1 路由接入第 4 级零样本兜底（§5.2/§7.6）
- [ ] T7.12-1..6 前端 6 页面骨架 + `BboxCanvas` + WebSocket hooks + API 封装
- [ ] T7.9-1 推理轨迹数据结构 + 记录中间步骤（基础版）

**验收**：
```bash
# 后端三接口可用（无 GPU 时 StubDetector 先跑通，YOLO 权重可选装）
curl -X POST http://localhost:8000/api/detect/image -F "file=@demo.jpg"
curl -X POST http://localhost:8000/api/detect/video -F "file=@demo.mp4"   # 返回 task_id
curl http://localhost:8000/api/cameras/enumerate                          # 返回本机设备（含 OBS 虚拟摄像头若存在）
# 前端：npm run dev 打开 /detect 页，三种模式页签可见（图片/视频/实时）
# 冒烟测试脚本 scripts/smoke_test.py 通过（§8.1）
```

### Phase 2 · 数据与模型增强（多功能通用化 + 数据闭环）

**目标**：任务开放化 + 数据集/训练/VLM/RAG 四大能力，未知输入可转正为新任务。
**前置**：Phase 1 ✅
- [ ] T7.1-1..4 任务类型开放化（建表）+ 数据集管理（上传/抽帧/去重/划分/版本/导出/聚类预览）
- [ ] T7.2-1..2 标注工作台 + 主动学习
- [ ] T7.3-1..3 训练中心（异步任务 + 指标 WS + 产物进审批流）
- [ ] T7.7-1..2 VLM Provider 抽象（Cloud/Local + 降级）+ prompt 模板按任务生成
- [ ] T7.8-1..3 RAG 知识中枢（四类知识源 + 混合检索 + 入库权限控制）
- [ ] T7.6-2 路由生产化（换 ClipEmbedder + LlmDecider，四级路由完整）
- [ ] T7.4-2 能力描述草稿自动生成从训练产物接管（task_id 关联）
- [ ] T7.12-5 模型库/数据集/训练页联调

**验收**：
```bash
# 任务开放：创建自定义任务 → 数据集 → 标注确认 → 训练提交 → 产物进审批 → 审批通过 → 路由候选可见
curl -X POST http://localhost:8000/api/tasks -H "Content-Type: application/json" \
     -d '{"name":"包装缺陷","task_desc":"识别包装破损/污渍/压痕","categories":[{"name":"broken"},{"name":"stain"},{"name":"dent"}]}'
curl -X POST http://localhost:8000/api/datasets -H "Content-Type: application/json" -d '{"name":"包装v1","task_id":<新task_id>}'
# ... 上传 → 确认标注 → split → version → training jobs → models 出现 draft → approval → active
# 全链路脚本 scripts/e2e_phase2.py 通过（§8.2）
# VLM 双通道：GET /api/analysis/providers 可切换；云端不可用时自动降级本地
```

### Phase 3 · 运营能力（告警/工单/运维）

**目标**：从"检测系统"变"管理系统"。
**前置**：Phase 2 ✅
- [ ] T7.11-1..3 告警分级去重 + 多通道推送（WS/企微/短信）+ 工单闭环
- [ ] T7.13-1..3 健康检查 + 模型漂移检测（置信度分布监控 → 建议重训）+ 容器化

**验收**：`POST /api/detect/image` 命中确认目标 → 自动生成 Alert（冷却去重生效）→ 转工单 → 流转 closed；`GET /api/health` 返回各组件状态；漂移检测脚本输出报告。

### Phase 4 · 平台生态（MCP/Agent 构建/开放）

**目标**：多 Agent 协作、能力对外开放。
**前置**：Phase 3 ✅
- [ ] T7.10-2..3 MCP 工具网关（六组工具 + 最小权限挂载 + 审计）
- [ ] T7.9-2 多 Agent 编排（路由/检测/分析/报告/运维）+ 推理轨迹可视化
- [ ] T7.12-7 Agent 构建画布（ReactFlow）
- [ ] 外部连接器（企微告警推送第一批；腾讯文档报告第二批）

**验收**：`/api/mcp/tools/list` 返回 ≤10 工具；配置 Agent 工具子集后，越权工具调用返回 403 且写入 `mcp_tool_audit`；对话页显示多 Agent 步骤轨迹。

---

## 7. 功能模块实现规格（按此构建，逐模块交付）

> 每个模块包含：**功能定义**（构建什么）、**为什么这么设计**（设计动机与取舍）、**关键规格**（实现要点）、**实现任务**（T 编号，对应 §6 勾选框）。

### 7.1 数据集管理（Phase 2）

**功能定义**：管理任意任务的训练数据：上传（图片/视频）→ 抽帧 → 去重 → 标注 → 划分 → 版本 → 导出训练包。

**为什么这么设计**：
- **训练数据是模型质量的源头**，必须有一等公民的管理设施，否则"数据反哺"闭环无从谈起。
- **任务开放**（task_types/categories 表，非枚举）：因为项目定位是"任何可训练任务都能接入"，写死类别枚举等于掐死扩展性。
- **素材与标注分离存储**：原始图片永不改动，标注独立存放，可回溯、可重标、可审计。
- **数据集版本不可变**（被训练引用即锁定）：保证训练可复现——同一版本号永远对应同一批数据。
- **未知图片聚类预览**：多功能定位的落地——上传未知类别图片 → 零样本粗检 + 自动聚类（感知哈希/CLIP 相似度分组）→ 用户确认类别名 → 生成新任务数据集草稿，让"新类别"从数据侧进入系统。

**关键规格**：
- 视频 N 帧/秒抽帧 + 感知哈希去重（剔除近似帧，避免冗余样本造成训练偏差）
- 导出格式适配：内部统一 COCO，按需导出 YOLO txt——未来接入其他检测框架零改动

**实现任务**：
- T7.1-1 建表（§4.1/4.2）+ `backend/app/datasets/` 包（schemas.py/routes.py/service.py）
- T7.1-2 上传接口（图片/视频 multipart → 异步抽帧任务 → 去重入库）
- T7.1-3 划分/版本/导出接口
- T7.1-4 未知图片聚类预览接口（`POST /api/datasets/{id}/cluster-preview`）

### 7.2 数据标注与主动学习（Phase 2）

**功能定义**：标注工作台（画框/打类目/确认）+ 主动学习（自动挑"最该人工标"的样本）+ SAM 半自动标注。

**为什么这么设计**：
- **标注成本是 AI 落地最大瓶颈**，纯手工逐张画框不可持续。
- **主动学习把人力花在最难的样本上**：不确定性三指标（最低置信度/类别熵/预测分歧度）挑出的样本最能提升模型，比随机采样效率高一个量级。
- **SAM 半自动标注**：点一下目标 → SAM 掩膜 → 转检测框，把"画框"降为"点选"，标注成本再降一个量级。
- **人工确认（confirm）后才进训练集/案例库**：与 §7.8 入库权限控制一致——未确认数据不污染任何下游。

**实现任务**：T7.2-1 标注 CRUD + 确认接口；T7.2-2 主动学习任务（异步：模型跑未标注池 → 算不确定性 → top-K 清单）

### 7.3 训练中心（Phase 2）

**功能定义**：异步训练任务（提交/监控/停止）、实时指标曲线、GPU 调度、产物自动进审批流。

**为什么这么设计**：
- **训练是分钟到小时级的长任务**，必须异步化（提交返回 job_id + WS 推送进度），否则会阻塞整个工作台。
- **训练从命令行变成工作台一等公民**：非算法工程师也能点按钮训练，是"多功能工作台"能自成长的前提。
- **产物自动进审批流（生成能力描述草稿 → draft）**：这是"新模型被系统认识"的唯一起点——训练完不等于能用，必须过人工审批（§7.4），保证系统里只有受控的模型。
- **状态机硬约束**（queued→running→completed/failed/canceled）：失败保留日志可重试，不丢上下文。

**实现任务**：T7.3-1 任务 CRUD + 状态机；T7.3-2 ultralytics 训练进程执行器 + 指标回传；T7.3-3 产物（best.pt + 报告）→ 审批流接入

### 7.4 模型生命周期（Phase 0 骨架 + Phase 2 完善）

**功能定义**：模型审批状态机（draft→pending→active|rejected）+ 能力描述向量化 + 注册表（只认 ACTIVE）。

**为什么这么设计**：
- **生产环境模型必须受控**：训练产物直接上线会失控，审批是"人把关"的强制闸门；非法迁移硬拦截 + 全程留痕保证流程严肃性。
- **驳回模型永不进路由**：被拒的模型不污染候选池，这是路由可信度的底线。
- **能力描述 = 路由质量源头**：模型注册时带自由文本（检测什么/适用场景/类别列表/精度），向量化后成为路由决策依据（§7.6 第 1 级粗筛比对对象）。描述质量直接决定自动路由准不准，所以人工可编辑且编辑后重新向量化。
- **新模型 = 注册一条记录**：路由代码零改动，这是"多功能可扩展"的机制保证。

**实现任务**：T7.4-1 审批状态机 + 注册表 + 能力描述向量化（Phase 0 骨架，含种子数据）；T7.4-2 能力描述草稿自动生成接入训练产物（Phase 2，§7.3 衔接）

### 7.5 检测推理层（Phase 1 主战场）

**功能定义**：插件化检测器（YOLO 真实现 + 零样本兜底）+ 视频流水线 + 实时采集（OBS/USB/RTSP）。

**插件化结构**：
```
BaseDetector(load_model / detect / warmup / unload)
 ├── HelmetDetector/WheelhubDetector/FireSmokeDetector  ← 示例任务（注册权重+配置）
 ├── ZeroShotDetector   ← 内置通用：YOLO-World/GroundingDINO 按文本提示词检测任意类别
 └── DetectorManager    ← 注册中心 + 懒加载 + LRU 显存卸载 + 路由分发
```

**为什么这么设计**：
- **多任务多模型必须插件化**：真实场景同时有安全帽/轮毂/烟火等模型，新增类型 = 写一个子类 + 一份权重 + 一份配置，零侵入、互不影响。
- **显存是稀缺资源**：多模型不能同时常驻 → 懒加载 + LRU 卸载（显存不足时卸载最久未用的模型）。
- **统一 `Detection` 输出**：上层（路由/VLM/告警）无差别消费所有检测器结果，这是"可插拔"的技术前提。
- **内置零样本检测器**：多功能定位的兜底——遇到没训练过的类别，YOLO-World/GroundingDINO 用文本提示词也能检出目标，保证"任何输入都有结果"。

**关键规格**：
- 视频流水线：抽帧 → 每 N 帧检测 1 次（跳帧，默认 N=3）→ 中间帧 ByteTrack 跟踪插值 → 时序过滤（连续 M 帧命中才确认，M 可配）→ 确认后触发告警/VLM/事件（省算力 + 防单帧误报）
- 实时采集：`CameraSource` 接口（`open/read_frame/release/is_opened/set_property`）；`LocalCameraSource`（Windows DirectShow 枚举 `CAP_DSHOW`，按名称匹配 OBS Virtual Camera，失败降级 `CAP_ANY`）+ `NetworkCameraSource`（RTSP/RTMP ffmpeg 拉流 + 指数退避重连 1s→2s→4s…上限 30s）+ `CameraManager`（枚举/测试/状态）
- WS 推流：检测后帧（叠加 bbox）JPEG 编码 10-15fps + 结构化结果；smooth/hd 带宽自适应（降推流质量，**检测仍本地全帧率**）；首帧路由 + 后续沿用；多用户连同一路流：服务端单实例采集、多路 WS 分发

**实现任务**：
- T7.5-1 真 `BaseDetector`（ultralytics）+ `manager._build_detector()` 按权重构造；保留 `StubDetector` 供无 GPU 环境
- T7.5-2 `ZeroShotDetector`（提示词来自任务类别列表/用户输入）
- T7.5-3 视频流水线服务 `backend/app/detection/pipeline.py`（ByteTrack 或自实现 IoU 跟踪；时序过滤）
- T7.5-4 `backend/app/detection/camera/`（camera_source.py / camera_manager.py）+ WS 推流端点（§5.3）
- （路由侧第 4 级零样本接入由 T7.6-1 承接）

### 7.6 Agent 自动路由（Phase 1 四级 + Phase 2 生产化）

**功能定义**：上传图片后自动决定"该用哪个模型"——四级混合路由，任何输入都有结果。

**四级路由**：
```
第1级 CLIP 粗筛：图片编码 vs ACTIVE 能力向量 → top-3
第2级 决策器：CLIP相似度 + 用户文本意图 + 对话上下文 + 长记忆 + 候选能力描述
第3级 YOLO 执行 + 回退：置信度校验 → 全低换候选重试(≤2次)
第4级 零样本兜底：无候选/仍低 → ZeroShotDetector 框目标 + VLM 描述 → "疑似新类别"引导
```

**为什么这么设计**：
- **用户不该关心选模型**：质检员上传图只想得到结论，路由把"模型选择"从人脑移到系统。
- **CLIP 粗筛毫秒级、零成本**，先用向量相似度缩到 top-3，避免每次都把所有模型跑一遍（省算力）。
- **LLM 决策补粗筛的盲区**：图片语义与能力描述不一定向量对齐（如"看看这个有没有脏污"），用户意图/上下文/记忆注入后决策更准。
- **四级回退保证鲁棒**：候选池 = ACTIVE 注册模型 + 内置零样本，注册表为空/无匹配**永不抛错**——未知输入走零样本兜底并引导转正，这是"多功能、未知数据集"定位的核心承诺。

**关键规格**：决策输入五要素（CLIP 相似度/用户文本意图/对话上下文/长记忆/候选能力描述）；失败回退链：换候选 → 图检索 RAG 历史案例 → 零样本兜底；视频/实时：首帧路由一次，后续沿用。

**实现任务**：
- T7.6-1 第 4 级零样本兜底接入（Phase 1）：候选池追加内置零样本标记；无候选/重试仍低时输出 `detect_zero_shot(image, prompt=任务类别列表或用户提示词)` 分支；结果标记 `zero_shot_used=true`，经 T7.5-2 的 ZeroShotDetector 执行
- T7.6-2 生产化（Phase 2）：`ClipEmbedder`（open_clip）+ `LlmDecider._call_vlm()`（对接 §7.7 Provider）

### 7.7 多模态分析 VLM（Phase 2）

**功能定义**：对检测结果做语义分析——严重度/成因/处置建议，输出结构化 `FusedResult`。

**为什么这么设计**：
- **YOLO 只有坐标，业务要的是结论**："检测到 no_helmet 0.93" 和"高处作业未戴安全帽，高风险，应立即整改"之间的差距就是 VLM 的价值。
- **Provider 抽象防锁定**：`VLMProvider.analyze(image, prompt)` 统一接口，云端（通义千问VL/GPT-4o）与本地（Qwen2.5-VL）可切换；云端故障自动降级本地，**生产不中断**。
- **prompt 模板按任务生成**：task_desc + categories 自动生成分析模板（高级用户可编辑），保证"任何新任务"都有可用的分析提示词，不用写代码。
- **成本控制**：视频流每 30 帧才调一次、只分析确认帧——VLM 按 token 计费，不能每帧都调。

**实现任务**：T7.7-1 Provider 抽象 + Cloud/Local 实现 + 降级策略；T7.7-2 模板引擎（按任务）+ `POST /api/analysis/image` 全链路（路由→检测→VLM→融合）

### 7.8 RAG 知识中枢（Phase 2）

**功能定义**：四类知识源 + 图文混合检索 + 入库权限控制，为 VLM 提供依据、为路由提供经验。

**四类知识源**：规范文档库（法规/标准/规程）、历史案例库（图文对，**不限任务场景，跨任务软加权互参**）、模型注册表（能力描述+代表示例图，由 7.4 自动同步）、告警预案库（处置流程/上报话术/责任人）。

**混合检索**：
```
查询(文本或图片) → 双塔编码(图像CLIP/文本bge-m3, 同一向量空间)
→ 向量 top-50 + BM25 top-50 → 加权合并 → bge-reranker 重排 top-5 → 注入 prompt/决策
```

**为什么这么设计**：
- **VLM 会幻觉，必须给依据**：`FusedResult.references` 强制携带检索来源，结论可溯源、可复核——工业采信的前提。
- **历史案例是组织经验**：每次人工确认的判定/处置都是宝贵先例，入库后新人可以直接对照"当时怎么判的"。
- **跨任务软加权**：轮毂"脏污"与食品"异物"可互参（相似机理），不做 task_type 硬过滤，只按相似度软加权——多功能平台的知识共享红利。
- **入库权限控制是硬规则**：只有人工确认的结果能入库；Agent 自动结论只进待确认区（cases_pending），确认后转正——防止系统自我污染。

**实现任务**：T7.8-1 建表 + 分块入库/删除（含向量）；T7.8-2 混合检索服务（numpy 起步向量，接口与 Milvus 对齐）；T7.8-3 待确认区 + confirm 转正流程（转正时同步长记忆）

### 7.9 Agent 编排与对话长记忆（Phase 1 基础 + Phase 4 完善）

**功能定义**：多 Agent 分工协作（路由/检测/分析/报告/运维）+ 跨会话长记忆 + 推理轨迹可视化。

**为什么这么设计**：
- **一次"分析这张图"包含多步**（选模型→检测→查知识→VLM→生成报告），需要一个调度中枢按序编排并传递中间结果——这就是 Agent。
- **长记忆让系统越用越懂业务**：路由经验、用户偏好、业务结论跨会话沉淀，下次决策自动注入（检索评分 = 0.7×向量 + 0.2×重要性 + 0.1×时间衰减）——"越用越准"的记忆基础。
- **推理轨迹可视化**：`GET /api/agent/trace/{id}` 回放每步（决策依据/工具调用/VLM 所见）——工业场景"为什么得出这个结论"必须可查。

**多 Agent 职责**：路由 Agent（get_models/knowledge_search）、检测 Agent（detect_image/detect_video）、分析 Agent（knowledge_search/detect_image）、报告 Agent（knowledge_search/docs_report）、运维 Agent（model_deploy/health_check）——工具经 MCP 网关最小权限挂载（§5.10）。

**实现任务**：T7.9-1 轨迹数据结构 + 记录中间步骤（Phase 1 与对话页一起做基础版）；T7.9-2 多 Agent 编排执行器（Phase 4，依赖 MCP）

### 7.10 MCP 工具网关（Phase 1 鉴权 + Phase 4 网关）

**功能定义**：把工作台能力封装成 MCP 工具（六组），多 Agent 按最小权限挂载，统一审计。

**为什么这么设计**：
- **能力要开放给 Agent 生态**：检测/训练/知识/告警/运维/报告封装成工具后，任何 Agent 都能复用，不局限于内置工作台。
- **最小权限挂载**：每个 Agent 只注入被授权工具（如报告 Agent 不给训练工具），越权调用 403——安全底线。
- **统一审计**：每次工具调用落 `mcp_tool_audit`（谁调的、调了什么、结果如何），可追溯、可复盘。

**三条铁律**：① 工具描述 = 路由质量（写清做什么/参数/返回/场景）② 长任务必须异步化 ③ 写操作权限门禁。

**外部连接器（可选按需）**：企业微信（告警推送，第一批）、腾讯文档（报告，第二批）、短信网关（高等级兜底）、IoT 平台（联动停线）。

**实现任务**：T7.10-1 鉴权框架（Phase 0 的 T0-7 已交付，供全模块复用）；T7.10-2 MCP Server 封装六组工具（内部调用走已有 API）；T7.10-3 Agent 工具子集配置 + 审计

### 7.11 告警与工单（Phase 3）

**功能定义**：检测命中目标 → 分级去重 → 多通道推送 → 工单闭环 → 复盘回流。

**为什么这么设计**：
- **检测结果要变成可处置的动作**："画个框"不是终点，必须触发告警、派工单、有人负责关闭——否则系统无业务价值。
- **分级去重防打扰**：同 track_id 冷却期内只报一次，低等级合并摘要，紧急才短信+电话——告警疲劳是监控系统失效的头号原因。
- **预案即答**：告警时检索 RAG 预案库直接输出处置流程/上报话术/责任人——把"经验"即时变成"行动"。
- **工单闭环 + 复盘回流**：`open→assigned→processing→review→closed`（超时自动升级），处置结果回流 RAG 案例库——运营数据变成下个模型的知识。

**实现任务**：T7.11-1 告警创建/去重/分级 + WS 推送；T7.11-2 多通道分发器（先 WS + 日志通道，企微/短信留适配器位）；T7.11-3 工单 CRUD + 状态机 + 超时升级

### 7.12 Web 工作台前端（Phase 1 骨架 + 各阶段完善）

**功能定义**：6 页面 Web 工作台——数据集管理 `/datasets`、训练中心 `/training`、模型库 `/models`、识别工作台 `/detect`（图片/视频/**实时**三模式页签）、Agent 构建 `/agent-builder`、对话分析 `/chat`。

**为什么这么设计**：
- **工作台形态让非技术用户全流程可用**：标注、训练、审批、检测、告警都在浏览器完成，不依赖命令行。
- **识别工作台三模式合一**：图片/视频/实时是同一检测能力的三种输入形态，统一交互降低学习成本。
- **推理透明**：对话页显示多 Agent 每一步执行过程（选了哪个模型、为什么、VLM 看到了什么）——工业采信的前提。
- **状态驱动 UI**：模型审批按钮按状态机显示（draft 显示"提交审批"，active 显示"可路由"），用户永远知道下一步能做什么。

**关键组件**：`BboxCanvas`（图上叠加 bbox+类别+置信度+track_id，支持缩放）；WebSocket hooks（训练指标/实时检测帧/告警推送三路复用）；实时检测页（采集源下拉 → 连接测试 → 开始检测 WS 接流 → 预览区左上角模型/FPS/分辨率 → 告警面板（证据帧缩略图、一键转工单/截图存档）→ 停止/断线重连角标）；零样本兜底提示卡片（无匹配/置信度全低时显示"疑似新类别"：零样本框选结果 + VLM 描述 + 一键创建新任务）。

**实现任务**：T7.12-1 Vite+TS 工程 + 路由 + 布局；T7.12-2 API 封装（axios）+ WS hooks；T7.12-3 `BboxCanvas`；T7.12-4 识别工作台（图片/视频/实时三模式）；T7.12-5 模型库/数据集/训练页（Phase 2 联调）；T7.12-6 对话分析页（推理轨迹）；T7.12-7 Agent 构建画布（Phase 4，ReactFlow）

### 7.13 部署与运维（Phase 3+）

**功能定义**：健康检查、模型漂移检测、容器化部署形态。

**为什么这么设计**：
- **生产可用需要可观测性**：模型加载/GPU 显存/队列深度/VLM 连通性一目了然，故障先于用户发现。
- **漂移检测是"模型越用越准"闭环的关键**：线上置信度分布持续下滑说明数据变了 → 自动建议重训——否则模型会悄悄失效。
- **分层部署形态**：开发 Docker Compose、内网生产 Compose/K8s + GPU 节点（训练/推理分离）、边缘 ONNX/TensorRT + Jetson——同一套代码适配不同算力预算。

**实现任务**：T7.13-1 `GET /api/health` + 组件状态上报；T7.13-2 漂移检测服务（采样线上置信度分布 → 统计检验/阈值 → 报告）；T7.13-3 `infra/docker-compose.yml`（redis/minio/postgres 可选 profile）

---

## 8. 端到端验收场景（转可执行测试）

### 8.1 一次识别请求（Phase 1 验收，`scripts/smoke_test.py`）

```python
# 伪码：脚本须覆盖以下断言
r = client.post("/api/route/image", files={"file": demo_jpg}, data={"session_id":"s1","user_text":"看看这个轮毂"})
assert r.status_code == 200
assert "model" in r.json() and "detections" in r.json()
assert r.json().get("zero_shot_used") in (True, False)      # Phase 1 起恒有结果，不抛错
```

### 8.2 未知输入转正链路（Phase 2 验收，`scripts/e2e_phase2.py`）

```
上传未知类别图 → /api/route/image zero_shot_used=true → VLM 描述 → 前端"疑似新类别"
→ 人工确认 → 自动生成数据集草稿（正样本 crop + 视觉相似负样本）
→ 训练(§7.3) → 审批注册(§7.4) → 再次上传同图 → 路由直接命中新模型（不再走零样本）
```

### 8.3 实时检测链路（Phase 1 验收）

```
选择采集源 → /api/cameras/{id}/test 返回 ok → /api/detect/live/start 得 stream_id
→ WS 订阅收到 type=frame（10-15fps）与 type=result
→ 注入一个已知告警目标 → 收到 type=result 且 alert 生成（§8.4 联动）
→ /api/detect/live/{stream_id}/stop → 采集释放
```

### 8.4 数据闭环（Phase 2/3 验收）

```
数据集版本 → 训练任务 → metrics WS 出曲线 → completed → models 出现 draft
→ approve → active → /api/route/candidates 可见
→ 推理命中 → alert 创建（冷却去重生效）→ ticket 流转 closed → 复盘入 RAG cases
```

---

## 9. 风险与约束

| 风险 | 应对（构建时落实） |
|------|------|
| RAG 知识库被低质量数据污染 | 入库权限控制是硬规则（§7.8）：只有人工确认可入库 |
| 多模型并发 GPU 显存溢出 | 懒加载 + LRU 卸载 + 训练/推理分离部署 |
| VLM 幻觉错误结论 | 强制 RAG 引用来源（FusedResult.references）+ 轨迹可视化 + 人工确认闭环 |
| 工具过多 Agent 选错工具 | MCP 初期 ≤10 个，命名空间分组，描述精修 |
| 视频流算力不足 | 跳帧 + 跟踪 + 只对确认帧调 VLM |
| 审批流形同虚设 | 状态机硬拦截 + 全量审计 + AB 对比辅助 |
| 模型过时 | 漂移检测 + 主动学习回流 + 定期重训（Phase 3） |
| 摄像头断流/设备占用 | 指数退避重连 + 前端"连接中"角标 + 设备占用明确报错 |
| 未知类别漏检 | 零样本兜底保证任何输入有结果；确认后转正新任务 |
| 零样本精度低于训练模型 | 零样本只做兜底与发现，不替代注册模型；确认后立即转正训练 |
| 案例库跨任务误召回 | 按图搜案例不做 task_type 硬过滤，只软加权；展示标注来源任务与相似度 |
| 推流带宽不足 | smooth/hd 模式降推流质量，检测仍全帧率执行 |
| OBS/驱动兼容性 | 采集源抽象封装 OpenCV 后端差异，枚举失败降级 CAP_ANY |
| 训练耗时不可控 | 异步任务 + 状态机 + 可停止；超参模板预置快速/标准/高精度三档 |

---

## 10. 关联文档

| 文档 | 用途 |
|------|------|
| `AGENTS.md` | harness 自动读取的入口：定位/规则/命令速查 |
| `README.md` | 项目概览（目标能力）+ 文档导航；**随构建进度同步标记 ✅** |
| `IMPROVEMENT_PLAN.md` | 改进与扩展方案 27 项（近期 1-9 中 **1-4 为多功能通用化改造，随 Phase 2 优先实施**；中期含按图搜案例/未知类别转正；实时 24-27 随 Phase 1 实时落地后跟进）；其"依赖"列编号沿用 v1.2 的 4.x = 本文 §7.1-7.13 |

---

*文档完（v2.1，从 0 构建版 · Agent Edition）。模块编号映射：v2.1 §7.x ⇔ v1.2 §4.x（7.1=4.1 数据集 … 7.13=4.13 部署运维）。*
