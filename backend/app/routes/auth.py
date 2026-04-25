"""认证和管理员相关 API 路由"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.middleware.auth import get_current_user, require_admin
from app.models.auth_models import (
    EmailConfig,
    EmailSyncLog,
    LoginLog,
    OperationLog,
    User,
)
from app.models.db import get_db, engine, SessionLocal
from app.models.schemas import (
    EmailConfigRequest,
    EmailConfigResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UpdateUserRequest,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    log_login,
    log_operation,
    verify_password,
)
from app.services.email_sync import encrypt_password, sync_emails

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["auth"])


def _user_to_dict(user: User) -> dict:
    """将 User 对象转换为不含密码的字典"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


def _email_config_to_dict(cfg: EmailConfig) -> dict:
    """将 EmailConfig 转换为不含密码的响应字典"""
    return {
        "id": cfg.id,
        "user_id": cfg.user_id,
        "imap_server": cfg.imap_server,
        "imap_port": cfg.imap_port,
        "email_address": cfg.email_address,
        "is_enabled": cfg.is_enabled,
        "download_dir": cfg.download_dir,
        "last_sync_at": cfg.last_sync_at,
    }


# ── 认证端点（无需 Token）────────────────────────────────

@router.post("/auth/register", response_model=UserResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册新用户"""
    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度不能少于 6 位",
        )

    existing = db.query(User).filter(
        (User.username == req.username) | (User.email == req.email)
    ).first()
    if existing:
        if existing.username == req.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被注册",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册",
        )

    new_user = User(
        username=req.username,
        email=req.email,
        password_hash=get_password_hash(req.password),
        role="user",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_operation(db, new_user.id, "register", "user", new_user.id, "用户注册")
    return new_user


@router.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """用户登录，支持用户名或邮箱"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")

    candidate = (
        db.query(User)
        .filter(
            (User.username == req.username_or_email)
            | (User.email == req.username_or_email)
        )
        .first()
    )
    if candidate and not candidate.is_active:
        log_login(db, candidate.id, ip_address, user_agent, "failed")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员",
        )

    user = authenticate_user(db, req.username_or_email, req.password)
    if not user:
        if candidate:
            log_login(db, candidate.id, ip_address, user_agent, "failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    log_login(db, user.id, ip_address, user_agent, "success")
    token = create_access_token(data={"sub": user.id})
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=_user_to_dict(user),
    )


# ── 用户端点（需 Token）─────────────────────────────────

@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


@router.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user)):
    """退出登录"""
    return {"message": "退出成功"}


# ── 用户端：邮箱配置（需登录，仅限自己的配置）─────────────────

@router.get("/user/email-configs")
def list_my_email_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的邮箱配置列表"""
    configs = (
        db.query(EmailConfig)
        .filter(EmailConfig.user_id == current_user.id)
        .order_by(EmailConfig.id)
        .all()
    )
    return [_email_config_to_dict(c) for c in configs]


@router.post("/user/email-configs", response_model=EmailConfigResponse)
def create_my_email_config(
    req: EmailConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建或更新当前用户的邮箱配置"""
    existing = db.query(EmailConfig).filter(
        (EmailConfig.email_address == req.email_address)
        & (EmailConfig.user_id == current_user.id)
    ).first()

    if existing:
        existing.imap_server = req.imap_server
        existing.imap_port = req.imap_port
        existing.password_encrypted = encrypt_password(req.password)
        if req.download_dir is not None:
            existing.download_dir = req.download_dir
        existing.is_enabled = True
        db.commit()
        db.refresh(existing)
        log_operation(db, current_user.id, "update_email_config", "email_config", existing.id, "更新邮箱配置")
        return existing
    else:
        new_cfg = EmailConfig(
            user_id=current_user.id,
            imap_server=req.imap_server,
            imap_port=req.imap_port,
            email_address=req.email_address,
            password_encrypted=encrypt_password(req.password),
            download_dir=req.download_dir,
            is_enabled=True,
        )
        db.add(new_cfg)
        db.commit()
        db.refresh(new_cfg)
        log_operation(db, current_user.id, "create_email_config", "email_config", new_cfg.id, "创建邮箱配置")
        return new_cfg


