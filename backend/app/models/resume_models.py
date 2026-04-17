"""SQLAlchemy ORM 模型"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index,
)
from app.models.db import Base


class ResumeFile(Base):
    """简历文件追踪（避免重复处理）"""

    __tablename__ = "resume_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(512), unique=True, nullable=False, comment="PDF 绝对路径")
    file_hash = Column(String(64), nullable=False, comment="SHA256 校验和")
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="状态: pending/processing/done/failed",
    )
    created_at = Column(DateTime, default=datetime.now, comment="发现时间")
    processed_at = Column(DateTime, nullable=True, comment="处理完成时间")


class Resume(Base):
    """解析后的简历数据"""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, nullable=False, comment="关联 resume_files.id")
    name = Column(String(100), nullable=True, comment="姓名")
    email = Column(String(200), nullable=True, comment="邮箱")
    phone = Column(String(50), nullable=True, comment="电话")
    current_title = Column(String(200), nullable=True, comment="当前/最近职位")
    years_exp = Column(String(20), nullable=True, comment="工作年限（如'5'、'3-5'、'3+'）")
    education_json = Column(Text, nullable=True, comment="教育背景 JSON 数组")
    skills_json = Column(Text, nullable=True, comment="技能 JSON 数组")
    work_exp_json = Column(Text, nullable=True, comment="工作经历 JSON 数组")
    summary_text = Column(Text, nullable=True, comment="AI 生成的简历摘要")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否已删除（软删除）")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="上传者")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    __table_args__ = (
        Index("idx_name", "name"),
        Index("idx_title", "current_title"),
    )


class ChatSession(Base):
    """AI 对话记录"""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True, comment="会话标识")
    role = Column(String(20), nullable=False, comment="角色: user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    resume_id = Column(Integer, nullable=True, comment="关联的简历 ID")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
