# 07 · 数据库 Schema 设计（28 表 ORM 草案）

> 权威字段定义以 `PROJECT_SKELETON.md` §4 为准；本文档为 **SQLAlchemy 2.0 实现级设计**（类型映射/约定/索引），建表（T0-3）前供审阅。

## 1. 实现约定（SQLAlchemy 2.0）

| 项 | 约定 |
|----|------|
| 声明式基类 | `DeclarativeBase`（`backend/app/core/models.py`） |
| 引擎 | SQLite `sqlite:///data/omnilight.db`（`check_same_thread=False` + `StaticPool` 供 FastAPI 多线程） |
| 时间戳 | TEXT（ISO8601 UTC 字符串），统一 `now_utc()` 工具函数 |
| JSON 字段 | SQLAlchemy `JSON` 类型（SQLite 自动存 TEXT，序列化透明） |
| 布尔 | INTEGER 0/1（SQLite 无原生 BOOL） |
| 向量列 | `capability_vec` / `embedding`：JSON 存 `list[float]` |
| 主键 | INTEGER AUTOINCREMENT |
| 外键 | `ondelete="SET NULL"`（可空 FK）/ `ondelete="CASCADE"`（明细表） |
| 索引 | 外键列一律建索引；高频查询列（status/level/session_id/task_id）建索引 |

## 2. 表清单（28 张 · 9 组）

### 2.1 任务组（多功能定位基石）
**task_types** — 任务 = 一类检测目标，自由创建
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK | |
| name | TEXT | NOT NULL UNIQUE | 任务名 |
| task_desc | TEXT | NOT NULL | 任务描述（路由/模板共用） |
| status | TEXT | DEFAULT 'active' | active/inactive |

**categories** — 类别字典（标注 + 零样本提示词复用）
| 字段 | 类型 | 约束 |
|------|------|------|
| id | INTEGER | PK |
| task_id | INTEGER | FK→task_types.id（索引） |
| name | TEXT | NOT NULL |
| aliases | TEXT | DEFAULT '[]'（JSON 别名数组） |
| description | TEXT | |

### 2.2 数据集组
**datasets**：`id PK, name NOT NULL, task_id FK→task_types, version TEXT, status TEXT DEFAULT 'draft'`
**image_items**：`id PK, dataset_id FK（索引）, storage_path NOT NULL, width INT, height INT, source_video_id INT NULL`
**annotations**：`id PK, image_id FK（索引）, bbox TEXT NOT NULL（JSON [x1,y1,x2,y2]）, class_id FK→categories, is_confirmed INT DEFAULT 0, annotator TEXT, confirmed_by TEXT`
**dataset_versions**：`id PK, dataset_id FK, version_no TEXT, split_ratio TEXT（JSON）, train_ids TEXT, val_ids TEXT, test_ids TEXT, created_at TEXT`（版本不可变）

### 2.3 训练组
**train_jobs**：`id PK, name TEXT, dataset_version_id FK, base_model_id FK→models NULL, hyperparams TEXT（JSON）, gpu_ids TEXT（JSON）, status TEXT DEFAULT 'queued'（queued|running|completed|failed|canceled）, created_by TEXT, created_at TEXT`（status 建索引）
**train_metrics**：`id PK, job_id FK（索引）, epoch INT, train_loss REAL, val_loss REAL, mAP50 REAL, mAP50_95 REAL`
**train_artifacts**：`id PK, job_id FK, weights_path TEXT, metrics_report TEXT, created_at TEXT`

### 2.4 模型组
**models**：`id PK, name TEXT, version TEXT, task_id FK→task_types, weights_path TEXT, capability_desc TEXT, capability_vec TEXT（JSON 向量）, status TEXT（draft|pending|active|rejected）, approved_by TEXT, approved_at TEXT`（status 建索引）
**approvals**：`id PK, model_id FK（索引）, action TEXT（submit|approve|reject|edit_desc）, operator TEXT, comment TEXT, created_at TEXT`

