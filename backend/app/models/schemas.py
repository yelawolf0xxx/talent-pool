"""Pydantic 数据模型（API 输入输出）"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ── 简历文件 ──────────────────────────────────────────────

class ResumeFileStatus(BaseModel):
    file_path: str
    file_hash: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None


# ── 简历数据 ──────────────────────────────────────────────

class EducationItem(BaseModel):
    school: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    year: Optional[int | str] = None


class WorkExperienceItem(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    description: Optional[str] = None


class ResumeBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    current_title: Optional[str] = None
    years_exp: Optional[int | str] = None
    education: list[EducationItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    work_experience: list[WorkExperienceItem] = Field(default_factory=list)
    summary_text: Optional[str] = None


class ResumeResponse(ResumeBase):
    id: int
    file_path: Optional[str] = None

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    """简历列表分页响应"""
    items: list[ResumeResponse]
    total: int
    skip: int
    limit: int


# ── 搜索 ──────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索关键词")
    skills: list[str] = Field(default_factory=list, description="技能筛选")
    min_years_exp: Optional[int] = Field(None, description="最低年限要求")


class SearchResultItem(BaseModel):
    resume: ResumeResponse
    score: float = Field(description="匹配度分数 0-1")
    match_reasons: list[str] = Field(default_factory=list, description="匹配原因说明")


class SearchResponse(BaseModel):
    total: int
    results: list[SearchResultItem]


# ── 扫描 ──────────────────────────────────────────────────

class ScanProgressResponse(BaseModel):
    active: bool = Field(description="是否有扫描任务在进行")
    total: int = Field(description="待处理文件总数")
    current: int = Field(description="当前处理进度")
    processed: int = Field(description="已成功处理数量")
    failed: int = Field(description="失败数量")
    message: str = Field(description="状态描述信息")


class ScanStartResponse(BaseModel):
    status: str = Field(description="状态: started/running")
    message: str = Field(description="提示信息")


# ── 对话 ──────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # user / assistant
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    resume_id: Optional[int] = Field(None, description="关联的候选人 ID")
    session_id: str = Field(description="会话标识")


class ChatResponse(BaseModel):
    session_id: str = Field(description="会话标识")
    reply: str = Field(description="AI 回复内容")


# ── 推荐理由 ──────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    resume_id: int
    query: str
    suitable: bool = Field(description="是否适合该岗位")
    score: int = Field(description="匹配度分数 0-100")
    conclusion: str = Field(description="一句话总结")
    reason: str = Field(description="详细分析说明")


# ── 批量操作 ──────────────────────────────────────────────

class BatchIdsRequest(BaseModel):
    ids: list[int] = Field(description="简历 ID 列表")


class RecycleBinItem(BaseModel):
    """回收站中的简历"""
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    current_title: Optional[str] = None
    years_exp: Optional[int | str] = None
    education: list[EducationItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    work_experience: list[WorkExperienceItem] = Field(default_factory=list)
    summary_text: Optional[str] = None
    file_path: Optional[str] = None
    deleted_at: Optional[datetime] = None


class RecycleBinResponse(BaseModel):
    total: int
    items: list[RecycleBinItem]


# ── 上传 ──────────────────────────────────────────────────

class UploadFailedItem(BaseModel):
    filename: str = Field(description="文件名")
    reason: str = Field(description="失败原因")


class UploadResponse(BaseModel):
    uploaded: list[str] = Field(description="成功上传的文件名列表")
    failed: list[UploadFailedItem] = Field(default_factory=list, description="上传失败的文件列表")
