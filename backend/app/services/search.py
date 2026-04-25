"""搜索服务：关键词搜索 + 语义搜索混合排序"""

import json
import logging
import re
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
    tokens = _parse_query_tokens(query) if query.strip() else [query]
    for token in tokens:
        token_lower = token.lower()
        if resume.name and token_lower == (resume.name or "").lower():
            reasons.append(f"姓名精确匹配「{token}」")
        elif resume.name and token_lower in (resume.name or "").lower():
            reasons.append(f"姓名包含「{token}」")
        if resume.current_title and token_lower in (resume.current_title or "").lower():
            reasons.append(f"职位「{resume.current_title}」与搜索相关")
        if resume.skills_json:
            skills = json.loads(resume.skills_json)
            matched = [s for s in skills if token_lower in s.lower()]
            if matched:
                reasons.append(f"技能匹配: {', '.join(matched)}")
    return reasons


def _is_name_like_query(query: str) -> bool:
    """判断搜索词是否像人名：短词（≤4字符）、不含空格、无特殊符号"""
    q = query.strip()
    return len(q) <= 4 and ' ' not in q and q.isalpha()


def _parse_query_tokens(query: str) -> list[str]:
    """将搜索词按空格拆分为多个 token"""
    return [t.strip() for t in query.strip().split() if t.strip()]


def search_resumes(db: Session, query: str, skills: Optional[list[str]] = None,
                   min_years_exp: Optional[int] = None, uploaded_by: Optional[int] = None) -> list[SearchResultItem]:
    """
    混合搜索简历：SQL 关键词搜索 + ChromaDB 语义搜索混合排序。

    特殊处理：
    - 当搜索词像人名（短词、无空格）且精确匹配姓名时，该简历置顶
    - 人名模式下仅返回姓名精确匹配的结果
    - 多词搜索时每个 token 独立计分
    """
    all_resumes = db.query(Resume).filter(Resume.is_deleted == False).all()

    # 按归属用户筛选
    if uploaded_by is not None:
        all_resumes = [r for r in all_resumes if r.uploaded_by == uploaded_by]

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
            m = re.match(r"(\d+)", s)
            return int(m.group(1)) if m else None

        filtered = [
            r for r in filtered
            if (_y := _parse_years(r.years_exp)) is not None and _y >= min_years_exp
        ]

    if not filtered:
        return []

    # ── 判断是否为"人名搜索"模式 ──────────────────
    is_name_query = _is_name_like_query(query)
    # 在人名模式下，先尝试精确匹配姓名
    exact_name_matches = []
    if is_name_query:
        for r in filtered:
            if r.name and query.strip().lower() == r.name.lower():
                exact_name_matches.append(r)
        if exact_name_matches:
            # 人名精确命中 → 仅返回姓名匹配的简历，不参与混合排序
            results = []
            for r in exact_name_matches:
                results.append(SearchResultItem(
                    resume=_to_response(r),
                    score=1.0,
                    match_reasons=[f"姓名精确匹配「{query.strip()}」"],
                ))
            return results

    # ── 1. 关键词搜索得分 ────────────────────────
    keyword_scores = {}
    if query.strip():
        tokens = _parse_query_tokens(query)
        for r in filtered:
            score = 0.0
            if tokens:
                for token in tokens:
                    token_lower = token.lower()
                    # 姓名精确匹配（整个 token 完全匹配）
                    if r.name and token_lower == (r.name or "").lower():
                        score += 1.0
                    # 姓名模糊匹配（子串）
                    elif r.name and token_lower in (r.name or "").lower():
                        score += 0.7
                    if r.current_title and token_lower in (r.current_title or "").lower():
                        score += 0.3
                    if r.summary_text and token_lower in (r.summary_text or "").lower():
                        score += 0.1
                    if r.skills_json and token_lower in (r.skills_json or "").lower():
                        score += 0.3
            keyword_scores[r.id] = min(score, 1.0)

    # ── 2. 语义搜索得分 ──────────────────────────
    has_name_hit = any(
        keyword_scores.get(r.id, 0.0) >= 0.7 for r in filtered
    )

    # 如果命中了姓名，降低语义权重；否则保持默认比例
    if has_name_hit:
        sem_weight = 0.1
        kw_weight = 0.9
    else:
        sem_weight = SEMANTIC_WEIGHT
        kw_weight = KEYWORD_WEIGHT

    try:
        semantic_ids = set(semantic_search(query, n_results=50))
    except Exception:
        logger.warning("语义搜索失败，降级为纯关键词搜索", exc_info=True)
        semantic_ids = set()
    semantic_scores = {}
    for i, rid in enumerate(semantic_ids):
        semantic_scores[rid] = 1.0 - (i / len(semantic_ids)) if semantic_ids else 0.0

    # ── 3. 混合排序 ──────────────────────────────
    results = []
    has_query = bool(query.strip())
    for r in filtered:
        kw_score = keyword_scores.get(r.id, 0.0)
        sem_score = semantic_scores.get(r.id, 0.0)
        if has_query and kw_score == 0 and sem_score == 0:
            continue
        combined = kw_score * kw_weight + sem_score * sem_weight if has_query else 0.0
        results.append(SearchResultItem(
            resume=_to_response(r),
            score=round(combined, 3),
            match_reasons=_match_reasons(r, query) if has_query else [],
        ))

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:50]