### 2.5 检测组
**camera_sources**：`id PK, name TEXT, source_type TEXT（obs|usb|rtsp）, uri TEXT, resolution TEXT, fps INT, status TEXT, created_by TEXT`
**detection_streams**：`id PK, camera_id FK（索引）, model_id FK NULL, started_at TEXT, ended_at TEXT NULL, frames_processed INT DEFAULT 0, alerts_count INT DEFAULT 0, status TEXT（running|stopped|error）`

### 2.6 Agent 组
**conversations**：`id PK, session_id TEXT UNIQUE, title TEXT, created_at TEXT, updated_at TEXT`
**messages**：`id PK, session_id FK（索引）, role TEXT（user|assistant|tool）, content TEXT, created_at TEXT`
**memories**：`id PK, session_id TEXT, memory_type TEXT（route_decision|preference|business_conclusion|approval）, content TEXT, importance REAL DEFAULT 0.5, embedding TEXT（JSON 向量）, created_at TEXT`
**memory_events**：`id PK, session_id TEXT, event_type TEXT, payload TEXT（JSON）, created_at TEXT`

### 2.7 RAG 组
**knowledge_docs**：`id PK, doc_type TEXT（regulation|case_source|alert_plan）, title TEXT, content TEXT, created_by TEXT, created_at TEXT`
**knowledge_chunks**：`id PK, doc_id FK（索引）, chunk_index INT, content TEXT, embedding TEXT（JSON 向量）`
**cases**（人工确认后写入）：`id PK, image_path TEXT, task_id FK NULL, detection_json TEXT, vlm_result TEXT, human_decision TEXT, confirmed_by TEXT, created_at TEXT`
**cases_pending**（待确认区）：同 cases 字段 + `auto_generated_by TEXT`

### 2.8 告警组
**alerts**：`id PK, source TEXT, level TEXT（tip|warning|emergency）, target_type TEXT, track_id INT NULL, evidence_image TEXT, message TEXT, status TEXT（open|ack|closed）`（level+status 建索引）
**alert_dispatches**：`id PK, alert_id FK（索引）, channel TEXT（ws|wecom|sms）, status TEXT, retry_count INT DEFAULT 0`
**tickets**：`id PK, alert_id FK（索引）, assignee TEXT, status TEXT（open|assigned|processing|review|closed）, priority TEXT, due_at TEXT, resolution TEXT, reviewed_by TEXT`

### 2.9 系统组
**users**：`id PK, username TEXT UNIQUE, password_hash TEXT, role TEXT（admin|operator|viewer）, created_at TEXT`
**roles**：`id PK, role_name UNIQUE, permissions TEXT（JSON 数组）`
**audit_logs**：`id PK, actor TEXT, action TEXT, target TEXT, detail TEXT, created_at TEXT`（created_at 建索引）
**mcp_tool_audit**：`id PK, agent_id TEXT, tool TEXT, args TEXT, result_status TEXT, created_at TEXT`

## 3. 关键设计决策（待确认）

| # | 决策 | 建议 |
|---|------|------|
| D1 | 数据库文件 | `data/omnilight.db`（`data/` 已 gitignore） |
| D2 | 时间戳 | 统一 TEXT ISO8601 UTC，`now_utc()` 生成 |
| D3 | bbox 存储 | annotations.bbox 存 JSON 文本 `[x1,y1,x2,y2]`（§4 契约） |
| D4 | 向量列 | JSON 存 `list[float]`，Phase 2 切 Milvus 时由向量化工厂接管 |
| D5 | 级联 | 明细表（approvals/metrics/chunks）随主表 CASCADE；可空 FK SET NULL |
| D6 | 种子数据 | 3 任务 + 3 模型（helmet active）+ 3 用户，T0-4 注入 |

## 4. 对应实现文件

- `backend/app/core/models.py` — 全部 28 表 ORM（§4 字段逐条映射）
- `backend/app/core/database.py` — 引擎/会话/`init_db()`（create_all + 种子注入钩子）
