"""认证与日志相关 SQLAlchemy ORM 模型"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index,
)
from app.models.db import Base


class User(Base):
    """系统用户"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(200), unique=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="bcrypt 加密密码")
    role = Column(String(20), nullable=False, default="user", comment="角色: admin/user")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    __table_args__ = (
        Index("idx_username", "username"),
        Index("idx_email", "email"),
    )


class LoginLog(Base):
    """登录日志"""

    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="关联用户")
    ip_address = Column(String(45), nullable=True, comment="登录 IP")
    user_agent = Column(String(500), nullable=True, comment="浏览器/设备信息")
    status = Column(String(20), nullable=True, comment="success/failed")
    created_at = Column(DateTime, default=datetime.now, comment="登录时间")

    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_created_at", "created_at"),
    )


class OperationLog(Base):
    """操作日志"""

    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="操作用户")
    action = Column(String(100), nullable=True, comment="操作类型")
    resource_type = Column(String(50), nullable=True, comment="资源类型")
    resource_id = Column(Integer, nullable=True, comment="资源 ID")
    detail = Column(Text, nullable=True, comment="操作详情 JSON")
    created_at = Column(DateTime, default=datetime.now, comment="操作时间")

    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_created_at", "created_at"),
    )


class EmailConfig(Base):
    """邮箱同步配置"""

    __tablename__ = "email_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    imap_server = Column(String(200), nullable=True, comment="IMAP 服务器地址")
    imap_port = Column(Integer, nullable=False, default=993, comment="IMAP 端口")
    email_address = Column(String(200), nullable=True, comment="邮箱地址")
    password_encrypted = Column(String(500), nullable=True, comment="加密后的授权码")
    is_enabled = Column(Boolean, nullable=False, default=False, comment="是否启用")
    download_dir = Column(
        String(512),
        nullable=False,
        default="\\\\192.168.3.30\\简历资料夹",
        comment="下载目录",
    )
    last_sync_at = Column(DateTime, nullable=True, comment="上次同步时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")


class EmailSyncLog(Base):
    """邮箱同步日志"""

    __tablename__ = "email_sync_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_config_id = Column(
        Integer, ForeignKey("email_configs.id"), nullable=True, comment="关联配置"
    )
    total_emails = Column(Integer, nullable=False, default=0, comment="扫描邮件总数")
    new_attachments = Column(Integer, nullable=False, default=0, comment="新附件数量")
    downloaded = Column(Integer, nullable=False, default=0, comment="成功下载数量")
    failed = Column(Integer, nullable=False, default=0, comment="失败数量")
    status = Column(String(20), nullable=True, comment="success/failed/partial")
    message = Column(Text, nullable=True, comment="执行详情")
    created_at = Column(DateTime, default=datetime.now, comment="同步时间")
