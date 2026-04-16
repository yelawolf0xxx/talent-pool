"""搜索服务：关键词搜索 + 语义搜索混合排序"""

import json
import logging
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.resume_models import Resume, ResumeFile
from app.models.schemas import ResumeResponse, SearchResultItem
from app.services.vector import semantic_search

logger = logging.getLogger(__name__)

# 混合搜索权重：语义搜索 60%，关键词匹配 40%
SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4


def _to_response(r: Resume) -> ResumeResponse:
    file_record = None  # 调用方自行填充
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
    )


def _match_reasons(resume: Resume, query: str) -> list[str]:
    """生成匹配原因说明"""
    reasons = []
    if resume.name and query.lower() in (resume.name or "").lower():
        reasons.append(f"姓名匹配「{query}」")
    if resume.current_title and query.lower() in (resume.current_title or "").lower():
        reasons.append(f"职位「{resume.current_title}」与搜索相关")
    if resume.skills_json:
        skills = json.loads(resume.skills_json)
        matched = [s for s in skills if query.lower() in s.lower()]
        if matched:
            reasons.append(f"技能匹配: {', '.join(matched)}")
    return reasons


def search_resumes(db: Session, query: str, skills: Optional[list[str]] = None,
                   min_years_exp: Optional[int] = None) -> list[SearchResultItem]:
    """
    混合搜索简历：SQL 关键词搜索 + ChromaDB 语义搜索。

    最终结果按加权分数排序。
    """
    all_resumes = db.query(Resume).all()

    # 应用筛选条件
    filtered = all_resumes
    if skills:
        filtered = [
            r for r in filtered
            if r.skills_json and any(s.lower() in (r.skills_json or "").lower() for s in skills)
        ]
    if min_years_exp is not None:
        def _parse_years(v) -> int | None:
            """解析年限字符串，提取可比较的整数（如 '3-5' → 3，'5+' → 5，'5' → 5）"""
            if v is None:
                return None
            s = str(v).strip()
            import re
            m = re.match(r"(\d+)", s)
            return int(m.group(1)) if m else None

        filtered = [
            r for r in filtered
            if (_y := _parse_years(r.years_exp)) is not None and _y >= min_years_exp
        ]

    if not filtered:
        return []

    # 1. 关键词搜索得分（SQL LIKE）
    keyword_scores = {}
    if query.strip():
        like_pattern = f"%{query.lower()}%"
        for r in filtered:
            score = 0.0
            if r.name and query.lower() in (r.name or "").lower():
                score += 0.5
            if r.current_title and query.lower() in (r.current_title or "").lower():
                score += 0.3
            if r.summary_text and query.lower() in (r.summary_text or "").lower():
                score += 0.2
            if r.skills_json and query.lower() in (r.skills_json or "").lower():
                score += 0.3
            keyword_scores[r.id] = min(score, 1.0)

    # 2. 语义搜索得分（向量不可用时降级为空）
    try:
        semantic_ids = set(semantic_search(query, n_results=50))
    except Exception:
        logger.warning("语义搜索失败，降级为纯关键词搜索", exc_info=True)
        semantic_ids = set()
    semantic_scores = {}
    for i, rid in enumerate(semantic_ids):
        # 排名越靠前分数越高
        semantic_scores[rid] = 1.0 - (i / len(semantic_ids)) if semantic_ids else 0.0

    # 3. 混合排序
    results = []
    for r in filtered:
        kw_score = keyword_scores.get(r.id, 0.0)
        sem_score = semantic_scores.get(r.id, 0.0)
        # 如果两个搜索都没命中，跳过
        if kw_score == 0 and sem_score == 0:
            continue
        combined = kw_score * KEYWORD_WEIGHT + sem_score * SEMANTIC_WEIGHT
        results.append(SearchResultItem(
            resume=_to_response(r),
            score=round(combined, 3),
            match_reasons=_match_reasons(r, query),
        ))

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:50]
