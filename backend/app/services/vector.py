"""向量搜索服务：ChromaDB 语义搜索"""

import json
import logging
import os
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.models.resume_models import Resume

logger = logging.getLogger(__name__)

# ChromaDB 持久化路径
_chroma_path = os.path.join(os.path.dirname(settings.resume_dir), "data", "chroma_db")
_client = chromadb.PersistentClient(path=_chroma_path, settings=ChromaSettings(anonymized_telemetry=False))
_collection = _client.get_or_create_collection(
    name="resume_embeddings",
    metadata={"hnsw:space": "cosine"},
)


def build_search_text(resume: Resume) -> str:
    """从简历数据构建搜索文本（用于生成 embedding）"""
    parts = []
    if resume.name:
        parts.append(resume.name)
    if resume.current_title:
        parts.append(resume.current_title)
    if resume.summary_text:
        parts.append(resume.summary_text)
    if resume.skills_json:
        skills = json.loads(resume.skills_json)
        if skills:
            parts.append("技能: " + ", ".join(skills))
    if resume.education_json:
        education = json.loads(resume.education_json)
        if education:
            for edu in education:
                parts.append(f"{edu.get('school', '')} {edu.get('degree', '')} {edu.get('major', '')}")
    if resume.work_exp_json:
        work = json.loads(resume.work_exp_json)
        if work:
            for w in work:
                parts.append(f"{w.get('company', '')} {w.get('title', '')}")
    return " ".join(parts)


def add_resume_embedding(resume_id: int, text: str):
    """为简历添加向量索引"""
    # ChromaDB 的默认 embedding 函数已支持语义搜索
    _collection.upsert(
        ids=[str(resume_id)],
        documents=[text],
        metadatas=[{"resume_id": resume_id}],
    )
    logger.info("已为简历 ID=%d 建立向量索引", resume_id)


def semantic_search(query: str, n_results: int = 50) -> list[int]:
    """
    语义搜索简历，返回按相似度排序的简历 ID 列表。

    如果向量库不可用（如模型未下载），返回空列表。
    """
    try:
        count = _collection.count()
        if count == 0:
            return []
        results = _collection.query(
            query_texts=[query],
            n_results=min(n_results, count),
        )
        if not results["ids"] or not results["ids"][0]:
            return []
        return [int(rid) for rid in results["ids"][0]]
    except Exception:
        logger.warning("向量搜索不可用（模型未就绪），降级为关键词搜索", exc_info=True)
        return []


def get_collection_count() -> int:
    """获取向量库中的文档数量"""
    return _collection.count()
