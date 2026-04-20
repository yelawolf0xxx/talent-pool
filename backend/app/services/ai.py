"""AI 服务封装：Claude API 调用"""

import json
import re
import logging
from typing import Optional

from anthropic import Anthropic

from app.config import settings
from app.services.preprocessor import preprocess_resume_text, extract_key_sections

logger = logging.getLogger(__name__)

_client: Optional[Anthropic] = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        kwargs = {"api_key": settings.auth_token}
        if settings.base_url:
            kwargs["base_url"] = settings.base_url
        _client = Anthropic(**kwargs)
    return _client


# 简历结构化提取提示词（v2：增强表格结构识别）
SYSTEM_EXTRACT_PROMPT = """\
你是一名专业的简历分析助手，擅长从非结构化的简历中提取和推断信息。

## 📋 解析原则
1. **精确优先原则**：首先提取明确写出的信息
2. **上下文推断原则**：如果没有明确写出，请根据上下文进行合理推断：
   - 从技能和工作经历推算可能的学历水平
   - 从工作起止时间计算大致工作年限
   - 从职位描述和项目经验推断核心技能
3. **保守留空原则**：如果既无明确信息也无法合理推断，再设为 null
4. **格式灵活原则**：支持各种时间格式、年限表达

## 📌 表格结构说明
文本中可能包含表格数据标记：
- `[表格N]` 表示第N个表格的某行内容（多列表格，单元格用 | 分隔）
- `[表格N 行M]` 表示第N个表格的第M行（单列表格）

**单列表格是智联招聘模板的常见格式，典型结构：**
- 表格1: 应聘信息（应聘职位、应聘企业、工作地点、手机、邮箱）
- 表格2: 工作经历（每段经历占1-3行：公司+职位、时间段、工作描述）
- 表格3+: 语言/技能/证书/教育

**工作经历识别规则：**
- 如果某行包含公司名和职位（如"某某公司   软件工程师"），下一行是时间（如"2020.01-2021.06"），再下一行含"工作描述"，这构成一段完整经历
- 公司名和职位通常在同一行，用空格或制表符分隔
- 时间格式可能是"2020.01-2021.06 (1年5个月)"或"2020.01-至今"

## 🎯 字段提取指南

### 姓名 (name)
- 寻找：通常在开头，"姓名："后，"个人简历"下方，或文件开头第一行非空文本
- 注意：可能有中文名、英文名，优先取中文名
- 推断：如果找不到，可设为 null

### 邮箱 (email)
- 格式：xxx@xxx.xxx
- 位置：联系方式段落、表格中的"邮箱："行、"EMAIL"行
- 注意：可能在 `[表格1 行X]` 标记的行中

### 电话 (phone)
- 格式：11位手机号 或 带区号的固话
- 位置：联系方式段落、表格中的"手机："行、"电话"行
- 注意：可能在 `[表格1 行X]` 标记的行中

### 当前职位 (current_title)
- 位置：最近的工作经历、自我评价、简历标题、表格2中第一段经历的职位
- 推断：如果没有明确当前职位，用最近的工作职位代替

### 工作年限 (years_exp)
- 精确提取：如"5年工作经验" → "5"
- 范围提取：如"3-5年" → "3-5"
- 符号提取：如"3+" → "3+"
- 计算：从工作经历时间跨度推算
- 应届生：如"26年应届生" → "应届"

### 教育经历 (education)
- 学校 (school)：大学、学院名称
- 学位 (degree)：本科/硕士/博士/大专/高中
- 专业 (major)：如"计算机科学与技术"
- 毕业年份 (year)：支持多种格式

### 技能 (skills)
- 明确技能：如"Python, Java, MySQL"
- 隐含技能：从工作描述、项目经验中挖掘
- **注意表格中的技能**：格式可能是"技能名 | 使用X个月"
- 标准化：将相似技能合并

### 工作经历 (work_experience)
- 公司 (company)：全称或简称
- 职位 (title)：明确职位名称
- 时间 (start/end)：支持多种格式，"至今"要保留
- 描述 (description)：职责和成就
- **关键**：仔细扫描所有含公司名、时间段的行，每段独立的公司经历都要提取

### 个人摘要 (summary_text)
- 用2-3句话概括核心优势和亮点
- 基于技能、经验、成就

## 📄 输出格式
请严格按照以下 JSON Schema 返回，不要输出任何其他内容：

{
    "name": "字符串或null",
    "email": "字符串或null",
    "phone": "字符串或null",
    "current_title": "字符串或null",
    "years_exp": "字符串（如'5'、'3-5'、'3+'、'经验丰富'）或null",
    "education": [{"school": "...", "degree": "...", "major": "...", "year": "..."}],
    "skills": ["技能1", "技能2", ...],
    "work_experience": [{"company": "...", "title": "...", "start": "...", "end": "...", "description": "..."}],
    "summary_text": "2-3句话的摘要"
}

## ⚠️ 重要提示
- 数组字段如果没找到，返回空数组 []
- 标量字段如果没找到，返回 null
- 时间格式保持原样，不要转换
- 如果信息模糊，可以合理猜测
- 最后一定要输出有效的 JSON
"""


