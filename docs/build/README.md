# 搭建过程总览（Build Log）

> 实时搭建过程文档。**每次编写代码只写一个模块内一个小步骤**，完成即更新对应阶段文件与本文总览。
> 状态图例：⬜ 未开始 ｜ 🔨 进行中 ｜ ✅ 完成（审核通过并存档）
> 存档规则：每关键步骤交用户审核 → 通过后 commit `存档N：<步骤名>` + tag `archive/N` → 推送 GitHub（分支策略：main 主干 + 每 Phase 一个开发分支）。

## 阶段总览

| 阶段 | 文档 | 步骤 | ✅ | 🔨 | ⬜ |
|------|------|------|----|----|----|
| Phase 0 | [phase0-foundation.md](phase0-foundation.md) | 8 | 1 | 0 | 7 |
| Phase 1 | [phase1-detection.md](phase1-detection.md) | 12 | 0 | 0 | 12 |
| Phase 2 | [phase2-data-loop.md](phase2-data-loop.md) | 11 | 0 | 0 | 11 |
| Phase 3 | [phase3-operations.md](phase3-operations.md) | 6 | 0 | 0 | 6 |
| Phase 4 | [phase4-ecosystem.md](phase4-ecosystem.md) | 5 | 0 | 0 | 5 |

## 存档记录

| 存档 | 内容 | 分支 | tag | 状态 |
|------|------|------|-----|------|
| first commit | 项目基础文档 + README + .gitignore | main | — | ✅ 已推送 GitHub |
| 存档1 | 文档目录化落盘（architecture 5份 + build 5份 + 总览） | phase0-foundation | archive/1 | ✅ 已推送 |
| 存档2 | T0-1 目录结构（12 包 + frontend/data/scripts/infra） | phase0-foundation | archive/2 | ✅ 已推送 |
