# 01 · A 平台底座（Phase 0）

> 对应 PROJECT_SKELETON.md §7.4（模型生命周期骨架）、§4 数据模型、§5.1 API。
> 交付顺序：T0-1 → T0-2 → T0-3 → T0-4 → T0-5 → T0-6 → T0-7 → T7.4-1

## 1. 模块构成

| 子模块 | 职责 | 关键文件 |
|--------|------|---------|
| core.database | SQLite 连接封装（可换 PostgreSQL）+ 28 张表定义 | `backend/app/core/database.py`、`models.py` |
| core.security | JWT 鉴权 + 角色校验依赖（admin/operator/viewer） | `backend/app/core/security.py`、`deps.py` |
| core.config | 配置加载（路径/模型权重/Provider 密钥） | `backend/app/core/config.py` |
| model_lifecycle | 审批状态机 + 注册表 + 能力描述向量化 | `backend/app/model_lifecycle/` |
| system | 健康检查占位 | `backend/app/system/` |
| main/run | FastAPI 装配 + 路由注册 + 种子数据注入 | `backend/app/main.py`、`backend/run.py` |

## 2. 数据模型（28 张表，按 §4 分组）

| 组 | 表 |
|----|----|
| 任务 | task_types / categories |
| 数据集 | datasets / image_items / annotations / dataset_versions |
| 训练 | train_jobs / train_metrics / train_artifacts |
| 模型 | models / approvals |
| 检测 | camera_sources / detection_streams |
| Agent | conversations / messages / memories / memory_events |
| RAG | knowledge_docs / knowledge_chunks / cases / cases_pending |
| 告警 | alerts / alert_dispatches / tickets |
| 系统 | users / roles / audit_logs / mcp_tool_audit |

> 字段/类型/约束**以 PROJECT_SKELETON.md §4 为唯一权威**，不得臆造。

## 3. 模型审批状态机

```
draft ──submit──▶ pending ──approve──▶ active
                     │
                     └──reject──▶ rejected   （draft/pending 可 edit_desc 重新向量化）
非法迁移一律 409 硬拦截；全程写 approvals + audit_logs
```

## 4. 种子数据（T0-4 注入）

| 类型 | 数据 |
|------|------|
| 任务 | 安全帽检测 / 轮毂缺陷检测 / 烟火检测（task_types + categories） |
| 模型 | helmet_v26(**active**，真实权重) / wheelhub_v18(pending) / fire_smoke_v12(draft) |
| 用户 | admin / operator / viewer（bcrypt 哈希） |

**helmet_v26 权重注册**（已与用户确认）：
- 路径：`E:\python_code\yolo\runs\models\ppe\HHW_noperson\finetune-4\weights\best.pt`
- 类别：`no_helmet`(idx 0) / `helmet`(idx 1)，imgsz 960
- wheelhub/fire 权重路径占位（pending/draft 不进路由，后续自训/提供后转 active）

## 5. 关键 API（§5.1 模型生命周期）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/models` | 训练产物提交 → draft |
| POST | `/api/models/{id}/approval` | submit/approve/reject/edit_desc，非法迁移 409 |
| GET | `/api/models` / `/api/models/active` | 全部 / 仅 ACTIVE（路由候选池） |
| POST | `/api/models/{id}/desc` | 更新能力描述并重新向量化 |

## 6. 验收（Phase 0）

```bash
cd backend && python run.py          # 建表 + 种子数据无报错
curl http://localhost:8000/api/models             # 3 个种子模型
curl http://localhost:8000/api/models/active      # 仅 helmet_v26
curl http://localhost:8000/api/tasks              # 3 个种子任务
# 前端 npm run dev 可启动
```

## 7. 构建步骤（对应 docs/build/phase0-foundation.md）

T0-1 目录结构 → T0-2 requirements.txt → T0-3 全量建表 → T0-4 main/run + 种子数据 → T0-5 IMPLEMENTATION_NOTES → T0-6 前端骨架 → T0-7 鉴权框架 → T7.4-1 模型生命周期骨架（审批/注册/向量化 API）
