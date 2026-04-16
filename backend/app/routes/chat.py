"""AI 对话路由：流式输出（SSE）"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.resume_models import Resume, ChatSession
from app.models.schemas import ChatRequest, ChatResponse
from app.services.ai import chat_completion

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    AI 对话（非流式）。

    前端 Vue3 可先用此版本，后续升级为 SSE 流式。
    """
    # 获取简历上下文
    resume_context = None
    if req.resume_id:
        r = db.query(Resume).filter(Resume.id == req.resume_id).first()
        if r:
            resume_context = f"姓名: {r.name}, 职位: {r.current_title}, 摘要: {r.summary_text}"

    # 调用 AI
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
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
