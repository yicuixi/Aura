"""
多维度匹配评分器 — 规则引擎 + 可选 LLM 增强

评分维度与权重:
  - 技能匹配 (required):  35%
  - 技能匹配 (preferred): 15%
  - 经验匹配:              20%
  - 学历匹配:              15%
  - 偏好匹配 (地点/行业):  10%
  - 加分项:                 5%

每个维度 0-100 分，加权求和得总分 (0-10 映射)。
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from .config import Config, load_resume_data
from .jd_parser import JDRequirements, parse_jd
from .models import Job, ScoreDetail
from .normalizer import (
    normalize_skill,
    normalize_skills,
    degree_level,
    normalize_school,
    parse_experience_years,
)

logger = logging.getLogger("job_hunter.scorer")


@dataclass
class _ResumeProfile:
    """从 YAML 简历构建的结构化档案"""
    all_skills: set[str] = field(default_factory=set)
    education: list[dict] = field(default_factory=list)
    max_degree: int = 0
    is_985: bool = False
    is_211: bool = False
    experience_years: float = 0.0
    experience_entries: list[dict] = field(default_factory=list)
    target_positions: list[str] = field(default_factory=list)
    target_locations: list[str] = field(default_factory=list)
    industry_preference: list[str] = field(default_factory=list)
    min_salary: float = 0
    awards: list[str] = field(default_factory=list)
    languages: list[dict] = field(default_factory=list)


def _build_profile(resume: dict) -> _ResumeProfile:
    """从简历 YAML 数据构建 _ResumeProfile"""
    p = _ResumeProfile()

    skills_section = resume.get("skills", {})
    raw_skills = []
    for group_name, items in skills_section.items():
        if isinstance(items, list):
            raw_skills.extend(items)
    p.all_skills = normalize_skills(raw_skills)

    # 复合技能拆解：从 "Playwright UI自动化" 中同时提取 playwright + 自动化测试
    from .jd_parser import _extract_skills_from_text
    for raw in raw_skills:
        for extracted in _extract_skills_from_text(raw):
            p.all_skills.add(extracted)

    # 从工作/项目经历中提取隐含技能
    text_blocks = []
    for exp in resume.get("experience", []):
        text_blocks.extend(exp.get("highlights", []))
    for proj in resume.get("projects", []):
        text_blocks.extend(proj.get("highlights", []))

    for block in text_blocks:
        for extracted in _extract_skills_from_text(block):
            p.all_skills.add(extracted)

    for edu in resume.get("education", []):
        p.education.append(edu)
        dlevel = degree_level(edu.get("degree", ""))
        if dlevel > p.max_degree:
            p.max_degree = dlevel
        if edu.get("is_985"):
            p.is_985 = True
        if edu.get("is_211"):
            p.is_211 = True

    p.experience_entries = resume.get("experience", [])
    total_months = 0
    for exp in p.experience_entries:
        start = exp.get("start_date", "")
        end = exp.get("end_date", "")
        months = _calc_months(start, end)
        total_months += months
    p.experience_years = round(total_months / 12, 1)

    prefs = resume.get("preferences", resume.get("job_preferences", {}))
    p.target_positions = prefs.get("target_positions", [])
    p.target_locations = prefs.get("target_locations", [])
    p.industry_preference = prefs.get("industry_preference", [])
    p.min_salary = prefs.get("min_salary", 0)

    p.awards = resume.get("awards", [])
    p.languages = resume.get("languages", [])

    return p


def _calc_months(start: str, end: str) -> int:
    """计算两个日期之间的月数"""
    import re
    from datetime import datetime

    def parse_date(s: str):
        s = s.strip()
        if not s or s in ("至今", "present", "now", ""):
            return datetime.now()
        m = re.match(r"(\d{4})[-/.](\d{1,2})", s)
        if m:
            return datetime(int(m.group(1)), int(m.group(2)), 1)
        m2 = re.match(r"(\d{4})", s)
        if m2:
            return datetime(int(m2.group(1)), 1, 1)
        return None

    d1, d2 = parse_date(start), parse_date(end)
    if not d1 or not d2:
        return 0
    delta = (d2.year - d1.year) * 12 + (d2.month - d1.month)
    return max(delta, 0)


def _parse_salary_range(salary_text: str) -> tuple[float, float]:
    """解析薪资文本，返回 (min_k, max_k) 单位千/月"""
    if not salary_text:
        return 0, 0
    text = salary_text.replace("，", "").replace(",", "")

    m = re.search(r"(\d+\.?\d*)\s*[-~到至]\s*(\d+\.?\d*)\s*[kK千]", text)
    if m:
        return float(m.group(1)), float(m.group(2))

    m = re.search(r"(\d+\.?\d*)\s*[-~到至]\s*(\d+\.?\d*)\s*万", text)
    if m:
        return float(m.group(1)) * 10, float(m.group(2)) * 10

    m = re.search(r"(\d+\.?\d*)\s*[kK千]", text)
    if m:
        return float(m.group(1)), float(m.group(1))

    return 0, 0


# ─── 各维度评分函数 ───


def _score_required_skills(profile: _ResumeProfile, jd: JDRequirements) -> ScoreDetail:
    """必选技能匹配"""
    detail = ScoreDetail(dimension="必选技能", weight=0.35)

    if not jd.required_skills:
        detail.score = 70
        detail.reason = "JD未明确列出必选技能，给予基准分"
        return detail

    matched = []
    missing = []
    for skill in jd.required_skills:
        if skill in profile.all_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    ratio = len(matched) / len(jd.required_skills)
    detail.score = min(ratio * 100, 100)

    matched_str = ", ".join(matched) if matched else "无"
    missing_str = ", ".join(missing) if missing else "无"
    detail.reason = (
        f"匹配 {len(matched)}/{len(jd.required_skills)} 项: "
        f"命中[{matched_str}], 缺失[{missing_str}]"
    )
    return detail


def _score_preferred_skills(profile: _ResumeProfile, jd: JDRequirements) -> ScoreDetail:
    """优选技能匹配"""
    detail = ScoreDetail(dimension="优选技能", weight=0.15)

    if not jd.preferred_skills:
        detail.score = 50
        detail.reason = "JD未列出优选技能"
        return detail

    matched = [s for s in jd.preferred_skills if s in profile.all_skills]
    ratio = len(matched) / len(jd.preferred_skills)
    detail.score = min(ratio * 100, 100)
    detail.reason = f"匹配 {len(matched)}/{len(jd.preferred_skills)} 项优选技能"
    return detail


def _score_experience(profile: _ResumeProfile, jd: JDRequirements) -> ScoreDetail:
    """经验年限匹配"""
    detail = ScoreDetail(dimension="工作经验", weight=0.20)
    actual = profile.experience_years
    req_min = jd.min_experience_years
    req_max = jd.max_experience_years

    if req_min == 0 and req_max >= 99:
        detail.score = 80
        detail.reason = f"不限经验，当前 {actual} 年"
        return detail

    if req_min <= actual <= req_max:
        detail.score = 100
        detail.reason = f"完全匹配: 要求 {req_min}-{req_max} 年，实际 {actual} 年"
    elif actual < req_min:
        gap = req_min - actual
        detail.score = max(100 - gap * 25, 10)
        detail.reason = f"经验不足: 要求 ≥{req_min} 年，实际 {actual} 年 (差 {gap} 年)"
    else:
        detail.score = max(80 - (actual - req_max) * 5, 50)
        detail.reason = f"经验超出范围: 要求 ≤{req_max} 年，实际 {actual} 年"

    return detail


def _score_education(profile: _ResumeProfile, jd: JDRequirements) -> ScoreDetail:
    """学历匹配"""
    detail = ScoreDetail(dimension="学历背景", weight=0.15)

    if jd.min_degree < 0:
        detail.score = 70
        detail.reason = "JD未明确学历要求"
        if profile.is_985:
            detail.score = 85
            detail.reason += "，985院校加分"
        elif profile.is_211:
            detail.score = 80
            detail.reason += "，211院校加分"
        return detail

    if profile.max_degree >= jd.min_degree:
        detail.score = 80
        detail.reason = f"学历满足: 要求{jd.degree_text}，持有{_degree_name(profile.max_degree)}"
        if profile.is_985:
            detail.score = 100
            detail.reason += " (985院校)"
        elif profile.is_211:
            detail.score = 95
            detail.reason += " (211院校)"
    else:
        detail.score = 30
        detail.reason = (
            f"学历不足: 要求{jd.degree_text}，"
            f"持有{_degree_name(profile.max_degree)}"
        )

    return detail


def _degree_name(level: int) -> str:
    return {4: "博士", 3: "硕士", 2: "本科", 1: "大专", 0: "高中"}.get(level, "未知")


def _score_preferences(profile: _ResumeProfile, job: Job) -> ScoreDetail:
    """地点/行业/薪资偏好匹配"""
    detail = ScoreDetail(dimension="偏好匹配", weight=0.10)
    score = 50
    reasons = []

    if profile.target_locations and job.location:
        loc_match = any(loc in job.location for loc in profile.target_locations)
        if loc_match:
            score += 20
            reasons.append(f"地点匹配({job.location})")
        else:
            score -= 10
            reasons.append(f"地点不匹配({job.location})")

    if job.salary_range:
        sal_min, sal_max = _parse_salary_range(job.salary_range)
        if sal_max > 0:
            if sal_max >= profile.min_salary:
                score += 15
                reasons.append(f"薪资达标({job.salary_range})")
            else:
                score -= 15
                reasons.append(f"薪资偏低({job.salary_range})")

    if profile.target_positions:
        title_lower = job.title.lower()
        pos_match = any(
            pos.lower() in title_lower or title_lower in pos.lower()
            for pos in profile.target_positions
        )
        if pos_match:
            score += 15
            reasons.append(f"岗位方向匹配({job.title})")

    detail.score = max(min(score, 100), 0)
    detail.reason = "; ".join(reasons) if reasons else "信息不足无法判断"
    return detail


def _score_bonus(profile: _ResumeProfile, jd: JDRequirements) -> ScoreDetail:
    """加分项: 奖项、语言能力、开源贡献等"""
    detail = ScoreDetail(dimension="加分项", weight=0.05)
    score = 0
    reasons = []

    if profile.awards:
        national = sum(1 for a in profile.awards if "国家" in a or "全国" in a)
        if national:
            score += 40
            reasons.append(f"{national}项国家级奖项")
        if len(profile.awards) > national:
            score += 20
            reasons.append(f"{len(profile.awards) - national}项其他奖项")

    if profile.languages:
        for lang in profile.languages:
            name = lang.get("name", "")
            level = lang.get("level", "")
            if "cet-6" in level.lower() or "n1" in level.lower() or "ielts" in level.lower():
                score += 15
                reasons.append(f"{name}({level})")

    jd_text = jd.raw_text.lower()
    if "开源" in jd_text or "open source" in jd_text:
        for skill in profile.all_skills:
            if "开源" in skill:
                score += 10
                reasons.append("有开源贡献")
                break

    detail.score = min(score, 100)
    detail.reason = "; ".join(reasons) if reasons else "无明显加分项"
    return detail


# ─── 主评分器 ───


class JobScorer:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
        self.resume = load_resume_data()
        self._profile = _build_profile(self.resume)
        self._llm = None

        logger.info(
            f"评分器初始化: {len(self._profile.all_skills)} 项技能, "
            f"{self._profile.experience_years} 年经验, "
            f"学历={_degree_name(self._profile.max_degree)}"
        )

    def _get_llm(self):
        if self._llm is None:
            from langchain_ollama import ChatOllama
            self._llm = ChatOllama(
                model=self.config.model,
                base_url=self.config.ollama_url,
                temperature=0.1,
                num_ctx=self.config.num_ctx,
            )
        return self._llm

    def score(self, job: Job) -> Job:
        """对单个岗位进行多维度评分"""
        jd_text = (job.description or "") + "\n" + (job.requirements or "")
        jd = parse_jd(jd_text)

        details = [
            _score_required_skills(self._profile, jd),
            _score_preferred_skills(self._profile, jd),
            _score_experience(self._profile, jd),
            _score_education(self._profile, jd),
            _score_preferences(self._profile, job),
            _score_bonus(self._profile, jd),
        ]

        total_weighted = sum(d.score * d.weight for d in details)
        job.match_score = round(total_weighted / 10, 1)  # 映射到 0-10
        job.score_details = details
        job.score_reason = self._build_reason(details, job.match_score)

        logger.info(
            f"  {job.match_score:.1f}/10 | {job.company} | {job.title} | "
            f"技能{details[0].score:.0f} 经验{details[2].score:.0f} "
            f"学历{details[3].score:.0f}"
        )

        return job

    def _build_reason(self, details: list[ScoreDetail], total: float) -> str:
        """生成可读的评分摘要"""
        top = sorted(details, key=lambda d: d.score * d.weight, reverse=True)
        strengths = [d for d in top if d.score >= 70]
        weaknesses = [d for d in top if d.score < 50]

        parts = []
        if strengths:
            s_names = [f"{d.dimension}({d.score:.0f})" for d in strengths[:3]]
            parts.append(f"优势: {', '.join(s_names)}")
        if weaknesses:
            w_names = [f"{d.dimension}({d.score:.0f})" for d in weaknesses[:2]]
            parts.append(f"短板: {', '.join(w_names)}")
        return "; ".join(parts) if parts else f"综合评分 {total:.1f}"

    def score_all(self, jobs: list[Job]) -> list[Job]:
        """批量评分并按总分降序排列"""
        for i, job in enumerate(jobs):
            logger.info(f"评分 {i+1}/{len(jobs)}: {job.company} - {job.title}")
            self.score(job)
        return sorted(jobs, key=lambda j: j.match_score, reverse=True)

    def explain(self, job: Job) -> str:
        """输出某个岗位的详细评分报告"""
        lines = [
            f"{'='*50}",
            f"岗位: {job.company} - {job.title}",
            f"总分: {job.match_score}/10",
            f"{'='*50}",
        ]
        for d in job.score_details:
            filled = int(d.score / 5)
            bar = "#" * filled + "-" * (20 - filled)
            lines.append(
                f"  [{d.dimension}] {d.score:.0f}/100 (权重{d.weight:.0%}) "
                f"|{bar}|"
            )
            lines.append(f"    → {d.reason}")

        if job.risk_flags:
            lines.append(f"\n  ⚠ 风险: {'; '.join(job.risk_flags)}")

        lines.append(f"\n  综述: {job.score_reason}")
        return "\n".join(lines)