@router.delete("/user/email-configs/{config_id}")
def delete_my_email_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除当前用户的配置"""
    cfg = db.query(EmailConfig).filter(
        (EmailConfig.id == config_id)
        & (EmailConfig.user_id == current_user.id)
    ).first()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )
    db.delete(cfg)
    db.commit()
    log_operation(db, current_user.id, "delete_email_config", "email_config", config_id, "删除邮箱配置")
    return {"message": "配置已删除"}


@router.post("/user/email-sync/{config_id}")
def sync_my_email_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """手动触发当前用户的配置同步"""
    cfg = db.query(EmailConfig).filter(
        (EmailConfig.id == config_id)
        & (EmailConfig.user_id == current_user.id)
    ).first()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )
    result = sync_emails(config_id)
    log_operation(db, current_user.id, "trigger_email_sync", "email_config", config_id, f"手动触发同步: {result}")
    return result


@router.get("/user/email-sync-logs")
def list_my_email_sync_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前用户的同步日志"""
    # 先获取用户的所有邮箱配置 ID
    config_ids = (
        db.query(EmailConfig.id)
        .filter(EmailConfig.user_id == current_user.id)
        .subquery()
    )
    total = db.query(EmailSyncLog).filter(
        EmailSyncLog.email_config_id.in_(config_ids)
    ).count()
    logs = (
        db.query(EmailSyncLog)
        .filter(EmailSyncLog.email_config_id.in_(config_ids))
        .order_by(EmailSyncLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "items": [
            {
                "id": log.id,
                "email_config_id": log.email_config_id,
                "total_emails": log.total_emails,
                "new_attachments": log.new_attachments,
                "downloaded": log.downloaded,
                "failed": log.failed,
                "status": log.status,
                "message": log.message,
                "created_at": log.created_at,
            }
            for log in logs
        ],
        "skip": skip,
        "limit": limit,
    }


# ── 管理员端点（需 Admin）───────────────────────────────

@router.get("/admin/users")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """分页获取用户列表"""
    total = db.query(User).count()
    users = db.query(User).order_by(User.id).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [_user_to_dict(u) for u in users],
        "skip": skip,
        "limit": limit,
    }


@router.patch("/admin/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    req: UpdateUserRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """更新用户角色或启用状态"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    if req.role is not None:
        if req.role not in ("admin", "user"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色只能是 admin 或 user",
            )
        user.role = req.role

    if req.is_active is not None:
        user.is_active = req.is_active

    db.commit()
    db.refresh(user)

    log_operation(
        db, user.id, "update_user", "user", user.id,
        f"更新用户信息: role={user.role}, is_active={user.is_active}",
    )
    return user


@router.get("/admin/login-logs")
def list_login_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """分页获取登录日志"""
    query = db.query(LoginLog)
    if user_id is not None:
        query = query.filter(LoginLog.user_id == user_id)
    total = query.count()
    logs = query.order_by(LoginLog.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "status": log.status,
                "created_at": log.created_at,
            }
            for log in logs
        ],
        "skip": skip,
        "limit": limit,
    }


@router.get("/admin/operation-logs")
def list_operation_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """分页获取操作日志"""
    query = db.query(OperationLog)
    if user_id is not None:
        query = query.filter(OperationLog.user_id == user_id)
    if action is not None:
        query = query.filter(OperationLog.action == action)
    total = query.count()
    logs = query.order_by(OperationLog.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "detail": log.detail,
                "created_at": log.created_at,
            }
            for log in logs
        ],
        "skip": skip,
        "limit": limit,
    }


