"""
Agent评估模块
评估指标：
- 工具调用准确率: 该用工具时用了，不该用时没用
- 任务完成率: 成功回答问题的比例
- 平均响应时间: 从输入到输出的时间
- 平均工具调用次数: 完成任务用了几次工具
"""

import time
import re
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentTestResult:
    """单个测试用例的结果"""
    query: str
    expected_tool: Optional[str]
    actual_tool: Optional[str]
    tool_correct: bool
    response: str
    expected_contains: List[str]
    task_success: bool
    response_time_ms: float
    error: Optional[str] = None


@dataclass
class AgentEvalResults:
    """Agent整体评估结果"""
    # 核心指标
    tool_accuracy: float = 0.0
    task_success_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    
    # 工具分析
    tool_usage_stats: Dict[str, int] = field(default_factory=dict)
    tool_correct_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # 详细结果
    test_results: List[AgentTestResult] = field(default_factory=list)
    
    # 元数据
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    evaluation_time: str = ""


class AgentEvaluator:
    """Agent评估器 - 兼容 ReAct Agent"""
    
    def __init__(self, agent):
        """
        初始化Agent评估器
        
        Args:
            agent: AuraReActAgent 或 AuraAgentUltimate 实例
        """
        self.agent = agent
        self.results = AgentEvalResults()
        # 检查是否支持 process_query_with_info（新版 ReAct Agent）
        self.has_detailed_info = hasattr(agent, 'process_query_with_info')
        # 检查是否是旧版 Agent（有 _should_use_tool 方法）
        self.is_legacy_agent = hasattr(agent, '_should_use_tool')
    
    def evaluate(self, test_cases: List[Dict]) -> Dict[str, Any]:
        """
        评估Agent性能
        
        Args:
            test_cases: 测试用例列表，每个用例包含：
                - question: 用户查询
                - expected_tool: 期望使用的工具（None表示不需要工具）
                - expected_contains: 回答中应包含的关键词列表
                
        Returns:
            包含tool_accuracy, task_success_rate等指标的字典
        """
        tool_correct_count = 0
        task_success_count = 0
        total_time = 0.0
        test_results = []
        tool_usage_stats = {}
        tool_correct_stats = {}  # {expected_tool: {correct: n, incorrect: n}}
        
        for case in test_cases:
            query = case["question"]
            expected_tool = case.get("expected_tool")
            expected_contains = case.get("expected_contains", [])
            
            # 初始化工具统计
            tool_key = expected_tool if expected_tool else "none"
            if tool_key not in tool_correct_stats:
                tool_correct_stats[tool_key] = {"correct": 0, "incorrect": 0}
            
            error = None
            actual_tool = None
            response = ""
            elapsed_ms = 0.0
            
            try:
                # 记录开始时间
                start_time = time.time()
                
                if self.has_detailed_info:
                    result = self.agent.process_query_with_info(query)
                    response = result.get("response", "")
                    tools_used = result.get("tools_used", [])
                    # 过滤掉 _Exception（LangChain 解析失败产生的伪工具调用）
                    real_tools = [t for t in tools_used if t != "_Exception"]
                    actual_tool = real_tools[0] if real_tools else None
                elif self.is_legacy_agent:
                    # 旧版 Agent: 使用 _should_use_tool
                    need_tool, tool_name = self.agent._should_use_tool(query)
                    actual_tool = tool_name if need_tool else None
                    response = self.agent.process_query(query)
                else:
                    # 其他情况：直接调用
                    response = self.agent.process_query(query)
                    actual_tool = None
                
                elapsed_ms = (time.time() - start_time) * 1000
                total_time += elapsed_ms
                
                # 统计工具使用
                if actual_tool:
                    tool_usage_stats[actual_tool] = tool_usage_stats.get(actual_tool, 0) + 1
                else:
                    tool_usage_stats["none"] = tool_usage_stats.get("none", 0) + 1
                
            except Exception as e:
                error = str(e)
                actual_tool = None
                response = ""
                elapsed_ms = 0.0
            
            # 评估工具调用准确率
            tool_correct = (actual_tool == expected_tool)
            if tool_correct:
                tool_correct_count += 1
                tool_correct_stats[tool_key]["correct"] += 1
            else:
                tool_correct_stats[tool_key]["incorrect"] += 1
            
            # 评估任务完成（严格模式）
            match_any = case.get("match_any", False)  # 是否匹配任意一个关键词
            if expected_contains:
                task_success = self._check_task_success(response, expected_contains, match_any)
            else:
                # 没有指定关键词时，检查是否有实质性回答（非错误信息）
                task_success = (
                    len(response) > 20 and 
                    "出错" not in response and 
                    "抱歉" not in response[:20]
                )
            
            if task_success:
                task_success_count += 1
            
            # 保存详细结果
            test_results.append(AgentTestResult(
                query=query,
                expected_tool=expected_tool,
                actual_tool=actual_tool,
                tool_correct=tool_correct,
                response=response[:200] if response else "",
                expected_contains=expected_contains,
                task_success=task_success,
                response_time_ms=elapsed_ms,
                error=error
            ))
        
        n = len(test_cases)
        if n == 0:
            return {"error": "没有测试用例"}
        
        # 更新结果
        self.results.tool_accuracy = tool_correct_count / n
        self.results.task_success_rate = task_success_count / n
        self.results.avg_response_time_ms = total_time / n
        self.results.tool_usage_stats = tool_usage_stats
        self.results.tool_correct_stats = tool_correct_stats
        self.results.test_results = test_results
        self.results.total_cases = n
        self.results.passed_cases = sum(1 for r in test_results if r.tool_correct and r.task_success)
        self.results.failed_cases = n - self.results.passed_cases
        self.results.evaluation_time = datetime.now().isoformat()
        
        return {
            "tool_accuracy": self.results.tool_accuracy,
            "task_success_rate": self.results.task_success_rate,
            "avg_response_time_ms": self.results.avg_response_time_ms,
            "total_cases": n,
            "passed_cases": self.results.passed_cases,
            "failed_cases": self.results.failed_cases
        }
    
    def _check_task_success(self, response: str, expected_contains: List[str], match_any: bool = False) -> bool:
        """
        检查回答是否包含期望的关键词
        
        Args:
            response: 模型的回答
            expected_contains: 期望包含的关键词列表
            match_any: True=匹配任意一个即可，False=必须全部匹配
        """
        if not response:
            return len(expected_contains) == 0
        
        if not expected_contains:
            return True
        
        response_lower = response.lower()
        
        if match_any:
            # 匹配任意一个关键词即可
            for keyword in expected_contains:
                if keyword.lower() in response_lower:
                    return True
            return False
        else:
            # 必须匹配所有关键词
            for keyword in expected_contains:
                if keyword.lower() not in response_lower:
                    return False
            return True
    
    def evaluate_with_custom_checker(
        self, 
        test_cases: List[Dict], 
        success_checker: Callable[[str, Dict], bool]
    ) -> Dict[str, Any]:
        """
        使用自定义检查器评估Agent
        
        Args:
            test_cases: 测试用例列表
            success_checker: 自定义成功检查函数，接收(response, test_case)，返回bool
            
        Returns:
            评估结果字典
        """
        tool_correct_count = 0
        task_success_count = 0
        total_time = 0.0
        test_results = []
        
        for case in test_cases:
            query = case["question"]
            expected_tool = case.get("expected_tool")
            
            try:
                start_time = time.time()
                
                response = self.agent.process_query(query)
                elapsed_ms = (time.time() - start_time) * 1000
                total_time += elapsed_ms
                
                if self.is_react_agent:
                    actual_tool = self._get_tool_from_response(query, response)
                else:
                    need_tool, tool_name = self.agent._should_use_tool(query)
                    actual_tool = tool_name if need_tool else None
                
                tool_correct = (actual_tool == expected_tool)
                if tool_correct:
                    tool_correct_count += 1
                
                # 使用自定义检查器
                task_success = success_checker(response, case)
                if task_success:
                    task_success_count += 1
                
                test_results.append(AgentTestResult(
                    query=query,
                    expected_tool=expected_tool,
                    actual_tool=actual_tool,
                    tool_correct=tool_correct,
                    response=response[:200] if response else "",
                    expected_contains=case.get("expected_contains", []),
                    task_success=task_success,
                    response_time_ms=elapsed_ms
                ))
                
            except Exception as e:
                test_results.append(AgentTestResult(
                    query=query,
                    expected_tool=expected_tool,
                    actual_tool=None,
                    tool_correct=False,
                    response="",
                    expected_contains=[],
                    task_success=False,
                    response_time_ms=0.0,
                    error=str(e)
                ))
        
        n = len(test_cases)
        return {
            "tool_accuracy": tool_correct_count / n if n > 0 else 0,
            "task_success_rate": task_success_count / n if n > 0 else 0,
            "avg_response_time_ms": total_time / n if n > 0 else 0,
            "total_cases": n
        }
    
    def generate_report(self) -> str:
        """生成Markdown格式的评估报告"""
        report = f"""# Agent评估报告

**评估时间**: {self.results.evaluation_time}
**测试用例数**: {self.results.total_cases}
**通过/失败**: {self.results.passed_cases} / {self.results.failed_cases}

---

## 📊 总体指标

| 指标 | 值 | 说明 |
|------|-----|------|
| **工具调用准确率** | {self.results.tool_accuracy:.2%} | 正确判断是否需要工具 |
| **任务成功率** | {self.results.task_success_rate:.2%} | 成功完成任务的比例 |
| **平均响应时间** | {self.results.avg_response_time_ms:.0f}ms | 从输入到输出的时间 |

---

## 🔧 工具使用统计

| 工具 | 调用次数 | 准确率 |
|------|----------|--------|
"""
        # 添加工具统计
        for tool, count in self.results.tool_usage_stats.items():
            stats = self.results.tool_correct_stats.get(tool, {"correct": 0, "incorrect": 0})
            total = stats["correct"] + stats["incorrect"]
            accuracy = stats["correct"] / total if total > 0 else 0
            tool_name = tool if tool != "none" else "无工具"
            report += f"| {tool_name} | {count} | {accuracy:.2%} |\n"
        
        report += "\n---\n\n## 📋 测试用例详情\n\n"
        
        # 添加详细结果
        for i, r in enumerate(self.results.test_results, 1):
            status = "✅" if r.tool_correct and r.task_success else "❌"
            report += f"### {i}. {r.query[:50]}{'...' if len(r.query) > 50 else ''}\n"
            report += f"- **状态**: {status}\n"
            report += f"- **期望工具**: {r.expected_tool if r.expected_tool else '无'}\n"
            report += f"- **实际工具**: {r.actual_tool if r.actual_tool else '无'}\n"
            report += f"- **工具判断**: {'✅ 正确' if r.tool_correct else '❌ 错误'}\n"
            report += f"- **任务完成**: {'✅ 成功' if r.task_success else '❌ 失败'}\n"
            report += f"- **响应时间**: {r.response_time_ms:.0f}ms\n"
            if r.error:
                report += f"- **错误**: {r.error}\n"
            if r.response:
                report += f"- **回答预览**: {r.response[:100]}...\n"
            report += "\n"
        
        return report
    
    def generate_summary(self) -> str:
        """生成简洁的评估摘要"""
        summary = f"""
╔══════════════════════════════════════════════════════════╗
║                    Agent评估摘要                          ║
╠══════════════════════════════════════════════════════════╣
║  工具调用准确率: {self.results.tool_accuracy:>6.2%}                             ║
║  任务成功率:     {self.results.task_success_rate:>6.2%}                             ║
║  平均响应时间:   {self.results.avg_response_time_ms:>6.0f}ms                            ║
║  通过/总数:      {self.results.passed_cases:>3}/{self.results.total_cases:<3}                               ║
╚══════════════════════════════════════════════════════════╝
"""
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """将结果转换为字典格式"""
        return {
            "tool_accuracy": self.results.tool_accuracy,
            "task_success_rate": self.results.task_success_rate,
            "avg_response_time_ms": self.results.avg_response_time_ms,
            "tool_usage_stats": self.results.tool_usage_stats,
            "total_cases": self.results.total_cases,
            "passed_cases": self.results.passed_cases,
            "failed_cases": self.results.failed_cases,
            "evaluation_time": self.results.evaluation_time
        }


