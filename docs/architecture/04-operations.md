# 04 · D 运营闭环域（Phase 3）

> 对应 PROJECT_SKELETON.md §7.11（告警与工单）、§7.13（部署与运维）。
> 目标：从"检测系统"变"管理系统"——检测结果变成可处置动作。

## 1. 告警（alerts/）

```
检测命中确认目标 → 创建 Alert（分级 tip/warning/emergency）
→ 同 track_id 冷却去重（冷却期内只报一次，低等级合并摘要）
→ 多通道分发（WS 先行，企微/短信留适配器位）
→ 检索 RAG 预案库 → 输出处置流程/上报话术/责任人（预案即答）
```

- `GET /api/alerts?level&status&page` 列表查询
- `POST /api/alerts/{id}/dispatch` 手动/重发
- WS `/api/alerts/stream` 实时告警推送

## 2. 工单闭环（tickets/）

```
open → assigned → processing → review → closed（超时自动升级）
处置结果回流 RAG 案例库 → 运营数据变成下个模型的知识（复盘回流）
```

- `POST /api/tickets`（alert_id/assignee/priority）
- `PUT /api/tickets/{id}`（action: process/review/close + resolution）
- 状态机非法迁移 409 硬拦截

## 3. 部署与运维（system/）

- `GET /api/health`：模型加载/GPU 显存/队列深度/VLM 连通性组件状态
- **漂移检测**：采样线上置信度分布 → 统计检验/阈值 → 报告 → 建议重训
- 容器化（可选交付）：`infra/docker-compose.yml`（redis/minio/postgres profile）

## 4. 验收（Phase 3）

```
POST /api/detect/image 命中确认目标 → Alert 自动生成（冷却去重生效）
→ 转工单 → 流转 closed；GET /api/health 各组件状态正常；漂移脚本输出报告
```
