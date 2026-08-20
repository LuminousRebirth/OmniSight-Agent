# IMPLEMENTATION_NOTES.md — 构建假设与决策记录

> 按构建文档 R11：遇到歧义/踩坑在此记录假设并继续，不阻塞。每个任务追加。

## T0-2 · 依赖与环境
- **passlib 1.7.4 与 bcrypt 4.x 不兼容**（`bcrypt.__about__` 缺失 + 72 字节校验异常）→ 弃用 passlib，**直接使用 bcrypt 库**（`bcrypt.hashpw/checkpw`），requirements.txt 改 `bcrypt>=4.0`。
- requirements.txt 含中文注释会导致 Windows pip 以 GBK 解码失败（`UnicodeDecodeError`）→ 注释统一 **ASCII**。
- 运行环境：**conda `omnisight`**（Python 3.11.15），路径 `D:\Anaconda\envs\omnisight\python.exe`；`D:\Anaconda` 根目录受保护，sandbox 无法写入（用户手动创建环境）。
- 依赖安装走**清华源**：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`。

## T0-3 · 数据模型
- 全 28 表按 `PROJECT_SKELETON.md` §4 映射，见 `docs/architecture/07-db-schema.md`。
- 能力描述向量（capability_vec）：Phase 0 用 **SHA-256 确定性 64 维向量**（`seed._capability_vec`），Phase 2 换 CLIP 向量化工厂。

## T0-4 · 应用装配
- `GET /api/tasks` 在 Phase 0 提供最小端点（§5.4 原属 Phase 2，但 Phase 0 验收命令要求 curl 它），实现于 `backend/app/datasets/routes.py`，Phase 2 完善。
- 种子用户密码统一 `admin123`（开发用，生产必须改）。
- helmet_v26 挂真实权重 `E:\python_code\yolo\runs\models\ppe\HHW_noperson\finetune-4\weights\best.pt`（2 类 no_helmet/helmet，imgsz 960）；wheelhub/fire 权重占位（pending/draft 不进路由）。
- `edit_desc` 也写 `approvals` 流水（R10 留痕），`DescRequest.operator` 默认 `"system"`。
- Windows 控制台 GBK 编码：脚本输出前 `sys.stdout.reconfigure(encoding="utf-8")`。

## Git / 网络
- GitHub 直连不稳定：仓库级配置 `http.proxy=http://127.0.0.1:7897` + `http.sslBackend=openssl`（写入 `.git/config`）；凭据内嵌 remote URL。
- 分支策略：main 主干 + phase0-foundation 开发分支；存档 `存档N` + tag `archive/N`。
