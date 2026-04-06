"""
数据模型 — 只保留必要的
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib


def make_job_id(source: str, company: str, title: str) -> str:
    return hashlib.md5(f"{source}:{company}:{title}".encode()).hexdigest()[:12]


@dataclass
class ScoreDetail:
    """单个评分维度的结果"""
    dimension: str = ""
    weight: float = 0.0
    score: float = 0.0
    reason: str = ""

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str = ""
    salary_range: str = ""
    description: str = ""
    requirements: str = ""
    source: str = "boss"
    url: str = ""
    match_score: float = 0.0
    score_reason: str = ""
    score_details: list[ScoreDetail] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    crawled_at: str = field(default_factory=lambda: datetime.now().isoformat())
