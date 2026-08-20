# Phase 2 · 数据与模型增强（搭建记录）

> 目标：任务开放化 + 数据集/标注/训练/VLM/RAG 四大能力，未知输入可转正为新任务。
> 详细设计见 `../architecture/03-data-loop.md`；规范以 `../PROJECT_SKELETON.md` §6 为准。

## 步骤清单

### T7.1-1 · 任务类型/数据集建表 + datasets 包（schemas/routes/service）
- 状态：✅ 完成
- 改动文件：datasets/{tasks_routes.py（任务创建 201/重名 409）, datasets_routes.py（数据集 CRUD + 素材分页）}，替换旧 routes.py；scripts/phase2_check.py 自检通过
- 审核：⏳ Phase 2 统一审核
- 存档：-

### T7.1-2 · 数据集上传（图片/视频 → 异步抽帧 → 去重入库）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.1-3 · 划分/版本/导出接口
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.1-4 · 未知图片聚类预览接口
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.2-1 · 标注 CRUD + 人工确认接口
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.2-2 · 主动学习（不确定性采样）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.3-1 · 训练任务 CRUD + 状态机
- 状态：✅ 完成
- 改动文件：training/{routes.py, service.py}（queued→running→completed|failed|canceled，非法迁移 409）+ scripts/training_check.py；自检通过
- 审核：⏳ Phase 2 统一审核
- 存档：-

### T7.3-2 · ultralytics 训练执行器 + 指标回传
- 状态：✅ 完成
- 改动文件：training/service.py（asyncio.to_thread 执行 + 指标写 train_metrics + 数据未接入时占位模式）
- 审核：⏳ Phase 2 统一审核
- 存档：-

### T7.3-3 · 训练产物 → 审批流接入
- 状态：✅ 完成
- 改动文件：training/service.py（产物 TrainArtifact + Model draft 自动生成）
- 审核：⏳ Phase 2 统一审核
- 存档：-

### T7.7-1 · VLM Provider 抽象（通义/OpenAI 兼容/本地 Qwen2.5-VL + 降级）
- 状态：✅ 完成
- 改动文件：vlm/{provider.py, openai_compat.py, dashscope.py, local.py, factory.py, templates.py} + core/config.py（API key 配置）；scripts/vlm_check.py 自检通过（降级链/模板/解析）
- 审核：⏳ Phase 2 统一审核
- 存档：-

### T7.7-2 · prompt 模板引擎 + /api/analysis/image 全链路
- 状态：✅ 完成
- 改动文件：vlm/routes.py（检测→prompt→VLM→FusedResult 融合 + GET /api/analysis/providers）；自检通过
- 审核：⏳ Phase 2 统一审核
- 存档：-

### T7.8-1 · RAG 建表 + 分块入库/删除（含向量）
- 状态：✅ 完成
- 改动文件：rag/{vectorizer.py, store.py, service.py, routes.py}（Milvus Lite 向量库 + DB 双写，分块入库/删除）；scripts/rag_check.py 自检通过
- 审核：⏳ Phase 2 统一审核
- 存档：-

### T7.8-2 · 混合检索服务（向量 + BM25 + 重排）
- 状态：✅ 完成
- 改动文件：rag/service.py hybrid_search（Milvus 余弦 0.6 + 关键词重合 0.4 合并 top-k）；自检命中
- 审核：⏳ Phase 2 统一审核
- 存档：-

### T7.8-3 · 待确认区 + confirm 转正流程
- 状态：✅ 完成
- 改动文件：rag/service.py promote_case + routes（cases_pending → confirm 转正 cases，重复转正 404）；自检通过
- 审核：⏳ Phase 2 统一审核
- 存档：-

### T7.6-2 · 路由生产化（ClipEmbedder + LlmDecider）
- 状态：✅ 完成
- 改动文件：routing/{clip_embedder.py, service.py}（CLIP 图片/文本编码粗筛 top-3 + LLM 决策接 VLM Provider；不可用降级顺序候选）；route_check 自检通过（轨迹含"CLIP 粗筛+决策"）
- 审核：⏳ Phase 2 统一审核
- 存档：-

### T7.4-2 · 能力描述草稿自动生成（训练产物接管）
- 状态：✅ 完成
- 改动文件：training/service.py（run_training 内自动生成 Model draft + capability_desc/向量）
- 审核：⏳ Phase 2 统一审核
- 存档：-

> ⏭️ 按用户指示跳过（待数据接入时补做）：T7.1-2/3/4 数据集上传/划分/导出/聚类预览、T7.2-1/2 标注/主动学习。

## 阶段验收（全部通过才进 Phase 3）

```bash
# 任务开放 → 数据集 → 标注确认 → 训练 → 产物draft → 审批active → 路由候选可见
scripts/e2e_phase2.py 通过
GET /api/analysis/providers 可切换；云端不可用自动降级本地
```
