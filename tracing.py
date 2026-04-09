"""
Aura 可观测性模块
- 本地 JSON 文件追踪：每次请求记录 route → tools → latency → response
- 可选 LangSmith 集成：设置 LANGCHAIN_TRACING_V2=true + LANGCHAIN_API_KEY 即可启用
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

TRACE_DIR = Path("traces")


def _ensure_trace_dir():
    TRACE_DIR.mkdir(exist_ok=True)


def setup_langsmith():
    """如果环境变量已配置，自动启用 LangSmith tracing"""
    if os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true" and os.getenv("LANGCHAIN_API_KEY"):
        os.environ.setdefault("LANGCHAIN_PROJECT", "aura-agent")
        return True
    return False


class Tracer:
    """轻量级本地链路追踪"""

    def __init__(self):
        _ensure_trace_dir()
        self.langsmith_enabled = setup_langsmith()

    def start_trace(self, query: str) -> dict:
        return {
            "trace_id": datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
            "query": query,
            "start_time": time.time(),
            "events": [],
        }

    def add_event(self, trace: dict, event_type: str, data: dict | None = None):
        trace["events"].append({
            "type": event_type,
            "ts": time.time() - trace["start_time"],
            "data": data or {},
        })

    def end_trace(self, trace: dict, response: str, route: str = "",
                  tools_used: list | None = None):
        trace["end_time"] = time.time()
        trace["latency_ms"] = round((trace["end_time"] - trace["start_time"]) * 1000, 1)
        trace["response"] = response[:500]
        trace["route"] = route
        trace["tools_used"] = tools_used or []

        filepath = TRACE_DIR / f"{trace['trace_id']}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trace, f, ensure_ascii=False, indent=2, default=str)

        return trace

    def get_recent_traces(self, n: int = 10) -> list[dict]:
        """读取最近 n 条 trace 摘要"""
        files = sorted(TRACE_DIR.glob("*.json"), reverse=True)[:n]
        summaries = []
        for fp in files:
            with open(fp, "r", encoding="utf-8") as f:
                t = json.load(f)
                summaries.append({
                    "trace_id": t.get("trace_id"),
                    "query": t.get("query", "")[:60],
                    "route": t.get("route"),
                    "tools": t.get("tools_used"),
                    "latency_ms": t.get("latency_ms"),
                })
        return summaries
