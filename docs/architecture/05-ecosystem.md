# 05 · E 平台生态域（Phase 4）

> 对应 PROJECT_SKELETON.md §7.10（MCP 工具网关）、§7.9（Agent 编排与长记忆）、§7.12（画布）、外部连接器。
> 目标：多 Agent 协作、能力对外开放。

## 1. MCP 工具网关（mcp/）

**六组工具（初期总数 ≤10，命名空间分组）**：

| 命名空间 | 工具 |
|---------|------|
| `detect.*` | detect_image / detect_video / get_models |
| `train.*` | start_training / training_status / stop_training |
| `knowledge.*` | knowledge_search / case_add / case_confirm |
| `alert.*` | alert_dispatch / ticket_create / ticket_status |
| `ops.*` | model_deploy / health_check / list_devices |
| `report.*` | docs_report / export_report |

**三条铁律**：① 工具描述 = 路由质量（写清做什么/参数/返回/场景）② 长任务异步化 ③ 写操作权限门禁
**最小权限挂载**：每个 Agent 只注入被授权工具（`POST /api/mcp/agents/{agent_id}/tools`），越权调用 403
**统一审计**：每次调用落 `mcp_tool_audit`（谁调的/调了什么/结果）

## 2. 多 Agent 编排（agent/）

| Agent | 挂载工具 |
|-------|---------|
| 路由 Agent | get_models / knowledge_search |
| 检测 Agent | detect_image / detect_video |
| 分析 Agent | knowledge_search / detect_image |
| 报告 Agent | knowledge_search / docs_report |
| 运维 Agent | model_deploy / health_check |

- 推理轨迹：`GET /api/agent/trace/{id}` 回放每步（决策依据/工具调用/VLM 所见）
- 长记忆：跨会话沉淀，检索评分 = 0.7×向量 + 0.2×重要性 + 0.1×时间衰减

## 3. Agent 构建画布（T7.12-7）

ReactFlow 可视化编排 Agent 流程节点（路由→检测→分析→报告），拖拽连线生成执行图。

## 4. 外部连接器（可选按需）

企业微信（告警推送，第一批）→ 腾讯文档（报告，第二批）→ 短信网关 → IoT 平台（联动停线）

## 5. 验收（Phase 4）

```
/api/mcp/tools/list 返回 ≤10 工具；越权工具调用 403 且写 mcp_tool_audit；
对话页显示多 Agent 步骤轨迹
```
