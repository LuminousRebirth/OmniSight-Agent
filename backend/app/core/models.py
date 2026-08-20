"""数据库 ORM 模型：28 张表（PROJECT_SKELETON.md §4 权威映射）。

实现约定（docs/architecture/07-db-schema.md）：
- 时间戳：TEXT ISO8601 UTC，统一 now_utc() 生成
- JSON 语义字段：SQLAlchemy JSON 类型（SQLite 自动存 TEXT，Python 侧透明）
- 布尔：INTEGER 0/1（SQLite 无原生 BOOL）
- 外键：明细表 CASCADE，可空 FK SET NULL；外键列一律建索引
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now_utc() -> str:
    """ISO8601 UTC 时间戳（全项目统一时间表示）"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Base(DeclarativeBase):
    """全部 ORM 模型的声明式基类"""


# ── 任务组（§4.1）───────────────────────────────────────────

class TaskType(Base):
    """任务 = 一类检测目标，自由创建（多功能定位基石）"""
    __tablename__ = "task_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    task_desc: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")


class Category(Base):
    """类别字典（标注 + 零样本提示词复用）"""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task_types.id"), index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    aliases: Mapped[list] = mapped_column(JSON, default=list)  # 别名数组
    description: Mapped[str | None] = mapped_column(Text)


# ── 数据集组（§4.2）─────────────────────────────────────────

class Dataset(Base):
    """数据集（素材与标注分离存储）"""
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("task_types.id"), index=True)
    version: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="draft")


class ImageItem(Base):
    """数据集素材（原始图片永不改动）"""
    __tablename__ = "image_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    source_video_id: Mapped[int | None] = mapped_column(Integer)


class Annotation(Base):
    """标注（独立于素材存储，可重标可审计）"""
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("image_items.id"), index=True)
    bbox: Mapped[list] = mapped_column(JSON, nullable=False)  # [x1,y1,x2,y2]
    class_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    is_confirmed: Mapped[int] = mapped_column(Integer, default=0)  # 0/1
    annotator: Mapped[str | None] = mapped_column(String)
    confirmed_by: Mapped[str | None] = mapped_column(String)


class DatasetVersion(Base):
    """数据集版本（不可变，被训练引用即锁定）"""
    __tablename__ = "dataset_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    version_no: Mapped[str] = mapped_column(String)
    split_ratio: Mapped[dict] = mapped_column(JSON, default=dict)  # {"train":0.8,...}
    train_ids: Mapped[str] = mapped_column(Text, default="[]")
    val_ids: Mapped[str] = mapped_column(Text, default="[]")
    test_ids: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


# ── 训练组（§4.3）───────────────────────────────────────────

class TrainJob(Base):
    """训练任务（异步，状态机 queued→running→completed/failed/canceled）"""
    __tablename__ = "train_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    dataset_version_id: Mapped[int] = mapped_column(ForeignKey("dataset_versions.id"), index=True)
    base_model_id: Mapped[int | None] = mapped_column(ForeignKey("models.id", ondelete="SET NULL"))
    hyperparams: Mapped[dict] = mapped_column(JSON, default=dict)
    gpu_ids: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="queued", index=True)
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


class TrainMetric(Base):
    """训练指标（逐 epoch 回传）"""
    __tablename__ = "train_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("train_jobs.id", ondelete="CASCADE"), index=True)
    epoch: Mapped[int] = mapped_column(Integer)
    train_loss: Mapped[float] = mapped_column(Float)
    val_loss: Mapped[float] = mapped_column(Float)
    mAP50: Mapped[float] = mapped_column(Float)
    mAP50_95: Mapped[float] = mapped_column(Float)


class TrainArtifact(Base):
    """训练产物（权重 + 报告）"""
    __tablename__ = "train_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("train_jobs.id", ondelete="CASCADE"), index=True)
    weights_path: Mapped[str] = mapped_column(String)
    metrics_report: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


# ── 模型组（§4.4）───────────────────────────────────────────

class Model(Base):
    """模型注册表（只认 active 进路由候选池）"""
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    version: Mapped[str] = mapped_column(String)
    task_id: Mapped[int] = mapped_column(ForeignKey("task_types.id"), index=True)
    weights_path: Mapped[str | None] = mapped_column(String)
    capability_desc: Mapped[str | None] = mapped_column(Text)   # 自由文本能力描述
    capability_vec: Mapped[list | None] = mapped_column(JSON)   # 能力描述向量
    status: Mapped[str] = mapped_column(String, default="draft", index=True)
    approved_by: Mapped[str | None] = mapped_column(String)
    approved_at: Mapped[str | None] = mapped_column(String)


class Approval(Base):
    """审批流水（draft→pending→active|rejected 全程留痕）"""
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(String)  # submit|approve|reject|edit_desc
    operator: Mapped[str] = mapped_column(String)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


# ── 检测组（§4.5）───────────────────────────────────────────

class CameraSource(Base):
    """摄像头源（OBS/USB/RTSP）"""
    __tablename__ = "camera_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)  # obs|usb|rtsp
    uri: Mapped[str] = mapped_column(String)
    resolution: Mapped[str | None] = mapped_column(String)
    fps: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(String)


