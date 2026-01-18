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
                    # 新版 ReAct Agent: 使用 process_query_with_info 获取真实工具调用
                    result = self.agent.process_query_with_info(query)
                    response = result.get("response", "")
                    tools_used = result.get("tools_used", [])
                    # 取第一个使用的工具作为 actual_tool
                    actual_tool = tools_used[0] if tools_used else None
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
                # ReAct Agent: 通过实际执行来分析
                response = self.agent.process_query(query)
                # 简单推断
                need_tool = len(response) > 20
                tool_name = "auto"  # ReAct 自动选择
            else:
                need_tool, tool_name = self.agent._should_use_tool(query)
            
            decisions.append({
                "query": query,
                "need_tool": need_tool,
                "tool_name": tool_name if need_tool else None
            })
        
        # 统计
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

