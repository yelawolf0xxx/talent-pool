"""AI 对话路由：RAG 增强对话，自动检索人才库"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.resume_models import Resume, ChatSession
from app.models.schemas import ChatRequest, ChatResponse
from app.services.ai import chat_completion, build_candidates_context, _is_recommendation_intent
from app.services import search as search_svc

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    AI 对话（非流式）。

    当用户消息包含推荐意图时，自动检索人才库并将结果注入对话历史，
    强制 AI 基于真实候选人数据作答。
    """
    # 获取简历上下文
    resume_context = None
    if req.resume_id:
        r = db.query(Resume).filter(Resume.id == req.resume_id).first()
        if r:
            resume_context = f"姓名: {r.name}, 职位: {r.current_title}, 摘要: {r.summary_text}"

    # 构建消息列表（深拷贝，避免修改原始请求）
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    # 判断是否需要检索人才库
    candidates_context = None
    if req.messages:
        last_message = req.messages[-1].content
        if _is_recommendation_intent(last_message):
            matches = search_svc.search_resumes(
                db, query=last_message, skills=None, min_years_exp=None
            )
            matches = matches[:10]
            candidates_context = build_candidates_context(matches)
            logger.info("人才库检索: 问题='%s', 匹配 %d 人", last_message[:50], len(matches))

            # 将检索结果作为 system 消息插入到消息列表开头
            if candidates_context:
                system_inject = (
                    f"以下是从人才库中检索到的与用户问题最匹配的候选人列表。\n"
                    f"你必须直接从这个列表中推荐候选人，列出他们的姓名、职位、核心技能和亮点。\n"
                    f"不要询问更多条件，不要编造不存在的人。\n\n"
                    f"{candidates_context}"
                )
                messages.insert(0, {"role": "system", "content": system_inject})

    # 调用 AI
    reply = chat_completion(messages, resume_context)

    # 保存对话记录
    for m in req.messages:
        db.add(ChatSession(
            session_id=req.session_id,
            role=m.role,
            content=m.content,
            resume_id=req.resume_id,
        ))
    db.add(ChatSession(
        session_id=req.session_id,
        role="assistant",
        content=reply,
        resume_id=req.resume_id,
    ))
    db.commit()

    return ChatResponse(session_id=req.session_id, reply=reply)
