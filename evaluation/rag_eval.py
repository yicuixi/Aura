"""
RAG系统评估模块
评估指标：
- Hit Rate@K: Top-K结果中是否包含相关文档
- MRR (Mean Reciprocal Rank): 相关文档排在第几位
- Recall@K: 召回了多少相关文档
- Faithfulness: 回答是否基于检索内容（LLM评估）
- Answer Relevance: 回答是否切题（LLM评估）
"""

import json
import re
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RetrievalResult:
    """检索评估结果"""
    query: str
    relevant_docs: List[str]
    retrieved_sources: List[str]
    hit: bool
    reciprocal_rank: float
    recall: float
    retrieval_time_ms: float


@dataclass 
class GenerationResult:
    """生成评估结果"""
    query: str
    answer: str
    context: str
    faithfulness_score: float
    relevance_score: float
    generation_time_ms: float


@dataclass
class RAGEvalResults:
    """RAG整体评估结果"""
    # 检索指标
    hit_rate: float = 0.0
    mrr: float = 0.0
    avg_recall: float = 0.0
    avg_retrieval_time_ms: float = 0.0
    
    # 生成指标
    avg_faithfulness: float = 0.0
    avg_relevance: float = 0.0
    avg_generation_time_ms: float = 0.0
    
    # 详细结果
    retrieval_results: List[RetrievalResult] = field(default_factory=list)
    generation_results: List[GenerationResult] = field(default_factory=list)
    
    # 元数据
    total_cases: int = 0
    evaluation_time: str = ""


