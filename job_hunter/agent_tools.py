"""
JobHunter 工具集 — 注册为 Aura Agent 的 Tools
"""

import asyncio
import json
import logging

from .config import Config, load_resume_data
from .crawler import crawl_boss
from .scorer import JobScorer
from .form_filler import FormFiller
from .tracker import Tracker

logger = logging.getLogger("job_hunter.tools")

_config = None
_tracker = None


def _cfg():
    global _config
    if not _config:
        _config = Config.load()
    return _config


def _trk():
    global _tracker
    if not _tracker:
        _tracker = Tracker()
    return _tracker


def crawl_jobs(query: str) -> str:
    """爬取招聘岗位。输入：搜索词如'测试开发 上海'，或留空用默认配置。"""
    cfg = _cfg()
    if query.strip():
        parts = query.strip().split()
        cfg.target_positions = [parts[0]]
        if len(parts) > 1:
            cfg.target_locations = [parts[1]]

    try:
        jobs = asyncio.run(crawl_boss(cfg))
        if not jobs:
            return "未找到岗位"
        _trk().save_jobs(jobs)
        lines = [f"找到 {len(jobs)} 个岗位:"]
        for j in jobs[:15]:
            lines.append(f"  {j.company} | {j.title} | {j.salary_range} | {j.location}")
        return "\n".join(lines)
    except Exception as e:
        return f"爬取失败: {e}"


def score_jobs(query: str) -> str:
    """对已爬取岗位AI评分。输入：'all'全部，'top'只看高分。"""
    try:
        jobs = _trk().get_jobs()
        if not jobs:
            return "没有岗位，请先爬取"
        unscored = [j for j in jobs if j.match_score == 0]
        if unscored:
            scorer = JobScorer(_cfg())
            scorer.score_all(unscored)
            _trk().save_jobs(unscored)
            jobs = _trk().get_jobs()
        if "top" in query.lower():
            jobs = [j for j in jobs if j.match_score >= _cfg().min_score]
        if not jobs:
            return "没有高分岗位"
        lines = [f"{'分数':>4} | {'公司':<16} | {'岗位':<20} | 理由"]
        for j in jobs[:15]:
            lines.append(f"{j.match_score:>4.1f} | {j.company:<16} | {j.title:<20} | {j.score_reason[:25]}")
        return "\n".join(lines)
    except Exception as e:
        return f"评分失败: {e}"


def fill_form(url: str) -> str:
    """自动填写网页求职表单。输入：目标URL。会打开浏览器AI填写，填完等人工确认。"""
    try:
        filler = FormFiller(_cfg())
        result = asyncio.run(filler.fill(url))
        return result["message"]
    except Exception as e:
        return f"填写失败: {e}"


def job_stats(query: str) -> str:
    """投递统计。输入：'stats'看统计，'export'导出CSV。"""
    try:
        if "export" in query.lower():
            return f"已导出: {_trk().export_csv()}"
        s = _trk().stats()
        return f"岗位总数: {s['total']} | 高分(≥7): {s['high_score']} | 已投递: {s['applied']}"
    except Exception as e:
        return f"查询失败: {e}"


def get_langchain_tools():
    """返回 Aura Agent 可直接使用的 Tool 列表"""
    from langchain_core.tools import Tool
    return [
        Tool(name="crawl_jobs", func=crawl_jobs,
             description="爬取招聘岗位信息。输入搜索词如'测试开发 上海'"),
        Tool(name="score_jobs", func=score_jobs,
             description="对岗位AI匹配评分(1-10)。输入'all'或'top'"),
        Tool(name="fill_form", func=fill_form,
             description="自动填写网页求职表单。输入目标URL"),
        Tool(name="job_stats", func=job_stats,
             description="投递统计。输入'stats'或'export'"),
    ]