class DetectionStream(Base):
    """实时检测流会话"""
    __tablename__ = "detection_streams"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("camera_sources.id"), index=True)
    model_id: Mapped[int | None] = mapped_column(ForeignKey("models.id", ondelete="SET NULL"))
    started_at: Mapped[str] = mapped_column(String, default=now_utc)
    ended_at: Mapped[str | None] = mapped_column(String)
    frames_processed: Mapped[int] = mapped_column(Integer, default=0)
    alerts_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="running")  # running|stopped|error


# ── Agent 组（§4.6）─────────────────────────────────────────

class Conversation(Base):
    """对话会话"""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, default=now_utc)
    updated_at: Mapped[str] = mapped_column(String, default=now_utc)


class Message(Base):
    """对话消息"""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("conversations.session_id"), index=True)
    role: Mapped[str] = mapped_column(String)  # user|assistant|tool
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


class Memory(Base):
    """跨会话长记忆（检索评分 = 0.7×向量 + 0.2×重要性 + 0.1×时间衰减）"""
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    memory_type: Mapped[str] = mapped_column(String)  # route_decision|preference|business_conclusion|approval
    content: Mapped[str] = mapped_column(Text)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    embedding: Mapped[list | None] = mapped_column(JSON)  # 向量
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


class MemoryEvent(Base):
    """记忆沉淀事件"""
    __tablename__ = "memory_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    event_type: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


# ── RAG 组（§4.7）───────────────────────────────────────────

class KnowledgeDoc(Base):
    """知识文档（regulation 规范 / case_source 案例源 / alert_plan 预案）"""
    __tablename__ = "knowledge_docs"

    id: Mapped[int] = mapped_column(primary_key=True)
    doc_type: Mapped[str] = mapped_column(String)  # regulation|case_source|alert_plan
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


class KnowledgeChunk(Base):
    """知识分块（含向量）"""
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("knowledge_docs.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(JSON)


class Case(Base):
    """历史案例库（仅人工确认后写入）"""
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_path: Mapped[str] = mapped_column(String)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("task_types.id", ondelete="SET NULL"))
    detection_json: Mapped[dict] = mapped_column(JSON, default=dict)
    vlm_result: Mapped[dict] = mapped_column(JSON, default=dict)
    human_decision: Mapped[str] = mapped_column(Text)
    confirmed_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


class PendingCase(Base):
    """待确认案例区（Agent 自动结论，确认后转正进 cases）"""
    __tablename__ = "cases_pending"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_path: Mapped[str] = mapped_column(String)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("task_types.id", ondelete="SET NULL"))
    detection_json: Mapped[dict] = mapped_column(JSON, default=dict)
    vlm_result: Mapped[dict] = mapped_column(JSON, default=dict)
    human_decision: Mapped[str | None] = mapped_column(Text)
    confirmed_by: Mapped[str | None] = mapped_column(String)
    auto_generated_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


# ── 告警组（§4.8）───────────────────────────────────────────

class Alert(Base):
    """告警（分级 tip/warning/emergency + 冷却去重）"""
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String)  # 模型/检测器名
    level: Mapped[str] = mapped_column(String, index=True)  # tip|warning|emergency
    target_type: Mapped[str | None] = mapped_column(String)
    track_id: Mapped[int | None] = mapped_column(Integer)
    evidence_image: Mapped[str | None] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="open", index=True)  # open|ack|closed


class AlertDispatch(Base):
    """告警分发记录（多通道 ws/wecom/sms）"""
    __tablename__ = "alert_dispatches"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String)  # ws|wecom|sms
    status: Mapped[str] = mapped_column(String)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)


class Ticket(Base):
    """工单（open→assigned→processing→review→closed）"""
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), index=True)
    assignee: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="open")
    priority: Mapped[str | None] = mapped_column(String)
    due_at: Mapped[str | None] = mapped_column(String)
    resolution: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[str | None] = mapped_column(String)


# ── 系统组（§4.9）───────────────────────────────────────────

class User(Base):
    """用户（角色 admin/operator/viewer）"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="viewer")
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


class Role(Base):
    """角色权限表（permissions JSON 数组）"""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_name: Mapped[str] = mapped_column(String, unique=True)
    permissions: Mapped[list] = mapped_column(JSON, default=list)


class AuditLog(Base):
    """审计日志（审批/路由/工具调用/记忆沉淀全留痕）"""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    target: Mapped[str | None] = mapped_column(String)
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, default=now_utc, index=True)


class McpToolAudit(Base):
    """MCP 工具调用审计（谁调的/调了什么/结果）"""
    __tablename__ = "mcp_tool_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[str] = mapped_column(String)
    tool: Mapped[str] = mapped_column(String)
    args: Mapped[dict] = mapped_column(JSON, default=dict)
    result_status: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, default=now_utc)


# ── 全量表清单（供 init_db / 测试引用）─────────────────────
ALL_TABLES: list[type[Base]] = [
    TaskType, Category,
    Dataset, ImageItem, Annotation, DatasetVersion,
    TrainJob, TrainMetric, TrainArtifact,
    Model, Approval,
    CameraSource, DetectionStream,
    Conversation, Message, Memory, MemoryEvent,
    KnowledgeDoc, KnowledgeChunk, Case, PendingCase,
    Alert, AlertDispatch, Ticket,
    User, Role, AuditLog, McpToolAudit,
]
