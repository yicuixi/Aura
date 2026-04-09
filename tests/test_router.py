"""Adaptive RAG 路由器单元测试"""

import pytest
from unittest.mock import MagicMock, patch


def _make_router(llm_response: str):
    """构造一个带 mock LLM 的 QueryRouter"""
    from aura_react import QueryRouter

    mock_llm = MagicMock()
    router = QueryRouter(mock_llm)

    mock_result = MagicMock()
    mock_result.content = llm_response
    router.chain = MagicMock()
    router.chain.invoke = MagicMock(return_value=mock_result)
    return router


class TestQueryRouter:
    def test_route_retrieve(self):
        router = _make_router("RETRIEVE")
        assert router.route("查一下我论文里关于 GAN 的内容") == "RETRIEVE"

    def test_route_tool(self):
        router = _make_router("TOOL")
        assert router.route("今天北京天气怎么样") == "TOOL"

    def test_route_direct(self):
        router = _make_router("DIRECT")
        assert router.route("1+1等于几") == "DIRECT"

    def test_route_case_insensitive(self):
        router = _make_router("  retrieve  ")
        assert router.route("test") == "RETRIEVE"

    def test_route_with_explanation(self):
        """LLM 返回带解释的文本，仍能正确提取路由"""
        router = _make_router("This query needs TOOL because it asks about weather")
        assert router.route("天气") == "TOOL"

    def test_route_fallback_on_garbage(self):
        """LLM 返回无法解析的内容时兜底到 RETRIEVE"""
        router = _make_router("I don't know what to do")
        assert router.route("test") == "RETRIEVE"

    def test_route_fallback_on_exception(self):
        from aura_react import QueryRouter
        mock_llm = MagicMock()
        router = QueryRouter(mock_llm)
        router.chain = MagicMock()
        router.chain.invoke = MagicMock(side_effect=RuntimeError("LLM down"))

        assert router.route("test") == "RETRIEVE"

    def test_route_prefers_first_match(self):
        """如果 LLM 同时出现多个关键词，取第一个匹配"""
        router = _make_router("RETRIEVE or maybe TOOL")
        assert router.route("test") == "RETRIEVE"