class RAGEvaluator:
    """RAG系统评估器"""
    
    def __init__(self, rag_system, retrieval_qa=None, llm=None, agent=None):
        """
        初始化RAG评估器
        
        Args:
            rag_system: RAGSystem实例，用于检索评估
            retrieval_qa: RetrievalQA链，用于生成评估（可选）
            llm: LLM实例，用于自动评估生成质量（可选）
            agent: Agent实例，用于生成回答进行评估（可选）
        """
        self.rag = rag_system
        self.retrieval_qa = retrieval_qa
        self.llm = llm
        self.agent = agent
        self.results = RAGEvalResults()
    
    def evaluate_retrieval(self, test_cases: List[Dict], k: int = 3) -> Dict[str, Any]:
        """
        评估检索质量
        
        Args:
            test_cases: 测试用例列表，每个用例包含：
                - question: 查询问题
                - relevant_docs: 相关文档列表（文件名或路径片段）
            k: Top-K检索数量
            
        Returns:
            包含hit_rate, mrr, avg_recall等指标的字典
        """
        hit_count = 0
        mrr_sum = 0.0
        recall_sum = 0.0
        total_time = 0.0
        retrieval_results = []
        
        for case in test_cases:
            query = case["question"]
            relevant_docs = case.get("relevant_docs", [])
            
            # 记录检索时间
            start_time = time.time()
            
            # 执行检索
            retrieved = self.rag.search(query, k=k)
            
            elapsed_ms = (time.time() - start_time) * 1000
            total_time += elapsed_ms
            
            # 提取检索结果的来源
            retrieved_sources = []
            for doc in retrieved:
                source = doc.metadata.get("source", "")
                if not source:
                    # 尝试从page_content中提取标识
                    source = doc.page_content[:50] if doc.page_content else ""
                retrieved_sources.append(source)
            
            # 计算Hit（是否命中任何相关文档）
            hit = any(
                any(rel.lower() in src.lower() for src in retrieved_sources)
                for rel in relevant_docs
            )
            if hit:
                hit_count += 1
            
            # 计算MRR（Mean Reciprocal Rank）
            reciprocal_rank = 0.0
            for i, src in enumerate(retrieved_sources):
                if any(rel.lower() in src.lower() for rel in relevant_docs):
                    reciprocal_rank = 1.0 / (i + 1)
                    break
            mrr_sum += reciprocal_rank
            
            # 计算Recall@K
            if relevant_docs:
                recalled = sum(
                    1 for rel in relevant_docs
                    if any(rel.lower() in src.lower() for src in retrieved_sources)
                )
                recall = recalled / len(relevant_docs)
            else:
                recall = 1.0  # 如果没有标注相关文档，默认召回率为1
            recall_sum += recall
            
            # 保存详细结果
            retrieval_results.append(RetrievalResult(
                query=query,
                relevant_docs=relevant_docs,
                retrieved_sources=retrieved_sources,
                hit=hit,
                reciprocal_rank=reciprocal_rank,
                recall=recall,
                retrieval_time_ms=elapsed_ms
            ))
        
        n = len(test_cases)
        if n == 0:
            return {"error": "没有测试用例"}
        
        # 更新结果
        self.results.hit_rate = hit_count / n
        self.results.mrr = mrr_sum / n
        self.results.avg_recall = recall_sum / n
        self.results.avg_retrieval_time_ms = total_time / n
        self.results.retrieval_results = retrieval_results
        self.results.total_cases = n
        self.results.evaluation_time = datetime.now().isoformat()
        
        return {
            "hit_rate": self.results.hit_rate,
            "mrr": self.results.mrr,
            "avg_recall": self.results.avg_recall,
            "avg_retrieval_time_ms": self.results.avg_retrieval_time_ms,
            "total_cases": n
        }
    
    def evaluate_generation(self, test_cases: List[Dict]) -> Dict[str, Any]:
        """
        评估生成质量（需要retrieval_qa和llm）
        
        Args:
            test_cases: 测试用例列表，每个用例包含：
                - question: 查询问题
                - expected_answer: 期望答案（可选，用于参考）
                
        Returns:
            包含avg_faithfulness, avg_relevance等指标的字典
        """
        if not self.retrieval_qa:
            return {"error": "未提供retrieval_qa，无法评估生成质量"}
        
        faithfulness_scores = []
        relevance_scores = []
        total_time = 0.0
        generation_results = []
        
        for case in test_cases:
            query = case["question"]
            
            # 记录生成时间
            start_time = time.time()
            
            try:
                # 获取RAG回答
                result = self.retrieval_qa({"query": query})
                answer = result.get("result", "")
                source_docs = result.get("source_documents", [])
                context = "\n".join([doc.page_content for doc in source_docs])
            except Exception as e:
                print(f"生成回答时出错: {e}")
                answer = ""
                context = ""
            
            elapsed_ms = (time.time() - start_time) * 1000
            total_time += elapsed_ms
            
            # 评估Faithfulness和Relevance
            if self.llm and answer and context:
                faith_score = self._evaluate_faithfulness(query, answer, context)
                rel_score = self._evaluate_relevance(query, answer)
            else:
                # 如果没有LLM，使用简单的启发式评估
                faith_score = self._heuristic_faithfulness(answer, context)
                rel_score = self._heuristic_relevance(query, answer)
            
            faithfulness_scores.append(faith_score)
            relevance_scores.append(rel_score)
            
            # 保存详细结果
            generation_results.append(GenerationResult(
                query=query,
                answer=answer[:200] + "..." if len(answer) > 200 else answer,
                context=context[:200] + "..." if len(context) > 200 else context,
                faithfulness_score=faith_score,
                relevance_score=rel_score,
                generation_time_ms=elapsed_ms
            ))
        
        n = len(test_cases)
        if n == 0:
            return {"error": "没有测试用例"}
        
        # 更新结果
        self.results.avg_faithfulness = sum(faithfulness_scores) / n
        self.results.avg_relevance = sum(relevance_scores) / n
        self.results.avg_generation_time_ms = total_time / n
        self.results.generation_results = generation_results
        
        return {
            "avg_faithfulness": self.results.avg_faithfulness,
            "avg_relevance": self.results.avg_relevance,
            "avg_generation_time_ms": self.results.avg_generation_time_ms,
            "total_cases": n
        }
    
    def evaluate_agent_faithfulness(self, test_cases: List[Dict]) -> Dict[str, Any]:
        """
        评估 Agent 回答的忠实度和相关性
        
        Args:
            test_cases: 测试用例列表，每个用例包含：
                - question: 查询问题
                
        Returns:
            包含 avg_faithfulness, avg_relevance 等指标的字典
        """
        if not self.agent:
            return {"error": "未提供 agent，无法评估"}
        if not self.llm:
            return {"error": "未提供 llm，无法进行 LLM 评估"}
        
        faithfulness_scores = []
        relevance_scores = []
        total_time = 0.0
        generation_results = []
        
        for case in test_cases:
            query = case["question"]
            
            # 记录时间
            start_time = time.time()
            
            try:
                # 使用 Agent 获取回答
                if hasattr(self.agent, 'process_query_with_info'):
                    result = self.agent.process_query_with_info(query)
                    answer = result.get("response", "")
                    tool_outputs = result.get("tool_outputs", [])
                    # 工具输出作为上下文
                    context = "\n".join(tool_outputs) if tool_outputs else ""
                else:
                    answer = self.agent.process_query(query)
                    context = ""
                
                # 同时获取 RAG 检索的上下文
                rag_docs = self.rag.search(query, k=3)
                rag_context = "\n".join([doc.page_content[:300] for doc in rag_docs]) if rag_docs else ""
                
                # 合并上下文
                full_context = f"{context}\n{rag_context}".strip()
                
            except Exception as e:
                print(f"Agent 回答时出错: {e}")
                answer = ""
                full_context = ""
            
            elapsed_ms = (time.time() - start_time) * 1000
            total_time += elapsed_ms
            
            # 使用 LLM 评估 Faithfulness 和 Relevance
            if answer and full_context:
                faith_score = self._evaluate_faithfulness(query, answer, full_context)
                rel_score = self._evaluate_relevance(query, answer)
            elif answer:
                # 没有上下文，只评估相关性
                faith_score = 3.0  # 中性分
                rel_score = self._evaluate_relevance(query, answer)
            else:
                faith_score = 1.0
                rel_score = 1.0
            
            faithfulness_scores.append(faith_score)
            relevance_scores.append(rel_score)
            
            # 保存详细结果
            generation_results.append(GenerationResult(
                query=query,
                answer=answer[:200] + "..." if len(answer) > 200 else answer,
                context=full_context[:200] + "..." if len(full_context) > 200 else full_context,
                faithfulness_score=faith_score,
                relevance_score=rel_score,
                generation_time_ms=elapsed_ms
            ))
        
        n = len(test_cases)
        if n == 0:
            return {"error": "没有测试用例"}
        
        # 更新结果
        self.results.avg_faithfulness = sum(faithfulness_scores) / n
        self.results.avg_relevance = sum(relevance_scores) / n
        self.results.avg_generation_time_ms = total_time / n
        self.results.generation_results = generation_results
        
        return {
            "avg_faithfulness": self.results.avg_faithfulness,
            "avg_relevance": self.results.avg_relevance,
            "avg_generation_time_ms": self.results.avg_generation_time_ms,
            "total_cases": n,
            "details": [
                {
                    "query": r.query,
                    "faithfulness": r.faithfulness_score,
                    "relevance": r.relevance_score
                }
                for r in generation_results
            ]
        }
    
    def _evaluate_faithfulness(self, query: str, answer: str, context: str) -> float:
        """使用LLM评估回答的忠实度（1-5分）"""
        prompt = f"""请评估以下AI回答是否基于给定的上下文信息，不包含编造的内容。

【上下文】
{context[:1000]}

【问题】
{query}

【AI回答】
{answer}

请给出1-5分的评分：
1分 = 回答完全编造，与上下文无关
2分 = 回答大部分编造，仅少量信息来自上下文
3分 = 回答部分基于上下文，但有明显编造
4分 = 回答基本基于上下文，仅有少量推断
5分 = 回答完全基于上下文，无编造内容

请只回复一个数字（1-5）："""
        
        try:
            response = self.llm.invoke(prompt)
            return self._extract_score(response)
        except Exception as e:
            print(f"LLM评估失败: {e}")
            return 3.0
    
    def _evaluate_relevance(self, query: str, answer: str) -> float:
        """使用LLM评估回答的相关性（1-5分）"""
        prompt = f"""请评估以下AI回答是否切题回答了用户的问题。

【用户问题】
{query}

【AI回答】
{answer}

请给出1-5分的评分：
1分 = 完全答非所问
2分 = 回答与问题关系不大
3分 = 部分回答了问题
4分 = 基本回答了问题
5分 = 完美回答了问题

请只回复一个数字（1-5）："""
        
        try:
            response = self.llm.invoke(prompt)
            return self._extract_score(response)
        except Exception as e:
            print(f"LLM评估失败: {e}")
            return 3.0
    
    def _extract_score(self, response: str) -> float:
        """从LLM回复中提取分数"""
        if not response:
            return 3.0
        
        # 尝试提取1-5的数字
        match = re.search(r'[1-5]', str(response))
        if match:
            return float(match.group())
        return 3.0
    
    def _heuristic_faithfulness(self, answer: str, context: str) -> float:
        """启发式评估忠实度（当没有LLM时使用）"""
        if not answer or not context:
            return 1.0
        
        # 简单检查：回答中有多少词在上下文中出现
        answer_words = set(answer.lower().split())
        context_words = set(context.lower().split())
        
        if not answer_words:
            return 1.0
        
        overlap = len(answer_words & context_words)
        overlap_ratio = overlap / len(answer_words)
        
        # 转换为1-5分
        return min(5.0, max(1.0, overlap_ratio * 5))
    
    def _heuristic_relevance(self, query: str, answer: str) -> float:
        """启发式评估相关性（当没有LLM时使用）"""
        if not answer:
            return 1.0
        
        # 简单检查：问题中的关键词是否在回答中出现
        query_words = set(query.lower().split())
        answer_lower = answer.lower()
        
        # 移除常见停用词
        stopwords = {'的', '是', '了', '在', '有', '和', '与', '或', '等', '什么', '怎么', '如何', '吗', '呢'}
        query_keywords = query_words - stopwords
        
        if not query_keywords:
            return 3.0
        
        matched = sum(1 for word in query_keywords if word in answer_lower)
        match_ratio = matched / len(query_keywords)
        
        # 转换为1-5分
        return min(5.0, max(1.0, 1 + match_ratio * 4))
    
    def generate_report(self) -> str:
        """生成Markdown格式的评估报告"""
        report = f"""# RAG系统评估报告

**评估时间**: {self.results.evaluation_time}
**测试用例数**: {self.results.total_cases}

---

## 📊 检索质量评估

| 指标 | 值 | 说明 |
|------|-----|------|
| **Hit Rate@K** | {self.results.hit_rate:.2%} | Top-K结果中包含相关文档的比例 |
| **MRR** | {self.results.mrr:.3f} | 平均倒数排名 (越接近1越好) |
| **Avg Recall** | {self.results.avg_recall:.2%} | 平均召回率 |
| **Avg Retrieval Time** | {self.results.avg_retrieval_time_ms:.0f}ms | 平均检索时间 |

## 📝 生成质量评估

| 指标 | 值 | 说明 |
|------|-----|------|
| **Faithfulness** | {self.results.avg_faithfulness:.1f}/5 | 回答忠实度 (是否基于检索内容) |
| **Relevance** | {self.results.avg_relevance:.1f}/5 | 回答相关性 (是否切题) |
| **Avg Generation Time** | {self.results.avg_generation_time_ms:.0f}ms | 平均生成时间 |

---

## 📋 检索详情

"""
        # 添加检索详情
        for i, r in enumerate(self.results.retrieval_results, 1):
            status = "✅" if r.hit else "❌"
            report += f"### {i}. {r.query[:50]}{'...' if len(r.query) > 50 else ''}\n"
            report += f"- 状态: {status} {'命中' if r.hit else '未命中'}\n"
            report += f"- MRR: {r.reciprocal_rank:.2f}\n"
            report += f"- 召回率: {r.recall:.2%}\n"
            report += f"- 检索时间: {r.retrieval_time_ms:.0f}ms\n\n"
        
        if self.results.generation_results:
            report += "\n---\n\n## 📋 生成详情\n\n"
            for i, g in enumerate(self.results.generation_results, 1):
                report += f"### {i}. {g.query[:50]}{'...' if len(g.query) > 50 else ''}\n"
                report += f"- 忠实度: {g.faithfulness_score:.1f}/5\n"
                report += f"- 相关性: {g.relevance_score:.1f}/5\n"
                report += f"- 生成时间: {g.generation_time_ms:.0f}ms\n"
                report += f"- 回答预览: {g.answer[:100]}...\n\n"
        
        return report
    
    def to_dict(self) -> Dict[str, Any]:
        """将结果转换为字典格式"""
        return {
            "hit_rate": self.results.hit_rate,
            "mrr": self.results.mrr,
            "avg_recall": self.results.avg_recall,
            "avg_retrieval_time_ms": self.results.avg_retrieval_time_ms,
            "avg_faithfulness": self.results.avg_faithfulness,
            "avg_relevance": self.results.avg_relevance,
            "avg_generation_time_ms": self.results.avg_generation_time_ms,
            "total_cases": self.results.total_cases,
            "evaluation_time": self.results.evaluation_time
        }