def _extract_text(response) -> str:
    """从 Anthropic 响应中提取文本（兼容 thinking 模型）"""
    for block in response.content:
        if block.type == "text" and block.text:
            return block.text.strip()
    return ""


def _clean_json_response(text: str) -> str:
    """
    清理 AI 响应中的 JSON，移除可能的 markdown 和额外文本
    """
    if not text:
        return ""

    # 移除 markdown 代码块标记
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    # 查找 JSON 对象
    json_pattern = r"\{[\s\S]*\}"
    match = re.search(json_pattern, text)
    if match:
        return match.group(0)

    return text.strip()


def extract_structured_info(raw_text: str) -> Optional[dict]:
    """
    调用 Claude 从简历文本中提取结构化信息
    双层文本策略：原始文本保底 + 轻量整理文本辅助
    """
    try:
        logger.info("开始解析简历文本，长度: %d 字符", len(raw_text))

        # 1. 轻量整理（仅去页码和空行，保留所有信息）
        cleaned_text = preprocess_resume_text(raw_text)
        logger.debug("轻量整理后文本长度: %d 字符", len(cleaned_text))

        if len(cleaned_text) < 50:
            logger.warning("整理后文本过短，可能无法解析")
            return None

        # 2. 提取关键段落（在整理后的文本上操作）
        sections = extract_key_sections(cleaned_text)

        # 3. 构建双层输入的 User Prompt
        user_prompt = f"""请分析以下简历文本，提取结构化信息。

⚠️ 以下提供两层文本：
- 【原始文本】是直接从文件提取的完整内容，信息最全
- 【整理文本】是经过格式整理的版本，结构更清晰
请优先参考原始文本，确保不遗漏任何信息。

━━━━━━━━━━ 原始文本（完整保底） ━━━━━━━━━━

{raw_text}

━━━━━━━━━━ 整理文本（结构清晰） ━━━━━━━━━━

{cleaned_text}

🔍 已识别的关键段落（辅助参考）

{json.dumps(sections, ensure_ascii=False, indent=2)}

💡 推理提示

请先思考以下问题，然后提取信息：
1. 哪些信息是明确写出的？（姓名、联系方式、职位、年限）
2. 哪些信息可以合理推断？（学历、技能）
3. 工作经历有哪些？注意识别"公司名 + 职位 + 时间段"的组合
4. 核心技能有哪些？

请先列出你的推理过程，然后输出最终的 JSON 结果。"""

        # 4. 调用 AI
        client = get_client()
        response = client.messages.create(
            model=settings.model,
            max_tokens=4096,  # 增加 token 数用于推理
            system=SYSTEM_EXTRACT_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # 较低温度以获得更一致的结果
        )

        raw_response = _extract_text(response)
        if not raw_response:
            logger.error("AI 返回空响应")
            return None

        logger.debug("AI 原始响应: %s", raw_response[:500])

        # 5. 清理和解析 JSON
        json_str = _clean_json_response(raw_response)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error("JSON 解析失败，尝试修复: %s", e)
            # 尝试修复常见的 JSON 问题
            json_str = json_str.replace("'", '"')  # 单引号转双引号
            json_str = re.sub(r",\s*}", "}", json_str)  # 移除尾随逗号
            json_str = re.sub(r",\s*]", "]", json_str)

            try:
                data = json.loads(json_str)
            except Exception:
                logger.error("修复后仍然解析失败，响应: %s", raw_response[:1000])
                return None

        # 6. 验证和补全数据（使用原始文本作为参考）
        validated_data = validate_and_complete_resume_data(data, raw_text)

        logger.info("简历解析成功: 姓名=%s, 技能数=%d, 工作经历数=%d",
                   validated_data.get("name", "未知"),
                   len(validated_data.get("skills", [])),
                   len(validated_data.get("work_experience", [])))

        return validated_data

    except Exception as e:
        logger.exception("AI 信息提取失败: %s", str(e))
        return None


