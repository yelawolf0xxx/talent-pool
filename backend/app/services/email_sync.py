"""邮件同步服务：通过 IMAP 拉取简历附件并保存到简历目录。

核心流程：
1. 连接 IMAP 服务器，搜索未读邮件
2. 解析邮件并提取简历格式附件
3. 主保存到第一个 resume_dir（scanner 自动解析）
4. 备份到 EmailConfig.download_dir（UNC 路径，按日期分类）
"""

import imaplib
import email
import logging
import os
from datetime import datetime, date
from email.header import decode_header
from email.message import Message
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings
from app.models.auth_models import EmailConfig, EmailSyncLog
from app.models.db import SessionLocal

logger = logging.getLogger(__name__)

# 支持的简历文件格式
SUPPORTED_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx"}

# 最大单封邮件附件数限制
MAX_ATTACHMENTS_PER_EMAIL = 20


def _get_fernet() -> Fernet:
    """获取 Fernet 实例，优先使用环境变量密钥，否则使用 fallback 密钥。"""
    key = os.environ.get("EMAIL_ENCRYPTION_KEY")
    if not key:
        logger.warning("环境变量 EMAIL_ENCRYPTION_KEY 未设置，使用内置 fallback 密钥（不安全）")
        # 固定 fallback 密钥（仅用于开发环境，生产环境必须设置环境变量）
        key = "bW9ja19rZXlfZm9yX2RldmVsb3BtZW50X29ubHlfMDEyMzQ1Njc4OQ=="
    # Fernet 密钥必须为 32 字节 URL-safe base64 编码
    return Fernet(key.encode() if isinstance(key, str) else key)


def decrypt_password(encrypted: str) -> str:
    """解密邮箱密码。

    Args:
        encrypted: Fernet 加密后的密码字符串。

    Returns:
        解密后的明文密码。

    Raises:
        ValueError: 解密失败（密钥不匹配或数据损坏）。
    """
    if not encrypted:
        raise ValueError("加密密码为空")
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted.encode())
        return decrypted.decode("utf-8")
    except InvalidToken as exc:
        logger.error("密码解密失败：密钥不匹配或数据已损坏")
        raise ValueError("密码解密失败，请检查加密密钥配置") from exc


def encrypt_password(plain: str) -> str:
    """加密明文密码，用于保存到 EmailConfig.password_encrypted。

    Args:
        plain: 明文密码或授权码。

    Returns:
        Fernet 加密后的字符串。
    """
    if not plain:
        raise ValueError("明文密码不能为空")
    fernet = _get_fernet()
    return fernet.encrypt(plain.encode()).decode()


def connect_imap(config: EmailConfig) -> imaplib.IMAP4_SSL:
    """建立 IMAP SSL 连接并登录。

    Args:
        config: 邮箱配置实例。

    Returns:
        已登录的 IMAP4_SSL 连接对象。

    Raises:
        ConnectionError: IMAP 连接失败。
        AuthenticationError: 认证失败（密码错误/账号异常）。
    """
    server = config.imap_server
    port = config.imap_port or 993

    if not server:
        raise ValueError("IMAP 服务器地址未配置")

    try:
        password = decrypt_password(config.password_encrypted)
    except ValueError as exc:
        raise ValueError(f"解密邮箱密码失败: {exc}") from exc

    try:
        logger.info("正在连接 IMAP 服务器: %s:%s", server, port)
        imap_conn = imaplib.IMAP4_SSL(server, port)
        # 设置 30 秒超时
        imap_conn.socket().settimeout(30)

        logger.info("正在登录邮箱: %s", config.email_address)
        imap_conn.login(config.email_address, password)
        logger.info("IMAP 连接成功")
        return imap_conn
    except imaplib.IMAP4.error as exc:
        error_msg = str(exc).lower()
        if "login" in error_msg or "auth" in error_msg:
            logger.error("IMAP 认证失败: %s", exc)
            raise ConnectionError(f"邮箱认证失败（账号或密码/授权码错误）: {exc}") from exc
        logger.error("IMAP 连接错误: %s", exc)
        raise ConnectionError(f"IMAP 连接失败: {exc}") from exc
    except OSError as exc:
        logger.error("IMAP 网络异常: %s", exc)
        raise ConnectionError(f"无法连接 IMAP 服务器 {server}:{port}: {exc}") from exc
    except TimeoutError as exc:
        logger.error("IMAP 连接超时: %s", exc)
        raise ConnectionError(f"连接超时: {server}:{port}") from exc


