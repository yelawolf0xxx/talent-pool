"""REST API 路由：搜索、简历详情"""

import asyncio
import json
import logging
import threading
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.resume_models import Resume, ResumeFile
from app.models.schemas import (
    ResumeResponse,
    SearchRequest, SearchResponse, SearchResultItem,
    RecommendationResponse,
    ScanProgressResponse, ScanStartResponse,
)
from app.services import search as search_svc
from app.services.ai import generate_recommendation
from app.services.scanner import scan_resume_directory
from app.services.parser import parse_resume

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["resumes"])

# ── 扫描进度（线程安全共享状态）────────────────────

_scan_progress = {
    "active": False,
    "total": 0,
    "current": 0,
    "processed": 0,
    "failed": 0,
    "message": "",
}
_progress_lock = threading.Lock()


def _update_progress(**kwargs):
    with _progress_lock:
        _scan_progress.update(kwargs)


def _get_progress():
    with _progress_lock:
        return dict(_scan_progress)


def _scan_worker():
    """后台扫描线程，使用全局锁避免与定时扫描竞争"""
    from app.main import acquire_scan_lock, release_scan_lock
    from app.models.db import SessionLocal

    if not acquire_scan_lock():
        _update_progress(active=False, message="扫描任务已在运行")
        return

    _update_progress(active=True, current=0, processed=0, failed=0, message="正在扫描目录...")
    db = SessionLocal()
    try:
        new_files = scan_resume_directory(db)
        total = len(new_files)
        _update_progress(total=total, current=0)

        if total == 0:
            _update_progress(active=False, message="无需处理的简历")
            return

        for f in new_files:
            if f.status in ("pending", "processing", "failed"):
                f.status = "processing"
                db.commit()
                if parse_resume(db, f):
                    _update_progress(processed=_scan_progress["processed"] + 1)
                else:
                    _update_progress(failed=_scan_progress["failed"] + 1)
                _update_progress(current=_scan_progress["current"] + 1)

        _update_progress(active=False, message=f"扫描完成，成功 {_scan_progress['processed']} 份，失败 {_scan_progress['failed']} 份")
    except Exception:
        logger.exception("扫描任务异常")
        _update_progress(active=False, message="扫描出错")
    finally:
        db.close()
        release_scan_lock()


@router.get("/scan/status", response_model=ScanProgressResponse)
def scan_status():
    """获取扫描进度"""
    return _get_progress()


@router.post("/scan", response_model=ScanStartResponse)
def manual_scan(db: Session = Depends(get_db)):
    """手动触发简历扫描与解析（异步）"""
    if _scan_progress["active"]:
        return {"status": "running", "message": "扫描任务正在进行中"}

    # 启动后台线程执行扫描
    thread = threading.Thread(target=_scan_worker, daemon=True)
    thread.start()
    return {"status": "started", "message": "扫描任务已启动"}


@router.get("/resumes", response_model=list[ResumeResponse])
def list_resumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """列出所有已解析简历"""
    resumes = db.query(Resume).offset(skip).limit(limit).all()
    results = []
    for r in resumes:
        file_record = db.query(ResumeFile).filter(ResumeFile.id == r.file_id).first()
        resp = ResumeResponse(
            id=r.id,
            name=r.name,
            email=r.email,
            phone=r.phone,
            current_title=r.current_title,
            years_exp=r.years_exp,
            education=json.loads(r.education_json) if r.education_json else [],
            skills=json.loads(r.skills_json) if r.skills_json else [],
            work_experience=json.loads(r.work_exp_json) if r.work_exp_json else [],
            summary_text=r.summary_text,
            file_path=file_record.file_path if file_record else None,
        )
        results.append(resp)
    return results


@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """获取简历详情"""
    r = db.query(Resume).filter(Resume.id == resume_id).first()
    if not r:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="简历不存在")

    file_record = db.query(ResumeFile).filter(ResumeFile.id == r.file_id).first()
    return ResumeResponse(
        id=r.id,
        name=r.name,
        email=r.email,
        phone=r.phone,
        current_title=r.current_title,
        years_exp=r.years_exp,
        education=json.loads(r.education_json) if r.education_json else [],
        skills=json.loads(r.skills_json) if r.skills_json else [],
        work_experience=json.loads(r.work_exp_json) if r.work_exp_json else [],
        summary_text=r.summary_text,
        file_path=file_record.file_path if file_record else None,
    )


@router.post("/search", response_model=SearchResponse)
def search_resumes(req: SearchRequest, db: Session = Depends(get_db)):
    """搜索简历（关键词 + 筛选）"""
    results = search_svc.search_resumes(
        db,
        query=req.query,
        skills=req.skills or None,
        min_years_exp=req.min_years_exp,
    )
    return SearchResponse(total=len(results), results=results)


@router.get("/resumes/{resume_id}/recommend", response_model=RecommendationResponse)
def get_recommendation(resume_id: int, query: str = Query(..., description="岗位需求描述"), db: Session = Depends(get_db)):
    """AI 分析岗位匹配度"""
    r = db.query(Resume).filter(Resume.id == resume_id).first()
    if not r:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="简历不存在")

    summary = r.summary_text or ""
    result = generate_recommendation(summary, query)
    return RecommendationResponse(
        resume_id=resume_id,
        query=query,
        suitable=result.get("suitable", False),
        score=result.get("score", 0),
        conclusion=result.get("conclusion", ""),
        reason=result.get("reason", ""),
    )