class ToolAccuracyAnalyzer:
    """工具调用准确率详细分析器"""
    
    def __init__(self, agent):
        self.agent = agent
        self.is_react_agent = not hasattr(agent, '_should_use_tool')
    
    def analyze_tool_decision(self, queries: List[str]) -> Dict[str, Any]:
        """
        分析Agent的工具决策逻辑
        
        Args:
            queries: 查询列表
            
        Returns:
            工具决策分析结果
        """
        decisions = []
        
        for query in queries:
            if self.is_react_agent:
                response = self.agent.process_query(query)
                need_tool = len(response) > 20
                tool_name = "auto"
            else:
                need_tool, tool_name = self.agent._should_use_tool(query)
            
            decisions.append({
                "query": query,
                "need_tool": need_tool,
                "tool_name": tool_name if need_tool else None
            })
        
        tool_counts = {}
        for d in decisions:
            tool = d["tool_name"] if d["need_tool"] else "none"
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        return {
            "decisions": decisions,
            "tool_distribution": tool_counts,
            "total_queries": len(queries),
            "tool_usage_rate": sum(1 for d in decisions if d["need_tool"]) / len(queries) if queries else 0
        }


# ─────────────────────────────────────────────────────────────
# 能力维度分析
# ─────────────────────────────────────────────────────────────

