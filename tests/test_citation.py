"""Citation 溯源功能单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace


@pytest.fixture
def rag_system():
    """构造一个不依赖真实 embedding / Chroma 的 RAGSystem"""
    with patch("rag.HuggingFaceEmbeddings"), \
         patch("rag.Chroma"), \
         patch("rag.CrossEncoder"):
        from rag import RAGSystem
        system = RAGSystem(persist_directory="test_db", enable_reranker=False)
        return system


def _make_doc(content: str, source: str):
    return SimpleNamespace(
        page_content=content,
        metadata={"source": source},
    )


class TestHybridSearchWithSources:
    def test_returns_citation_format(self, rag_system):
        fake_docs = [
            _make_doc("Python 是一门解释型语言", "/data/python_intro.md"),
            _make_doc("LangChain 提供了 Agent 框架", "/data/langchain.md"),
        ]
        rag_system.hybrid_search = MagicMock(return_value=fake_docs)

        results = rag_system.hybrid_search_with_sources("什么是 Python", k=2)

        assert len(results) == 2
        assert results[0]["index"] == 1
        assert results[0]["source"] == "python_intro.md"
        assert results[0]["full_path"] == "/data/python_intro.md"
        assert "Python" in results[0]["content"]

    def test_empty_results(self, rag_system):
        rag_system.hybrid_search = MagicMock(return_value=[])

        results = rag_system.hybrid_search_with_sources("不存在的内容")
        assert results == []

    def test_unknown_source_fallback(self, rag_system):
        fake_docs = [_make_doc("无来源内容", "")]
        # metadata 没有 source 的情况
        fake_docs[0].metadata = {}
        rag_system.hybrid_search = MagicMock(return_value=fake_docs)

        results = rag_system.hybrid_search_with_sources("test")
        assert results[0]["source"] == "unknown"

    def test_respects_k_parameter(self, rag_system):
        fake_docs = [_make_doc(f"doc {i}", f"/data/d{i}.md") for i in range(5)]
        rag_system.hybrid_search = MagicMock(return_value=fake_docs[:3])

        results = rag_system.hybrid_search_with_sources("test", k=3)
        assert len(results) == 3
        rag_system.hybrid_search.assert_called_once_with("test", k=3, use_rerank=True)