def validate_and_complete_resume_data(data: dict, original_text: str) -> dict:
    """
    验证和补全简历数据
    """
    if not data:
        return {
            "name": None,
            "email": None,
            "phone": None,
            "current_title": None,
            "years_exp": None,
            "education": [],
            "skills": [],
            "work_experience": [],
            "summary_text": "简历信息提取失败"
        }

    # 确保所有字段都存在
    defaults = {
        "name": None,
        "email": None,
        "phone": None,
        "current_title": None,
        "years_exp": None,
        "education": [],
        "skills": [],
        "work_experience": [],
        "summary_text": ""
    }

    for key, default in defaults.items():
        if key not in data or data[key] is None:
            data[key] = default

    # 类型检查
    if not isinstance(data.get("education"), list):
        data["education"] = []
    if not isinstance(data.get("skills"), list):
        data["skills"] = []
    if not isinstance(data.get("work_experience"), list):
        data["work_experience"] = []

    # 智能补全缺失信息（使用原始文本兜底）
    data = _infer_missing_fields(data, original_text)

    # 生成摘要（如果 AI 没生成）
    if not data["summary_text"] or len(data["summary_text"]) < 10:
        data["summary_text"] = _generate_summary(data)

    return data


def _infer_missing_fields(data: dict, text: str) -> dict:
    """
    推断缺失的字段，使用原始文本兜底
    """
    # 1. 从工作经历推断当前职位
    if not data["current_title"] and data["work_experience"]:
        for exp in data["work_experience"][:2]:  # 查看最近的两段经历
            if exp.get("title"):
                data["current_title"] = exp["title"]
                break

    # 2. 从工作经历推断工作年限
    if not data["years_exp"] and data["work_experience"]:
        # 简单推断：有多个工作经历 -> 经验丰富
        if len(data["work_experience"]) > 1:
            data["years_exp"] = "经验丰富"
        elif data["work_experience"]:
            data["years_exp"] = "有相关经验"

    # 3. 从原始文本中提取技能（如果 AI 没提取到）
    if not data["skills"] or len(data["skills"]) < 3:
        inferred_skills = _extract_skills_from_text(text)
        if inferred_skills:
            data["skills"] = list(set(data["skills"] + inferred_skills))[:20]  # 去重，最多20个

    # 4. 标准化技能名称
    if data["skills"]:
        data["skills"] = [_normalize_skill(skill) for skill in data["skills"]]
        data["skills"] = [s for s in data["skills"] if s]  # 移除空值

    return data


def _extract_skills_from_text(text: str) -> list:
    """
    从文本中提取技能关键词（兜底策略）
    """
    # 常见技能关键词
    skill_keywords = [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "C++", "C#",
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
        "Docker", "Kubernetes", "Linux", "Git", "AWS", "Azure", "阿里云",
        "Vue", "React", "Angular", "Spring", "Django", "Flask",
        "机器学习", "深度学习", "AI", "数据分析", "数据挖掘",
        "产品经理", "项目经理", "UI设计", "UX设计", "测试", "运维"
    ]

    found_skills = []
    for skill in skill_keywords:
        if skill.lower() in text.lower():
            found_skills.append(skill)

    return found_skills[:10]  # 最多10个


def _normalize_skill(skill: str) -> str:
    """
    标准化技能名称
    """
    skill = skill.strip()

    # 映射常见变体
    skill_map = {
        "python3": "Python",
        "java开发": "Java",
        "js": "JavaScript",
        "ts": "TypeScript",
        "mysql数据库": "MySQL",
        "postgresql": "PostgreSQL",
        "mongodb": "MongoDB",
        "docker容器": "Docker",
        "k8s": "Kubernetes",
        "linux系统": "Linux"
    }

    return skill_map.get(skill.lower(), skill)


