"""
简历文本预处理模块
轻量整理策略：保留所有可能有信息的内容，只做最基础的格式规范。
核心原则：宁可保留噪音，不可丢失信息。
"""
import re


def preprocess_resume_text(text: str) -> str:
    """
    轻量整理简历文本，保留原始结构和所有可能有意义的行。

    策略：
    - 仅删除明确无信息的噪音（页码、纯空行）
    - 保留邮箱、电话、姓名、求职意向等所有行
    - 不过度合并行，保持表格/段落的结构边界
    - 只处理连续短行（如从表格单元格拆分的词组）

    Args:
        text: 从 PDF/DOCX/PPTX 中提取的原始文本

    Returns:
        轻量整理后的文本
    """
    if not text or not text.strip():
        return ""

    lines = [line.strip() for line in text.split("\n")]

    # 1. 仅删除明确的无信息噪音
    cleaned_lines = []
    for line in lines:
        # 跳过纯空行
        if not line:
            continue
        # 跳过页码
        if re.match(r"^第\s*\d+\s*[/页]", line):
            continue
        # 跳过仅有"简历"/"个人简历"标题的行
        if re.match(r"^(简历|个人简历|resume|CV)$", line, re.IGNORECASE):
            continue
        # 其余行全部保留（包括邮箱、电话、姓名、求职意向等）
        cleaned_lines.append(line)

    # 2. 轻度合并：仅合并连续的非表格短行
    # 表格提取后的文本可能一行只有一两个词，需要合并
    # 但如果一行很长（>=50字符），说明是完整的一句话，不应合并
    merged_lines = []
    buffer = ""

    for line in cleaned_lines:
        # 长行（完整句子）直接保存 buffer，开始新的行
        if len(line) >= 50:
            if buffer:
                merged_lines.append(buffer)
                buffer = ""
            merged_lines.append(line)
            continue

        # 关键段落标题行直接保存
        if re.search(r"^(教育|工作|项目|技能|自我评价|获奖|求职|联系)", line):
            if buffer:
                merged_lines.append(buffer)
                buffer = ""
            merged_lines.append(line)
            continue

        # 日期行（如"2025.04- 2025.10 (6个月)"）直接保存
        if re.match(r"\d{4}", line):
            if buffer:
                merged_lines.append(buffer)
                buffer = ""
            merged_lines.append(line)
            continue

        # 短行累积
        if buffer:
            buffer = f"{buffer} {line}"
        else:
            buffer = line

    if buffer:
        merged_lines.append(buffer)

    # 3. 清理多余空格（但不改标点）
    result_lines = []
    for line in merged_lines:
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            result_lines.append(line)

    return "\n".join(result_lines)


def extract_key_sections(text: str) -> dict:
    """
    尝试提取简历的关键段落，为 AI 提供额外上下文。

    Args:
        text: 预处理后的文本

    Returns:
        包含各段落标签的字典
    """
    sections = {
        "contact_info": "",
        "education": "",
        "work": "",
        "skills": "",
        "summary": "",
    }

    # 常见简历段落标记（扩展匹配范围）
    patterns = {
        "contact_info": r"(联系方式|联系信息|个人信息|手机|邮箱|电话)[：:\s]",
        "education": r"(教育背景|教育经历|学历|学习经历)[：:\s]",
        "work": r"(工作经历|工作经验|实习经历|工作履历)[：:\s]",
        "skills": r"(专业技能|技术技能|技能专长|个人技能|技能)[：:\s]",
        "summary": r"(自我评价|个人总结|项目经历|个人优势|核心优势)[：:\s]",
    }

    lines = text.split("\n")
    current_section = "unknown"

    for line in lines:
        # 检查是否为新的段落开始
        section_found = False
        for section_name, pattern in patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                current_section = section_name
                sections[section_name] = line
                section_found = True
                break

        if not section_found and current_section in sections:
            # 继续累积到当前段落
            sections[current_section] += f" {line}"

    return sections
