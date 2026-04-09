"""可观测性 Tracer 单元测试"""

import json
import os
import pytest
from pathlib import Path


@pytest.fixture
def trace_dir(tmp_path, monkeypatch):
    """把 trace 目录指向临时目录，避免污染项目"""
    import tracing
    monkeypatch.setattr(tracing, "TRACE_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def tracer(trace_dir):
    from tracing import Tracer
    return Tracer()


class TestTracer:
    def test_start_trace_returns_dict(self, tracer):
        trace = tracer.start_trace("hello")
        assert trace["query"] == "hello"
        assert "trace_id" in trace
        assert "start_time" in trace
        assert trace["events"] == []

    def test_add_event(self, tracer):
        trace = tracer.start_trace("q")
        tracer.add_event(trace, "route", {"route": "RETRIEVE"})
        assert len(trace["events"]) == 1
        assert trace["events"][0]["type"] == "route"
        assert trace["events"][0]["data"]["route"] == "RETRIEVE"
        assert trace["events"][0]["ts"] >= 0

    def test_end_trace_writes_json(self, tracer, trace_dir):
        trace = tracer.start_trace("test query")
        tracer.add_event(trace, "route", {"route": "DIRECT"})
        finished = tracer.end_trace(trace, "test response", route="DIRECT", tools_used=[])

        assert finished["latency_ms"] >= 0
        assert finished["response"] == "test response"
        assert finished["route"] == "DIRECT"

        json_files = list(trace_dir.glob("*.json"))
        assert len(json_files) == 1

        with open(json_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["query"] == "test query"
        assert data["route"] == "DIRECT"

    def test_end_trace_truncates_long_response(self, tracer, trace_dir):
        long_resp = "x" * 1000
        trace = tracer.start_trace("q")
        finished = tracer.end_trace(trace, long_resp)
        assert len(finished["response"]) == 500

    def test_get_recent_traces(self, tracer, trace_dir):
        for i in range(5):
            t = tracer.start_trace(f"query_{i}")
            tracer.end_trace(t, f"resp_{i}", route="DIRECT")

        recent = tracer.get_recent_traces(n=3)
        assert len(recent) == 3
        for item in recent:
            assert "trace_id" in item
            assert "query" in item
            assert "latency_ms" in item

    def test_get_recent_traces_empty(self, tracer, trace_dir):
        assert tracer.get_recent_traces() == []


class TestLangSmithSetup:
    def test_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
        monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
        from tracing import setup_langsmith
        assert setup_langsmith() is False

    def test_enabled_with_env_vars(self, monkeypatch):
        monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
        monkeypatch.setenv("LANGCHAIN_API_KEY", "fake-key")
        from tracing import setup_langsmith
        assert setup_langsmith() is True
        assert os.environ.get("LANGCHAIN_PROJECT") == "aura-agent"
