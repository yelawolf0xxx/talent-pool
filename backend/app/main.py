"""FastAPI 应用入口"""

import logging
import threading
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.db import init_db, SessionLocal
from app.routes import api, chat, auth
from app.services.scanner import scan_resume_directory
from app.services.parser import parse_resume

# 日志配置
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format=settings.log_format,
)
logger = logging.getLogger(__name__)

# 全局扫描锁：防止手动扫描和定时扫描并发竞争
scan_lock = threading.Lock()

# 应用启动时间（用于系统状态 uptime 计算）
_startup_time = datetime.now()

app = FastAPI(title="AI 简历人才库", version="0.1.0")

# CORS：允许前端开发服务器
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _do_scan():
    """执行一次扫描 + 解析（供定时和手动扫描共用）"""
    logger.info("开始扫描简历...")
    db = SessionLocal()
    try:
        new_files = scan_resume_directory(db)
        for f in new_files:
            if f.status in ("pending", "failed"):
                f.status = "processing"
                db.commit()
                parse_resume(db, f)
    except Exception:
        logger.exception("扫描任务异常")
    finally:
        db.close()


def _acquire_scan_lock() -> bool:
    """尝试获取扫描锁，返回是否成功"""
    if scan_lock.acquire(blocking=False):
        return True
    logger.info("扫描任务已在运行，跳过本次触发")
    return False


def _release_scan_lock():
    """释放扫描锁"""
    scan_lock.release()


@app.on_event("startup")
def startup():
    """应用启动：初始化数据库 + 启动定时扫描器"""
    logger.info("初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")

    logger.info("启动简历扫描器（每 %d 秒）", settings.scan_interval)
    scheduler = BackgroundScheduler()
    scheduler.add_job(_scheduled_scan, "interval", seconds=settings.scan_interval)
    scheduler.start()


def _scheduled_scan():
    """定时扫描入口（带锁）"""
    if _acquire_scan_lock():
        try:
            _do_scan()
        finally:
            _release_scan_lock()


# 导出给 API 路由使用
acquire_scan_lock = _acquire_scan_lock
release_scan_lock = _release_scan_lock
do_scan = _do_scan

# 注册路由
app.include_router(api.router)
app.include_router(chat.router)
app.include_router(auth.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