def _generate_summary(data: dict) -> str:
    """
    根据提取的数据生成摘要
    """
    parts = []

    if data.get("current_title"):
        parts.append(f"具有{data['current_title']}经验")

    if data.get("years_exp"):
        parts.append(f"{data['years_exp']}工作经验")

    if data.get("skills"):
        skills = data["skills"][:5]
        parts.append(f"擅长{', '.join(skills)}")

    if data.get("work_experience"):
        exp_count = len(data["work_experience"])
        parts.append(f"有{exp_count}段工作经历")

    if parts:
        return f"{'，'.join(parts)}。"
    else:
        return "简历信息已解析，详细内容请查看各字段。"


# ── 推荐理由 ──────────────────────────────────────────────

SYSTEM_RECOMMEND_PROMPT = """\
你是一名人事部门的专业顾问。请根据候选人的简历摘要，客观分析其与指定岗位需求的匹配度。

要求：
1. 必须明确表态：如果候选人的技能、经验与岗位不匹配，请直接说"不合适"，不要一味推荐。
2. 分析维度：对比候选人的技能栈、行业经验、工作年限与岗位需求的差异。
3. 给出结论：以 JSON 格式返回，不要输出其他内容。

请严格按以下 JSON Schema 返回：
{
    "suitable": true 或 false,
    "score": 0-100 之间的匹配分数,
    "conclusion": "一句话总结是否合适",
    "reason": "2-3句话详细说明为什么合适或不合适，具体指出技能、经验等方面的匹配或不匹配之处"
}
"""


def generate_recommendation(resume_summary: str, query: str) -> dict:
    """生成岗位匹配度分析（结构化返回）"""
    try:
        client = get_client()
        response = client.messages.create(
            model=settings.model,
            max_tokens=512,
            system=SYSTEM_RECOMMEND_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"岗位需求: {query}\n\n候选人摘要: {resume_summary}\n\n请分析该候选人是否适合此岗位。"
                }
            ],
        )
        raw = _extract_text(response)
        if raw:
            # 清理可能的 markdown 代码块
            raw = _clean_json_response(raw)
            return json.loads(raw)
    except Exception:
        logger.exception("推荐理由生成失败")
    return {
        "suitable": False,
        "score": 0,
        "conclusion": "无法生成分析结果",
        "reason": "AI 服务暂时不可用，请稍后再试。",
    }


def build_candidates_context(candidates: list, max_count: int = 10) -> str:
    """将搜索结果格式化为 AI 对话可用的候选人上下文文本"""
    if not candidates:
        return "（人才库中暂无匹配的候选人）"

    lines = []
    for item in candidates[:max_count]:
        r = item.resume
        parts = []
        if r.name:
            parts.append(f"姓名: {r.name}")
        if r.current_title:
            parts.append(f"职位: {r.current_title}")
        if r.years_exp:
            parts.append(f"经验: {r.years_exp}")
        if r.skills:
            parts.append(f"技能: {', '.join(r.skills[:8])}")
        if r.summary_text:
            parts.append(f"简介: {r.summary_text}")
        if item.score > 0:
            parts.append(f"匹配度: {item.score:.0%}")
        lines.append(" | ".join(parts))

    return "\n".join(lines)


# 推荐意图关键词：用于判断是否需要检索人才库
RECOMMEND_INTENT_KEYWORDS = [
    "推荐", "筛选", "找", "有哪些", "多少人", "几个",
    "合适", "匹配", "谁有", "有没有", "人才库", "候选人",
    "Java", "Python", "前端", "后端", "开发", "测试", "运维",
]


def _is_recommendation_intent(text: str) -> bool:
    """判断用户消息是否为候选人检索意图"""
    return any(kw in text for kw in RECOMMEND_INTENT_KEYWORDS)


def chat_completion(messages: list[dict], resume_context: Optional[str] = None) -> str:
    """AI 对话（人事客服），支持上下文"""
    try:
        client = get_client()
        system_prompt = "你是一名人事部门 AI 助手，负责解答关于候选人和人才库的问题。回答要简洁专业。"
        if resume_context:
            system_prompt += f"\n\n当前讨论的候选人信息: {resume_context}"

        response = client.messages.create(
            model=settings.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return _extract_text(response) or "抱歉，我暂时无法回答这个问题，请稍后再试。"
    except Exception:
        logger.exception("AI 对话失败")
        return "抱歉，我暂时无法回答这个问题，请稍后再试。"
