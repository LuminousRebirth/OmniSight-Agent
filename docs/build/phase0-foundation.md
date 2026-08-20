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
- 状态：✅ 完成
- 改动文件：backend/app/core/models.py（28 表 ORM）+ database.py（引擎/init_db/get_db），真实建表 data/omnilight.db 验证 28 张
- 审核：✅ 用户已通过（models.py 第一步）
- 存档：存档5（models.py）+ 存档6（database.py）

### T0-4 · main.py/run.py + 种子数据注入
- 状态：✅ 完成
- 改动文件：backend/app/main.py（lifespan 建表+种子+路由）、backend/run.py、backend/app/core/seed.py（3 任务+3 模型+3 用户幂等注入）、scripts/t0_smoke.py（冒烟脚本全过）
- 审核：✅ Phase 0 已验收
- 存档：存档6（tag: archive/6）

### T0-5 · IMPLEMENTATION_NOTES.md 创建
- 状态：✅ 完成
- 改动文件：IMPLEMENTATION_NOTES.md（passlib/bcrypt 坑、GBK 编码坑、清华源、conda 环境等）
- 审核：✅ Phase 0 已验收
- 存档：存档6（tag: archive/6）

### T0-6 · 前端工程初始化（Vite+React+TS）
- 状态：✅ 完成
- 改动文件：frontend/（package.json/vite.config.ts/tsconfig.json/index.html + src 白蓝风格 6 页路由）；npm install 167 包（--ignore-scripts + 工作区缓存），dev server 验证 HTTP 200
- 审核：✅ Phase 0 已验收
- 存档：存档6（tag: archive/6）

### T0-7 · 鉴权框架（JWT + 角色校验）
- 状态：✅ 完成
- 改动文件：backend/app/core/{config.py, security.py, deps.py}、backend/app/system/auth.py（POST /api/auth/login）；冒烟验证：错误密码 401 / admin 登录 200 / 无 token 401 / 带 token 201
- 审核：✅ Phase 0 已验收
- 存档：存档6（tag: archive/6）

### T7.4-1 · 模型生命周期骨架（审批状态机/注册表/向量化）
- 状态：✅ 完成
- 改动文件：backend/app/model_lifecycle/{schemas.py, service.py, routes.py}（§5.1 全部 6 端点；状态机非法迁移 409；edit_desc 重新向量化+留痕；create 需 admin）
- 审核：✅ Phase 0 已验收
- 存档：存档6（tag: archive/6）

## 阶段验收（全部通过才进 Phase 1）

```bash
cd backend && python run.py
curl http://localhost:8000/api/models         # 3 个种子模型
curl http://localhost:8000/api/models/active  # 仅 helmet_v26
curl http://localhost:8000/api/tasks          # 3 个种子任务
# 前端 npm run dev 可启动
```

## Phase 0 验收结果

- ✅ **用户验收通过**（存档6）：后端启动无报错、/api/models 3 种子模型、/api/models/active 仅 helmet_v26、/api/tasks 3 任务、/docs 200、前端 5173 可访问（左侧折叠导航 + 知识库骨架）
- ✅ scripts/t0_smoke.py 全绿（含审批状态机 409、鉴权 401/201、审批留痕）
