"""
JobHunter 配置 — 扁平化，一个 dataclass 搞定
"""

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

JOB_HUNTER_DIR = Path(__file__).parent
DATA_DIR = JOB_HUNTER_DIR / "data"
DB_PATH = DATA_DIR / "job_hunter.db"
RESUME_DATA_PATH = JOB_HUNTER_DIR / "resume_data.yaml"

# Windows 系统 Edge 路径（Chromium 内核，免下载）
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


@dataclass
class Config:
    # LLM
    model: str = "qwen3:4b"
    ollama_url: str = "http://localhost:11434"
    temperature: float = 0.3
    num_ctx: int = 32000

    # 爬取
    target_positions: list = field(default_factory=lambda: [
        "测试开发工程师", "AI工程师", "Python开发工程师",
    ])
    target_locations: list = field(default_factory=lambda: ["上海", "杭州", "北京"])
    max_pages: int = 3

    # 评分
    min_score: float = 7.0

    # 填表
    headless: bool = False
    browser_path: str = EDGE_PATH
    cdp_url: str = "http://localhost:9222"

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        p = Path(path) if path else JOB_HUNTER_DIR / "config.yaml"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

    def save(self, path: Optional[str] = None):
        p = Path(path) if path else JOB_HUNTER_DIR / "config.yaml"
        p.parent.mkdir(parents=True, exist_ok=True)
        from dataclasses import asdict
        with open(p, "w", encoding="utf-8") as f:
            yaml.dump(asdict(self), f, allow_unicode=True, default_flow_style=False)


def load_resume_data(path: Optional[str] = None) -> dict:
    resume_path = Path(path) if path else RESUME_DATA_PATH
    if not resume_path.exists():
        raise FileNotFoundError(
            f"简历数据不存在: {resume_path}\n"
            "请复制 resume_data.example.yaml 为 resume_data.yaml 并填入真实信息"
        )
    with open(resume_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