# 内置能力维度定义（可在测试用例中通过 "dimension" 字段覆盖）
CAPABILITY_DIMENSIONS = {
    "reasoning":       "逻辑推理",
    "knowledge":       "知识检索",
    "tool_use":        "工具调用",
    "multi_turn":      "多轮对话",
    "instruction":     "指令遵循",
    "safety":          "安全拒绝",
}


@dataclass
class DimensionScore:
    """单个能力维度的评分"""
    dimension: str
    display_name: str
    total: int = 0
    passed: int = 0
    avg_response_time_ms: float = 0.0

    @property
    def score(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


class CapabilityAnalyzer:
    """
    能力维度分析器
    
    在测试用例中添加 "dimension" 字段（取值见 CAPABILITY_DIMENSIONS）即可
    自动按维度聚合评估结果，生成雷达图所需数据及 Markdown 报告。
    """

    def __init__(self):
        self.dimension_scores: Dict[str, DimensionScore] = {
            dim: DimensionScore(dimension=dim, display_name=label)
            for dim, label in CAPABILITY_DIMENSIONS.items()
        }
        self._raw: List[Dict[str, Any]] = []

    def feed(self, test_case: Dict, result: AgentTestResult) -> None:
        """将一条评估结果喂入分析器"""
        dim = test_case.get("dimension", "reasoning")
        if dim not in self.dimension_scores:
            self.dimension_scores[dim] = DimensionScore(
                dimension=dim, display_name=dim
            )
        ds = self.dimension_scores[dim]
        ds.total += 1
        if result.task_success:
            ds.passed += 1
        # 滚动均值
        ds.avg_response_time_ms = (
            (ds.avg_response_time_ms * (ds.total - 1) + result.response_time_ms)
            / ds.total
        )
        self._raw.append({"case": test_case, "result": result, "dimension": dim})

    def to_dict(self) -> Dict[str, Any]:
        return {
            dim: {
                "display_name": ds.display_name,
                "score": round(ds.score, 4),
                "passed": ds.passed,
                "total": ds.total,
                "avg_response_time_ms": round(ds.avg_response_time_ms, 1),
            }
            for dim, ds in self.dimension_scores.items()
            if ds.total > 0
        }

    def weakest_dimensions(self, n: int = 3) -> List[DimensionScore]:
        active = [ds for ds in self.dimension_scores.values() if ds.total > 0]
        return sorted(active, key=lambda x: x.score)[:n]

    def generate_report(self) -> str:
        rows = sorted(
            [ds for ds in self.dimension_scores.values() if ds.total > 0],
            key=lambda x: x.score,
            reverse=True,
        )
        lines = [
            "## 🧩 能力维度分析\n",
            "| 维度 | 得分 | 通过/总数 | 平均响应时间 |",
            "|------|------|-----------|------------|",
        ]
        for ds in rows:
            bar = "█" * int(ds.score * 10) + "░" * (10 - int(ds.score * 10))
            lines.append(
                f"| {ds.display_name} | {ds.score:.2%} `{bar}` "
                f"| {ds.passed}/{ds.total} | {ds.avg_response_time_ms:.0f}ms |"
            )
        lines.append("")
        weak = self.weakest_dimensions(3)
        if weak:
            lines.append("### ⚠️ 能力短板（待提升）\n")
            for ds in weak:
                lines.append(f"- **{ds.display_name}**: {ds.score:.2%}（{ds.passed}/{ds.total}）")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 多模型横向对比
# ─────────────────────────────────────────────────────────────

@dataclass
class ModelBenchmarkResult:
    """单个模型的基准测试结果"""
    model_name: str
    tool_accuracy: float
    task_success_rate: float
    avg_response_time_ms: float
    dimension_scores: Dict[str, float]   # {dimension: score}
    total_cases: int
    passed_cases: int
    evaluation_time: str = ""


class ModelComparator:
    """
    多模型横向对比评估器
    
    用法示例:
        comparator = ModelComparator(agent_factory, test_cases)
        comparator.run(["qwen2.5:7b", "qwen3:4b", "llama3:8b"])
        print(comparator.generate_report())
    
    agent_factory: Callable[[str], agent] —— 接收模型名称，返回初始化好的 Agent
    """

    def __init__(self, agent_factory: Callable, test_cases: List[Dict]):
        self.agent_factory = agent_factory
        self.test_cases = test_cases
        self.results: List[ModelBenchmarkResult] = []

    def run(self, model_names: List[str]) -> List[ModelBenchmarkResult]:
        """对多个模型依次跑评估，收集结果"""
        self.results = []
        for model_name in model_names:
            print(f"\n{'='*50}")
            print(f"正在评估模型: {model_name}")
            print(f"{'='*50}")
            try:
                agent = self.agent_factory(model_name)
                result = self._evaluate_single(model_name, agent)
                self.results.append(result)
                print(f"  工具准确率: {result.tool_accuracy:.2%} | "
                      f"任务成功率: {result.task_success_rate:.2%} | "
                      f"响应时间: {result.avg_response_time_ms:.0f}ms")
            except Exception as e:
                print(f"  模型 {model_name} 评估失败: {e}")
        return self.results

    def _evaluate_single(self, model_name: str, agent) -> ModelBenchmarkResult:
        evaluator = AgentEvaluator(agent)
        capability = CapabilityAnalyzer()

        tool_correct = 0
        task_success = 0
        total_time = 0.0

        for case in self.test_cases:
            query = case["question"]
            expected_tool = case.get("expected_tool")
            expected_contains = case.get("expected_contains", [])
            match_any = case.get("match_any", False)

            start = time.time()
            try:
                if hasattr(agent, "process_query_with_info"):
                    info = agent.process_query_with_info(query)
                    response = info.get("response", "")
                    tools_used = info.get("tools_used", [])
                    real_tools = [t for t in tools_used if t != "_Exception"]
                    actual_tool = real_tools[0] if real_tools else None
                else:
                    response = agent.process_query(query)
                    actual_tool = None
            except Exception as e:
                response = ""
                actual_tool = None
            elapsed_ms = (time.time() - start) * 1000
            total_time += elapsed_ms

            tc = (actual_tool == expected_tool)
            if tc:
                tool_correct += 1

            if expected_contains:
                ts = evaluator._check_task_success(response, expected_contains, match_any)
            else:
                ts = len(response) > 20 and "出错" not in response and "抱歉" not in response[:20]
            if ts:
                task_success += 1

            result_obj = AgentTestResult(
                query=query,
                expected_tool=expected_tool,
                actual_tool=actual_tool,
                tool_correct=tc,
                response=response[:200],
                expected_contains=expected_contains,
                task_success=ts,
                response_time_ms=elapsed_ms,
            )
            capability.feed(case, result_obj)

        n = len(self.test_cases)
        dim_scores = {
            dim: data["score"]
            for dim, data in capability.to_dict().items()
        }

        return ModelBenchmarkResult(
            model_name=model_name,
            tool_accuracy=tool_correct / n if n > 0 else 0.0,
            task_success_rate=task_success / n if n > 0 else 0.0,
            avg_response_time_ms=total_time / n if n > 0 else 0.0,
            dimension_scores=dim_scores,
            total_cases=n,
            passed_cases=task_success,
            evaluation_time=datetime.now().isoformat(),
        )

    def generate_report(self) -> str:
        if not self.results:
            return "# 模型对比报告\n\n暂无评估结果。"

        best_success = max(self.results, key=lambda r: r.task_success_rate)
        best_speed = min(self.results, key=lambda r: r.avg_response_time_ms)

        lines = [
            "# 多模型横向对比报告\n",
            f"**评估时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**测试用例数**: {self.results[0].total_cases if self.results else 0}  ",
            f"**冠军模型（任务成功率）**: `{best_success.model_name}`  ",
            f"**最快模型**: `{best_speed.model_name}`\n",
            "---\n",
            "## 📊 总体指标对比\n",
            "| 模型 | 工具准确率 | 任务成功率 | 平均响应时间 | 综合得分 |",
            "|------|-----------|-----------|------------|---------|",
        ]

        for r in sorted(self.results, key=lambda x: x.task_success_rate, reverse=True):
            composite = (r.tool_accuracy * 0.4 + r.task_success_rate * 0.6)
            crown = " 👑" if r.model_name == best_success.model_name else ""
            lines.append(
                f"| `{r.model_name}`{crown} | {r.tool_accuracy:.2%} "
                f"| {r.task_success_rate:.2%} | {r.avg_response_time_ms:.0f}ms "
                f"| **{composite:.2%}** |"
            )

        # 能力维度雷达表
        all_dims = sorted({dim for r in self.results for dim in r.dimension_scores})
        if all_dims:
            lines += [
                "\n---\n",
                "## 🧩 能力维度对比\n",
                "| 维度 | " + " | ".join(f"`{r.model_name}`" for r in self.results) + " |",
                "|------|" + "|".join(["------"] * len(self.results)) + "|",
            ]
            for dim in all_dims:
                display = CAPABILITY_DIMENSIONS.get(dim, dim)
                scores = []
                for r in self.results:
                    s = r.dimension_scores.get(dim)
                    scores.append(f"{s:.2%}" if s is not None else "N/A")
                # 标记最高分
                try:
                    num_scores = [
                        r.dimension_scores.get(dim, 0.0) for r in self.results
                    ]
                    max_idx = num_scores.index(max(num_scores))
                    scores[max_idx] = f"**{scores[max_idx]}** ✓"
                except Exception:
                    pass
                lines.append(f"| {display} | " + " | ".join(scores) + " |")

        lines += [
            "\n---\n",
            "## 💡 结论与建议\n",
        ]
        for r in self.results:
            lines.append(f"### `{r.model_name}`")
            if r.dimension_scores:
                weak_dims = sorted(r.dimension_scores.items(), key=lambda x: x[1])[:2]
                for dim, score in weak_dims:
                    display = CAPABILITY_DIMENSIONS.get(dim, dim)
                    lines.append(f"- {display} 较弱（{score:.2%}），建议针对性优化 prompt 或 fine-tune")
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> List[Dict[str, Any]]:
        return [
            {
                "model_name": r.model_name,
                "tool_accuracy": r.tool_accuracy,
                "task_success_rate": r.task_success_rate,
                "avg_response_time_ms": r.avg_response_time_ms,
                "dimension_scores": r.dimension_scores,
                "total_cases": r.total_cases,
                "passed_cases": r.passed_cases,
                "evaluation_time": r.evaluation_time,
            }
            for r in self.results
        ]

