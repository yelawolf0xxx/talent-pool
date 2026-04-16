"""目录扫描服务：检测新增简历文件（PDF/DOC/DOCX/PPT/PPTX）"""

import hashlib
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.resume_models import ResumeFile

logger = logging.getLogger(__name__)


def compute_file_hash(file_path: Path) -> str:
    """计算文件 SHA256 校验和"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def scan_resume_directory(db: Session) -> list[ResumeFile]:
    """
    扫描多个简历目录，找出新增或待处理的文件。

    返回需要处理的 ResumeFile 列表（新文件 + 已有 pending 状态 + 已变更文件）。
    """
    resume_dirs = settings.resume_dirs
    all_files = []
    for resume_dir in resume_dirs:
        dir_path = Path(resume_dir)
        if not dir_path.exists():
            logger.warning("简历目录不存在: %s", resume_dir)
            continue

        SUPPORTED_EXTENSIONS = {"*.pdf", "*.doc", "*.docx", "*.ppt", "*.pptx"}
        files = []
        for ext in SUPPORTED_EXTENSIONS:
            files.extend(dir_path.glob(ext))
        logger.info("扫描目录 %s: %d 个简历文件", resume_dir, len(files))
        all_files.extend(files)

    logger.info("共扫描到 %d 个简历文件", len(all_files))

    new_files = []
    for file_path in all_files:
        # UNC 路径不做 resolve，保持 \\server\share 格式
        if str(file_path).startswith("\\\\") or str(file_path).startswith("//"):
            abs_path = str(file_path).replace("//", "\\\\")
        else:
            abs_path = str(file_path.resolve())
        file_hash = compute_file_hash(file_path)

        # 检查是否已记录
        existing = db.query(ResumeFile).filter(ResumeFile.file_path == abs_path).first()

        if existing is None:
            # 新文件
            record = ResumeFile(
                file_path=abs_path,
                file_hash=file_hash,
                status="pending",
            )
            db.add(record)
            new_files.append(record)
            logger.info("发现新简历: %s", file_path.name)
        elif existing.status in ("pending", "failed"):
            # 之前未处理成功或处理失败的，重新尝试
            existing.file_hash = file_hash
            new_files.append(existing)
            logger.info("重新处理: %s (状态: %s)", file_path.name, existing.status)
        elif existing.status == "done" and existing.file_hash != file_hash:
            # 文件内容已变更，需要重新处理
            existing.file_hash = file_hash
            existing.status = "pending"
            existing.processed_at = None
            new_files.append(existing)
            logger.info("简历内容已更新: %s", file_path.name)

    if new_files:
        db.commit()
        for f in new_files:
            db.refresh(f)

    logger.info("本次新增/变更 %d 个简历文件", len(new_files))
    return new_files