def _decode_header_value(raw: Optional[str]) -> str:
    """解码 MIME 邮件头（处理中文等非 ASCII 编码）。"""
    if not raw:
        return ""
    parts = []
    for data, charset in decode_header(raw):
        if isinstance(data, bytes):
            parts.append(data.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(data)
    return "".join(parts)


def fetch_unread_emails(imap_conn: imaplib.IMAP4_SSL, max_emails: int = 500) -> list:
    """搜索 INBOX 中未读邮件，返回 UID 列表。

    Args:
        imap_conn: 已登录的 IMAP 连接。
        max_emails: 最大获取数量。

    Returns:
        未读邮件的 UID 列表（字符串）。
    """
    try:
        # 选择 INBOX 文件夹
        status, _ = imap_conn.select("INBOX", readonly=False)
        if status != "OK":
            logger.warning("无法选择 INBOX 文件夹")
            return []

        # 搜索未读邮件
        status, data = imap_conn.search(None, "UNSEEN")
        if status != "OK" or not data[0]:
            logger.info("未发现未读邮件")
            return []

        uid_list = data[0].split()
        # 限制最大数量
        if len(uid_list) > max_emails:
            uid_list = uid_list[:max_emails]
            logger.info("未读邮件较多，仅处理前 %d 封", max_emails)

        logger.info("找到 %d 封未读邮件", len(uid_list))
        return uid_list
    except imaplib.IMAP4.error as exc:
        logger.error("搜索邮件失败: %s", exc)
        raise ConnectionError(f"搜索未读邮件失败: {exc}") from exc


def extract_attachments(email_bytes: bytes) -> list[tuple[str, bytes]]:
    """解析邮件并提取所有支持的简历格式附件。

    Args:
        email_bytes: 原始邮件字节。

    Returns:
        [(文件名, 文件内容), ...] 列表。
    """
    attachments = []
    msg: Message = email.message_from_bytes(email_bytes)

    for part in msg.walk():
        # 仅处理 multipart 的子部分
        if part.get_content_maintype() == "multipart":
            continue
        # 跳过内嵌图片等
        if part.get("Content-Disposition") is None:
            continue

        filename = part.get_filename()
        if not filename:
            continue

        # 解码文件名
        filename = _decode_header_value(filename)
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            logger.debug("跳过不支持的附件格式: %s", filename)
            continue

        payload = part.get_payload(decode=True)
        if payload is None:
            logger.warning("附件解码失败: %s", filename)
            continue

        attachments.append((filename, payload))

    # 限制单封邮件的附件数量
    if len(attachments) > MAX_ATTACHMENTS_PER_EMAIL:
        logger.warning("附件数量超出限制 (%d)，仅保留前 %d 个",
                       len(attachments), MAX_ATTACHMENTS_PER_EMAIL)
        attachments = attachments[:MAX_ATTACHMENTS_PER_EMAIL]

    return attachments


def save_attachment(filename: str, content: bytes, base_dir: str) -> str:
    """保存附件到指定目录。

    主保存位置为 resume_dir（scanner 自动解析），同时复制到 UNC 备份目录。

    Args:
        filename: 附件文件名。
        content: 附件字节内容。
        base_dir: 基础目录（第一个 resume_dir）。

    Returns:
        保存的完整文件路径。
    """
    today = date.today().isoformat()  # YYYY-MM-DD 格式
    target_dir = Path(base_dir) / today

    # 确保目录存在
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error("无法创建目录 %s: %s", target_dir, exc)
        raise

    # 文件名冲突处理：添加时间戳
    file_path = target_dir / filename
    if file_path.exists():
        stamp = datetime.now().strftime("%H%M%S%f")
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        new_name = f"{stem}_{stamp}{suffix}"
        file_path = target_dir / new_name
        logger.info("文件名冲突，重命名为: %s", new_name)

    file_path.write_bytes(content)
    logger.info("附件已保存: %s", file_path)
    return str(file_path)


def _copy_to_unc_backup(file_path: str, unc_dir: str) -> bool:
    """将已保存的附件复制到 UNC 备份目录。

    Args:
        file_path: 已保存的文件路径。
        unc_dir: UNC 备份目录（来自 EmailConfig.download_dir）。

    Returns:
        是否复制成功。
    """
    if not unc_dir:
        return False

    today = date.today().isoformat()
    backup_dir = Path(unc_dir) / today

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning("无法创建 UNC 备份目录 %s: %s", backup_dir, exc)
        return False

    dest = backup_dir / Path(file_path).name
    if dest.exists():
        stamp = datetime.now().strftime("%H%M%S%f")
        stem = Path(file_path).stem
        suffix = Path(file_path).suffix
        dest = backup_dir / f"{stem}_{stamp}{suffix}"

    try:
        dest.write_bytes(Path(file_path).read_bytes())
        logger.info("已备份到 UNC 目录: %s", dest)
        return True
    except OSError as exc:
        logger.warning("UNC 备份失败 %s -> %s: %s", file_path, dest, exc)
        return False


def sync_emails(config_id: int) -> dict:
    """执行单条邮箱配置的同步流程。

    Args:
        config_id: EmailConfig 主键 ID。

    Returns:
        结果统计 {total, new_attachments, downloaded, failed, saved_paths: []}
    """
    db = None
    result = {
        "total": 0,
        "new_attachments": 0,
        "downloaded": 0,
        "failed": 0,
        "saved_paths": [],
    }

    try:
        db = SessionLocal()
        config = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()

        if not config:
            logger.warning("邮箱配置不存在: id=%d", config_id)
            result["failed"] = 1
            return result

        if not config.is_enabled:
            logger.info("邮箱配置已禁用，跳过: id=%d email=%s", config_id, config.email_address)
            return result

        logger.info("开始同步邮箱: %s", config.email_address)

        # 连接 IMAP
        imap_conn = connect_imap(config)
        try:
            # 获取未读邮件
            uid_list = fetch_unread_emails(imap_conn)
            result["total"] = len(uid_list)

            # 获取第一个 resume_dir 作为主保存目录
            primary_dir = settings.resume_dirs[0] if settings.resume_dirs else None
            if not primary_dir:
                logger.error("未配置简历目录 (resume_dir)，无法保存附件")
                result["failed"] = len(uid_list)
                return result

            # 逐封处理邮件
            for uid in uid_list:
                try:
                    ok, data = imap_conn.fetch(uid, "(RFC822)")
                    if ok != "OK" or not data[0]:
                        logger.warning("邮件获取失败: uid=%s", uid.decode())
                        result["failed"] += 1
                        continue

                    raw_bytes = data[0][1]
                    attachments = extract_attachments(raw_bytes)
                    result["new_attachments"] += len(attachments)

                    for fname, fcontent in attachments:
                        try:
                            saved_path = save_attachment(fname, fcontent, primary_dir)
                            result["downloaded"] += 1
                            result["saved_paths"].append(saved_path)

                            # 同步备份到 UNC 路径
                            _copy_to_unc_backup(saved_path, config.download_dir)
                        except OSError as exc:
                            logger.error("保存附件失败: %s - %s", fname, exc)
                            result["failed"] += 1

                    # 标记邮件为已读
                    imap_conn.store(uid, "+FLAGS", "\\Seen")

                except Exception as exc:
                    logger.error("处理邮件失败 uid=%s: %s", uid.decode(), exc)
                    result["failed"] += 1

            # 更新最后同步时间
            config.last_sync_at = datetime.now()

        finally:
            try:
                imap_conn.logout()
            except Exception:
                pass

    except Exception as exc:
        logger.error("邮箱同步异常: id=%d error=%s", config_id, exc)
        result["failed"] = result["total"] or 1
        raise
    finally:
        if db:
            try:
                _write_sync_log(db, config_id, result)
                # 更新 last_sync_at
                config_record = db.query(EmailConfig).filter(EmailConfig.id == config_id).first()
                if config_record:
                    config_record.last_sync_at = datetime.now()
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()

    return result


def _write_sync_log(db, config_id: int, result: dict) -> None:
    """写入同步日志记录。"""
    total = result["total"]
    downloaded = result["downloaded"]
    failed = result["failed"]

    if failed == 0:
        status = "success"
    elif downloaded == 0:
        status = "failed"
    else:
        status = "partial"

    message = f"扫描 {total} 封，下载 {downloaded} 个附件，失败 {failed} 个"
    if result["saved_paths"]:
        message += f"，路径: {', '.join(result['saved_paths'][:5])}"
        if len(result["saved_paths"]) > 5:
            message += f" ... 等 {len(result['saved_paths'])} 个文件"

    sync_log = EmailSyncLog(
        email_config_id=config_id,
        total_emails=total,
        new_attachments=result["new_attachments"],
        downloaded=downloaded,
        failed=failed,
        status=status,
        message=message,
    )
    db.add(sync_log)
    db.flush()
    logger.info("同步日志已写入: %s", message)


def schedule_email_sync() -> dict:
    """定时任务入口（供 APScheduler 调用）。

    查询所有启用的邮箱配置，逐个执行同步。

    Returns:
        总体统计结果。
    """
    logger.info("=== 开始定时邮件同步 ===")
    db = None
    overall = {"total_configs": 0, "success": 0, "failed": 0, "details": []}

    try:
        db = SessionLocal()
        enabled_configs = db.query(EmailConfig).filter(EmailConfig.is_enabled == True).all()
        overall["total_configs"] = len(enabled_configs)

        if not enabled_configs:
            logger.info("未找到启用的邮箱配置，跳过同步")
            return overall

        for config in enabled_configs:
            try:
                sync_result = sync_emails(config.id)
                overall["success"] += 1
                overall["details"].append({
                    "config_id": config.id,
                    "email": config.email_address,
                    "status": "success",
                    "downloaded": sync_result["downloaded"],
                })
                logger.info("邮箱同步成功: %s 下载 %d 个附件",
                            config.email_address, sync_result["downloaded"])
            except Exception as exc:
                overall["failed"] += 1
                overall["details"].append({
                    "config_id": config.id,
                    "email": config.email_address,
                    "status": "failed",
                    "error": str(exc),
                })
                logger.error("邮箱同步失败: %s - %s", config.email_address, exc)

    except Exception as exc:
        logger.error("邮件同步调度异常: %s", exc)
    finally:
        if db:
            db.close()

    logger.info("=== 邮件同步完成: 成功 %d, 失败 %d ===",
                overall["success"], overall["failed"])
    return overall