@router.get("/admin/system-status")
def get_system_status(_: User = Depends(require_admin)):
    """获取系统运行状态"""
    db = SessionLocal()
    try:
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:
            db_status = "error"

        total_users = db.query(User).count()

        from app.models.resume_models import Resume
        total_resumes = db.query(Resume).filter(Resume.is_deleted == False).count()

        from app.main import acquire_scan_lock, release_scan_lock
        scan_active = not acquire_scan_lock()
        if not scan_active:
            release_scan_lock()

        from app.main import _startup_time
        delta = datetime.now() - _startup_time
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        uptime = f"{hours}小时{minutes}分钟"
    except Exception:
        db_status = "error"
        total_users = 0
        total_resumes = 0
        scan_active = False
        uptime = "未知"
    finally:
        db.close()

    return {
        "database": db_status,
        "total_users": total_users,
        "total_resumes": total_resumes,
        "scan_active": scan_active,
        "uptime": uptime,
    }


# ── 邮箱配置管理（需 Admin）─────────────────────────────

@router.get("/admin/email-configs")
def list_email_configs(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取邮箱配置列表"""
    configs = db.query(EmailConfig).order_by(EmailConfig.id).all()
    return [_email_config_to_dict(c) for c in configs]


@router.post("/admin/email-configs", response_model=EmailConfigResponse)
def create_email_config(
    req: EmailConfigRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """创建或更新邮箱配置"""
    existing = db.query(EmailConfig).filter(
        EmailConfig.email_address == req.email_address
    ).first()

    if existing:
        existing.imap_server = req.imap_server
        existing.imap_port = req.imap_port
        existing.password_encrypted = encrypt_password(req.password)
        if req.download_dir is not None:
            existing.download_dir = req.download_dir
        db.commit()
        db.refresh(existing)
        log_operation(db, existing.id, "update_email_config", "email_config", existing.id, "更新邮箱配置")
        return existing
    else:
        new_cfg = EmailConfig(
            imap_server=req.imap_server,
            imap_port=req.imap_port,
            email_address=req.email_address,
            password_encrypted=encrypt_password(req.password),
            download_dir=req.download_dir,
            is_enabled=True,
        )
        db.add(new_cfg)
        db.commit()
        db.refresh(new_cfg)
        log_operation(db, new_cfg.id, "create_email_config", "email_config", new_cfg.id, "创建邮箱配置")
        return new_cfg


@router.delete("/admin/email-configs/{config_id}")
def delete_email_config(
    config_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """删除邮箱配置"""
    cfg = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )
    db.delete(cfg)
    db.commit()
    log_operation(db, config_id, "delete_email_config", "email_config", config_id, "删除邮箱配置")
    return {"message": "配置已删除"}


@router.post("/admin/email-sync/{config_id}")
def trigger_email_sync(
    config_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """手动触发邮箱同步"""
    cfg = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )

    from app.services.email_sync import sync_emails
    result = sync_emails(config_id)

    log_operation(db, config_id, "trigger_email_sync", "email_config", config_id, f"手动触发同步: {result}")
    return result


# ── 管理员：邮件列表 / 详情（实时 IMAP 查询）─────────────────

@router.get("/admin/emails")
def list_emails(
    config_id: int = Query(..., description="邮箱配置 ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", description="搜索关键词"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取指定邮箱的邮件列表（实时 IMAP 查询）"""
    from app.services.email_sync import list_emails_from_imap
    result = list_emails_from_imap(config_id, page, page_size, search)
    return result


@router.get("/admin/emails/{uid}")
def get_email_detail(
    config_id: int = Query(..., description="邮箱配置 ID"),
    uid: str = Path(..., description="邮件 UID"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取单封邮件详情（实时 IMAP 查询）"""
    from app.services.email_sync import get_email_detail_from_imap
    result = get_email_detail_from_imap(config_id, uid)
    return result


@router.get("/admin/email-sync-logs")
def list_email_sync_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """分页获取邮箱同步日志"""
    total = db.query(EmailSyncLog).count()
    logs = (
        db.query(EmailSyncLog)
        .order_by(EmailSyncLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "items": [
            {
                "id": log.id,
                "email_config_id": log.email_config_id,
                "total_emails": log.total_emails,
                "new_attachments": log.new_attachments,
                "downloaded": log.downloaded,
                "failed": log.failed,
                "status": log.status,
                "message": log.message,
                "created_at": log.created_at,
            }
            for log in logs
        ],
        "skip": skip,
        "limit": limit,
    }
