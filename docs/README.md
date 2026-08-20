# OmniSight-Agent · 构建进度总览

> 本项目文档采用**目录化结构**：本页为唯一入口，打开即可定位"代码做到哪一步"，无需通读全文。
> 状态图例：⬜ 未开始 ｜ 🔨 进行中 ｜ ✅ 完成（审核通过并存档）

## 文档导航

| 文档 | 说明 |
|------|------|
| [`architecture/`](architecture/) | **整体核心构建框架**（分模块设计，按能力域拆分） |
| [`build/`](build/) | **实时搭建过程文档**（按阶段分文件，每小步记录状态与存档号） |
| `../AGENTS.md` | 项目执行入口（harness 自动读取） |
| `../PROJECT_SKELETON.md` | 从 0 构建文档 v2.1（唯一权威规范） |

## 全局进度表

| 阶段 | 模块 | 步骤数 | 完成 | 进行中 | 未开始 | 最近存档 |
|------|------|--------|------|--------|--------|----------|
| Phase 0 | A 平台底座（core/鉴权/模型生命周期/种子数据） | 8 | 8 | 0 | 0 | 存档6 ✅ |
| Phase 1 | B 视觉检测域（检测器/零样本/视频/实时/路由/前端骨架） | 12 | 0 | 0 | 12 | — |
| Phase 2 | C 数据闭环域（数据集/训练/VLM/RAG/路由生产化） | 11 | 0 | 0 | 11 | — |
| Phase 3 | D 运营闭环域（告警/工单/漂移/运维） | 6 | 0 | 0 | 6 | — |
| Phase 4 | E 平台生态域（MCP/多Agent/画布/连接器） | 5 | 0 | 0 | 5 | — |

## 当前焦点

- **当前阶段**：Phase 1（核心闭环补齐：真 YOLO 检测 + 零样本 + 视频/实时 + 前端骨架）
- **当前步骤**：T7.5-1 BaseDetector + UltralyticsDetector（⬜ 待开始）
- **当前分支**：`phase1-detection`（Phase 0 的 `phase0-foundation` 已合并 main）
- **最近存档**：存档6（Phase 0 完成）

## 存档记录

| 存档 | 内容 | 分支 | 状态 |
|------|------|------|------|
| first commit | 项目基础文档 + README + .gitignore | main | ✅ 已推送 GitHub |
| 存档1 | 文档目录化落盘（architecture 5份 + build 5份 + 总览） | phase0-foundation | ✅ 已推送 |
| 存档2 | T0-1 目录结构（12 包 + frontend/data/scripts/infra） | phase0-foundation | ✅ 已推送 |
| 存档3 | T0-2 requirements.txt（进度保存，待 pip install 与审核） | phase0-foundation | ✅ 已推送 |
| 存档4 | T0-2 依赖安装完成（conda omnisight，依赖复检全过） | phase0-foundation | ✅ 已推送 |
| 存档5 | T0-3 第一步 models.py（28 表 ORM，验证通过） | phase0-foundation | ✅ 已推送 |
| 存档6 | Phase 0 完成（后端骨架+种子+鉴权+前端骨架，验收通过） | phase0-foundation | ✅ 已推送 |
