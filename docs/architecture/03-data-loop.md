# 03 · C 数据闭环域（Phase 2）

> 对应 PROJECT_SKELETON.md §7.1-7.3、§7.7、§7.8、§7.6 生产化、§7.4 完善。
> 核心目标：**未知类别 → 确认 → 训练 → 审批 → 注册 → 路由命中** 自成长闭环。

## 1. 数据集管理（datasets/）

- 上传（图片/视频 multipart）→ 异步抽帧（N 帧/秒）→ 感知哈希去重 → 入库
- 内部统一 COCO 格式，按需导出 YOLO txt（未来换框架零改动）
- 划分（train/val/test）→ 版本（不可变，被训练引用即锁定）→ 导出训练包
- 聚类预览：未知图片 → 零样本粗检 + 感知哈希/CLIP 分组 → 用户确认类别名 → 新任务数据集草稿

## 2. 标注与主动学习（Phase 2）

- 标注 CRUD + 人工 confirm（确认后才进训练集/案例库，与 §7.8 权限一致）
- 主动学习：不确定性三指标（最低置信度/类别熵/预测分歧度）→ top-K 待标注清单
- SAM 半自动标注（点选 → 掩膜 → 转检测框，Phase 2 可后装）

## 3. 训练中心（training/）

- 异步任务：提交返回 job_id + WS 推送指标（epoch/train_loss/mAP50…）
- 状态机硬约束：queued→running→completed/failed/canceled
- 产物自动进审批流：训练完成 → 生成 capability_desc 草稿 → POST /api/models → draft
- 超参模板预置：快速/标准/高精度三档

## 4. VLM 多模态分析（vlm/）

```
VLMProvider (analyze(image, prompt) → FusedResult)
 ├── DashScopeProvider     ← 通义千问VL（云端）
 ├── OpenAICompatProvider  ← GPT-4o / OpenAI 兼容接口（云端）
 └── LocalQwenVLProvider   ← Qwen2.5-VL（本地，可选装）
Provider 工厂：配置文件指定默认 + 降级顺序；云端不可用自动降级本地
```

- prompt 模板按任务生成（task_desc + categories 自动拼装，高级用户可编辑）
- 成本控制：视频流每 30 帧调一次、只分析确认帧
- 输出统一 `FusedResult`（detections/severity/description/action/references）

## 5. RAG 知识中枢（rag/）

**四类知识源**：规范文档库 / 历史案例库（跨任务软加权）/ 模型注册表（自动同步）/ 告警预案库

```
查询(文本或图片) → 双塔编码(图像CLIP/文本bge-m3 同一空间)
→ 向量 top-50 + BM25 top-50 → 加权合并 → bge-reranker 重排 top-5 → 注入 prompt/决策
```

**入库权限（硬规则）**：只有人工确认结果能进 cases；Agent 自动结论只进 cases_pending，confirm 后转正并同步长记忆。

## 6. 路由生产化（T7.6-2）

- `ClipEmbedder`（open_clip）：图片/能力描述统一编码
- `LlmDecider._call_vlm()`：对接 §7.7 Provider，输入五要素（CLIP 相似度/用户意图/上下文/长记忆/能力描述）
- 四级路由完整化：CLIP 粗筛 → LLM 决策 → 执行回退 → 零样本兜底

## 7. 验收（Phase 2）

```bash
# 任务开放 → 数据集 → 标注确认 → 训练 → 产物draft → 审批active → 路由候选可见
scripts/e2e_phase2.py 通过
GET /api/analysis/providers 可切换；云端不可用自动降级本地
```
