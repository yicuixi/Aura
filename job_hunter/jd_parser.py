"""
JD 解析器 — 从岗位描述文本中提取结构化需求
"""

import re
from dataclasses import dataclass, field

from .normalizer import normalize_skill, degree_level, parse_experience_years


@dataclass
class JDRequirements:
    """JD 解析后的结构化需求"""
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    min_experience_years: int = 0
    max_experience_years: int = 99
    min_degree: int = -1
    degree_text: str = ""
    raw_text: str = ""


# 技能关键词库 — 用于从非结构化文本中识别技能
# (display_name, need_boundary): need_boundary=True 表示短词需要词边界匹配
_KNOWN_SKILLS: list[tuple[str, bool]] = [
    # 编程语言 (短名需边界)
    ("python", False), ("java", True), ("c++", False), ("c#", False),
    ("c语言", False), ("golang", False), ("go语言", False),
    ("rust", True), ("javascript", False), ("typescript", False),
    ("ruby", True), ("php", True), ("scala", True), ("kotlin", True),
    ("swift", True), ("sql", False), ("shell", True), ("bash", True),
    ("lua", True),
    # 前端
    ("react", True), ("react.js", False), ("reactjs", False),
    ("vue", True), ("vue.js", False), ("vuejs", False),
    ("angular", False), ("next.js", False),
    ("webpack", False), ("vite", True), ("html", False), ("css", False),
    ("tailwind", False), ("electron", False),
    # 后端
    ("spring boot", False), ("springboot", False), ("spring", True),
    ("django", False), ("flask", True), ("fastapi", False),
    ("node.js", False), ("nodejs", False), ("express", True),
    ("gin", True), ("nest.js", False),
    # AI/ML
    ("pytorch", False), ("tensorflow", False), ("keras", False),
    ("scikit-learn", False), ("sklearn", False),
    ("pandas", False), ("numpy", False),
    ("opencv", False), ("langchain", False),
    ("rag", True), ("agent", True), ("mcp", True),
    ("transformer", False), ("huggingface", False),
    ("onnx", False), ("tensorrt", False), ("tensorrt-llm", False),
    ("vllm", False), ("sglang", False), ("ollama", False),
    ("prompt engineering", False),
    ("大模型", False), ("llm", True),
    ("深度学习", False), ("机器学习", False),
    ("自然语言处理", False), ("nlp", True),
    ("计算机视觉", False), ("cv", True),
    ("模型量化", False), ("模型微调", False), ("fine-tune", False),
    # 测试
    ("pytest", False), ("junit", False), ("selenium", False),
    ("playwright", False), ("cypress", False), ("appium", False),
    ("jmeter", False), ("k6", True), ("postman", False),
    ("自动化测试", False), ("性能测试", False), ("接口测试", False),
    ("ui测试", False), ("单元测试", False), ("测试开发", False),
    # DevOps
    ("docker", False), ("kubernetes", False), ("k8s", False),
    ("git", True), ("ci/cd", False), ("cicd", False),
    ("github actions", False), ("jenkins", False),
    ("linux", False), ("nginx", False), ("redis", False),
    ("mongodb", False), ("elasticsearch", False),
    ("kafka", False), ("rabbitmq", False),
    ("grpc", False), ("graphql", False), ("restful", False),
    ("jira", False), ("confluence", False),
    # 云
    ("aws", True), ("gcp", True), ("azure", False),
    ("阿里云", False), ("腾讯云", False),
]

# 用于辅助判断"优先/加分"语境的模式
_PREFERRED_CONTEXT = re.compile(
    r"(?:优先|加分|preferred|nice\s*to\s*have|bonus|优选|有.*(?:经验|能力).*(?:优先|加分|更佳))"
)


def _split_sections(text: str) -> dict[str, str]:
    """按常见 JD 标题拆分段落"""
    section_headers = [
        (r"(?:岗位|职位)\s*(?:职责|描述|说明)", "responsibilities"),
        (r"(?:任职|岗位)\s*(?:要求|资格|条件)", "requirements"),
        (r"(?:必备|必须|硬性)\s*(?:条件|要求|技能)", "required"),
        (r"(?:优先|加分|优选)\s*(?:条件|项|要求|技能)", "preferred"),
        (r"(?:福利|待遇|薪资)", "benefits"),
    ]

    sections: dict[str, str] = {"full": text}
    lines = text.split("\n")

    current_section = "preamble"
    section_lines: dict[str, list[str]] = {"preamble": []}

    for line in lines:
        stripped = line.strip().lstrip("#").lstrip("*").strip()
        matched = False
        for pattern, name in section_headers:
            if re.search(pattern, stripped):
                current_section = name
                section_lines.setdefault(name, [])
                matched = True
                break
        if not matched:
            section_lines.setdefault(current_section, []).append(line)

    for name, slines in section_lines.items():
        sections[name] = "\n".join(slines)

    return sections


def _extract_skills_from_text(text: str) -> list[str]:
    """从文本中识别技能关键词，返回归一化后的列表"""
    text_lower = text.lower()
    found = []
    seen = set()

    sorted_skills = sorted(_KNOWN_SKILLS, key=lambda x: len(x[0]), reverse=True)

    for skill_name, need_boundary in sorted_skills:
        skill_lower = skill_name.lower()

        if need_boundary:
            pattern = r'(?<![a-zA-Z\u4e00-\u9fff])' + re.escape(skill_lower) + r'(?![a-zA-Z\u4e00-\u9fff])'
            if not re.search(pattern, text_lower):
                continue
        else:
            if skill_lower not in text_lower:
                continue

        normalized = normalize_skill(skill_name)
        if normalized not in seen:
            found.append(normalized)
            seen.add(normalized)

    return found


def _extract_degree(text: str) -> tuple[int, str]:
    """提取学历要求"""
    degree_patterns = [
        (r"博士及以上", "博士"),
        (r"博士", "博士"),
        (r"硕士及以上", "硕士"),
        (r"硕士|研究生", "硕士"),
        (r"本科及以上|本科以上", "本科"),
        (r"本科", "本科"),
        (r"大专及以上|大专以上", "大专"),
        (r"大专|专科", "大专"),
        (r"(?i)phd|doctor", "博士"),
        (r"(?i)master", "硕士"),
        (r"(?i)bachelor", "本科"),
    ]

    for pattern, label in degree_patterns:
        m = re.search(pattern, text)
        if m:
            return degree_level(label), m.group()

    return -1, ""


def parse_jd(text: str) -> JDRequirements:
    """
    解析 JD 文本，提取结构化需求。
    优先从 requirements/required 段落提取必选技能，
    从 preferred 段落提取优选技能。
    """
    sections = _split_sections(text)
    req = JDRequirements(raw_text=text)

    req_text = sections.get("requirements", "") or sections.get("required", "")
    pref_text = sections.get("preferred", "")

    if req_text:
        req.required_skills = _extract_skills_from_text(req_text)
        if pref_text:
            req.preferred_skills = _extract_skills_from_text(pref_text)
            req.preferred_skills = [
                s for s in req.preferred_skills if s not in req.required_skills
            ]
        else:
            req.preferred_skills = []
    else:
        all_skills = _extract_skills_from_text(text)
        req.required_skills = all_skills
        req.preferred_skills = []

    min_y, max_y = parse_experience_years(text)
    req.min_experience_years = min_y
    req.max_experience_years = max_y

    level, dtxt = _extract_degree(text)
    req.min_degree = level
    req.degree_text = dtxt

    return req
