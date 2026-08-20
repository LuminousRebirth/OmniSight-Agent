# Phase 0 · 项目骨架与全量建表（搭建记录）

> 目标：从空目录搭建出可运行后端骨架 + 全部 28 张表 + 种子数据 + 鉴权框架 + 前端工程。
> 详细设计见 `../architecture/01-foundation.md`；规范以 `../PROJECT_SKELETON.md` §6 为准。

## 步骤清单

### T0-1 · 初始化目录结构
- 状态：✅ 完成
- 改动文件：backend/app/{core,model_lifecycle,routing,detection,agent,datasets,training,vlm,rag,alerts,mcp,system}/、frontend/、data/、scripts/、infra/（.gitkeep 占位）
- 审核：✅ 用户已通过
- 存档：存档2（tag: archive/2）

### T0-2 · requirements.txt 与依赖安装
- 状态：✅ 完成
- 改动文件：requirements.txt；环境 conda omnisight（Python 3.11.15），deps 清华源安装到位（ultralytics 8.4.123 / pymilvus 3.0.1）
- 审核：✅ 用户已通过（依赖复检全过）
- 存档：存档4（tag: archive/4）

### T0-3 · 全量建表（28 张）
- 状态：⬜ 未开始（schema 草案已就绪：`docs/architecture/07-db-schema.md`，待审阅确认）
- 改动文件：-
- 审核：-
- 存档：-

### T0-4 · main.py/run.py + 种子数据注入
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T0-5 · IMPLEMENTATION_NOTES.md 创建
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T0-6 · 前端工程初始化（Vite+React+TS）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T0-7 · 鉴权框架（JWT + 角色校验）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

### T7.4-1 · 模型生命周期骨架（审批状态机/注册表/向量化）
- 状态：⬜ 未开始
- 改动文件：-
- 审核：-
- 存档：-

## 阶段验收（全部通过才进 Phase 1）

```bash
cd backend && python run.py
curl http://localhost:8000/api/models         # 3 个种子模型
curl http://localhost:8000/api/models/active  # 仅 helmet_v26
curl http://localhost:8000/api/tasks          # 3 个种子任务
# 前端 npm run dev 可启动
```
