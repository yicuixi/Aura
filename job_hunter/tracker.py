"""
投递跟踪 — SQLite 存储 + CSV 导出
"""

import csv
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import DB_PATH, DATA_DIR
from .models import Job

logger = logging.getLogger("job_hunter.tracker")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT DEFAULT '',
    salary_range TEXT DEFAULT '',
    description TEXT DEFAULT '',
    requirements TEXT DEFAULT '',
    source TEXT DEFAULT 'boss',
    url TEXT DEFAULT '',
    match_score REAL DEFAULT 0,
    score_reason TEXT DEFAULT '',
    crawled_at TEXT DEFAULT '',
    status TEXT DEFAULT 'new',
    applied_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_score ON jobs(match_score);
"""


class Tracker:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def save_jobs(self, jobs: list[Job]) -> int:
        with self._conn() as conn:
            for j in jobs:
                conn.execute(
                    """INSERT OR REPLACE INTO jobs
                       (id,title,company,location,salary_range,description,
                        requirements,source,url,match_score,score_reason,crawled_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (j.id, j.title, j.company, j.location, j.salary_range,
                     j.description, j.requirements, j.source, j.url,
                     j.match_score, j.score_reason, j.crawled_at),
                )
        return len(jobs)

    def get_jobs(self, min_score: float = 0) -> list[Job]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE match_score >= ? ORDER BY match_score DESC",
                (min_score,),
            ).fetchall()
        return [self._to_job(r) for r in rows]

    def mark_applied(self, job_id: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE jobs SET status='applied', applied_at=? WHERE id=?",
                (datetime.now().isoformat(), job_id),
            )

    def stats(self) -> dict:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            high = conn.execute("SELECT COUNT(*) FROM jobs WHERE match_score>=7").fetchone()[0]
            applied = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='applied'").fetchone()[0]
        return {"total": total, "high_score": high, "applied": applied}

    def export_csv(self, path: Optional[str] = None) -> str:
        out = Path(path) if path else DATA_DIR / f"jobs_{datetime.now():%Y%m%d}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        jobs = self.get_jobs()
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["公司", "岗位", "地点", "薪资", "评分", "理由", "状态", "投递时间", "链接"])
            for j in jobs:
                w.writerow([j.company, j.title, j.location, j.salary_range,
                            j.match_score, j.score_reason, "", "", j.url])
        return str(out)

    def _to_job(self, row: sqlite3.Row) -> Job:
        return Job(
            id=row["id"], title=row["title"], company=row["company"],
            location=row["location"], salary_range=row["salary_range"],
            description=row["description"], requirements=row["requirements"],
            source=row["source"], url=row["url"],
            match_score=row["match_score"], score_reason=row["score_reason"],
            crawled_at=row["crawled_at"],
        )
