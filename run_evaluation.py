"""
Aura Agent 评估运行脚本

使用方法:
    python run_evaluation.py                    # 运行所有评估
    python run_evaluation.py --rag              # 只运行RAG评估
    python run_evaluation.py --agent            # 只运行Agent评估
    python run_evaluation.py --quick            # 快速模式（减少测试用例）
    python run_evaluation.py --save             # 保存评估报告到文件
"""

import os
import sys
import json
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aura_react import AuraReActAgent
from evaluation.rag_eval import RAGEvaluator
from evaluation.agent_eval import AgentEvaluator


def load_test_dataset(filepath: str = "evaluation/test_dataset.json") -> dict:
    """加载测试数据集"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_rag_evaluation(agent: AuraReActAgent, test_cases: list, use_llm: bool = False) -> dict:
    """运行RAG评估"""
    print("\n" + "=" * 60)
    print("📚 RAG系统评估")
    print("=" * 60)
    
    # 创建评估器
    rag_evaluator = RAGEvaluator(
        rag_system=agent.rag_system,
        retrieval_qa=None,
        llm=agent.llm if use_llm else None,
        agent=agent  # 传入 Agent 用于 Faithfulness 评估
    )
    
    # 评估检索质量
    print("\n⏳ 正在评估检索质量...")
    retrieval_results = rag_evaluator.evaluate_retrieval(test_cases, k=3)
    
    print(f"\n📊 检索评估结果:")
    print(f"   • Hit Rate@3:     {retrieval_results['hit_rate']:.2%}")
    print(f"   • MRR:            {retrieval_results['mrr']:.3f}")
    print(f"   • Avg Recall:     {retrieval_results['avg_recall']:.2%}")
    print(f"   • Avg Time:       {retrieval_results['avg_retrieval_time_ms']:.0f}ms")
    
    # 评估 Faithfulness（使用 Agent 回答 + LLM 评估）
    if use_llm:
        print("\n⏳ 正在评估 Faithfulness (使用LLM自动评估)...")
        # 只取前5个用例进行 Faithfulness 评估（节省时间）
        faith_test_cases = test_cases[:5]
        faith_results = rag_evaluator.evaluate_agent_faithfulness(faith_test_cases)
        
        print(f"\n📝 Faithfulness 评估结果:")
        print(f"   • Faithfulness:   {faith_results['avg_faithfulness']:.2f}/5 (回答忠于上下文)")
        print(f"   • Relevance:      {faith_results['avg_relevance']:.2f}/5 (回答切题)")
        print(f"   • 测试用例数:     {faith_results['total_cases']}")
    
    return {
        "retrieval": retrieval_results,
        "generation": rag_evaluator.to_dict(),
        "report": rag_evaluator.generate_report()
    }


def run_agent_evaluation(agent: AuraReActAgent, test_cases: list) -> dict:
    """运行Agent评估"""
    print("\n" + "=" * 60)
    print("🤖 Agent评估")
    print("=" * 60)
    
    # 创建评估器
    agent_evaluator = AgentEvaluator(agent)
    
    # 运行评估
    print(f"\n⏳ 正在评估 {len(test_cases)} 个测试用例...")
    results = agent_evaluator.evaluate(test_cases)
    
    # 打印摘要
    print(agent_evaluator.generate_summary())
    
    # 详细统计
    print("\n🔧 工具使用统计:")
    for tool, count in agent_evaluator.results.tool_usage_stats.items():
        tool_name = tool if tool != "none" else "无工具"
        print(f"   • {tool_name}: {count}次")
    
    return {
        "results": results,
        "full_results": agent_evaluator.to_dict(),
        "report": agent_evaluator.generate_report()
    }


def save_report(rag_report: str, agent_report: str, output_dir: str = "reports"):
    """保存评估报告"""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 合并报告
    full_report = f"""# Aura Agent 完整评估报告

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

{rag_report}

---

{agent_report}

---

## 📌 评估说明

### RAG评估指标说明
- **Hit Rate@K**: Top-K检索结果中包含至少一个相关文档的查询比例
- **MRR (Mean Reciprocal Rank)**: 第一个相关文档排名的倒数的平均值，越接近1越好
- **Recall@K**: 在Top-K结果中召回的相关文档比例
- **Faithfulness**: 回答是否基于检索到的内容，不包含编造信息
- **Relevance**: 回答是否与问题相关，是否切题

### Agent评估指标说明
- **工具调用准确率**: 正确判断是否需要使用工具，以及选择正确工具的比例
- **任务成功率**: 回答中包含所有期望关键词的比例
- **平均响应时间**: 从收到查询到生成回答的平均时间

### 如何改进
1. **提高Hit Rate**: 优化文档切分策略，确保相关信息不被截断
2. **提高MRR**: 优化Embedding模型，使用更好的相似度计算方法
3. **提高Faithfulness**: 调整prompt，强调基于上下文回答
4. **提高工具准确率**: 优化工具选择的关键词匹配逻辑
"""
    
    # 保存完整报告
    report_path = os.path.join(output_dir, f"evaluation_report_{timestamp}.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(full_report)
    
    print(f"\n✅ 评估报告已保存到: {report_path}")
    
    return report_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Aura Agent 评估工具")
    parser.add_argument("--rag", action="store_true", help="只运行RAG评估")
    parser.add_argument("--agent", action="store_true", help="只运行Agent评估")
    parser.add_argument("--quick", action="store_true", help="快速模式（减少测试用例）")
    parser.add_argument("--save", action="store_true", help="保存评估报告")
    parser.add_argument("--llm-eval", action="store_true", help="使用LLM评估生成质量")
    parser.add_argument("--model", type=str, default="qwen2.5:7b", help="使用的模型名称")
    
    args = parser.parse_args()
    
    # 如果没有指定评估类型，则运行所有评估
    run_rag = args.rag or (not args.rag and not args.agent)
    run_agent = args.agent or (not args.rag and not args.agent)
    
    print("=" * 60)
    print("🌟 Aura Agent 评估系统")
    print("=" * 60)
    
    # 加载测试数据集
    print("\n📂 加载测试数据集...")
    try:
        dataset = load_test_dataset()
        print(f"   • RAG测试用例: {len(dataset.get('rag_tests', []))}个")
        print(f"   • Agent测试用例: {len(dataset.get('agent_tests', []))}个")
        print(f"   • 边界测试用例: {len(dataset.get('edge_cases', []))}个")
    except FileNotFoundError:
        print("❌ 找不到测试数据集文件: evaluation/test_dataset.json")
        return
    
    # 快速模式：减少测试用例
    if args.quick:
        print("\n⚡ 快速模式：每类只使用前3个测试用例")
        dataset["rag_tests"] = dataset.get("rag_tests", [])[:3]
        dataset["agent_tests"] = dataset.get("agent_tests", [])[:3]
    
    # 初始化Agent
    print(f"\n🔧 初始化Aura Agent (模型: {args.model})...")
    try:
        agent = AuraReActAgent(model_name=args.model)
        print("   ✅ Agent初始化成功")
    except Exception as e:
        print(f"   ❌ Agent初始化失败: {e}")
        print("\n请确保:")
        print("   1. Ollama服务正在运行")
        print("   2. 所需模型已下载")
        return
    
    # 存储报告
    rag_report = ""
    agent_report = ""
    
    # 运行RAG评估
    if run_rag and dataset.get("rag_tests"):
        try:
            rag_results = run_rag_evaluation(
                agent, 
                dataset["rag_tests"],
                use_llm=args.llm_eval
            )
            rag_report = rag_results.get("report", "")
        except Exception as e:
            print(f"\n❌ RAG评估出错: {e}")
    
    # 运行Agent评估
    if run_agent and dataset.get("agent_tests"):
        try:
            # 合并agent_tests和edge_cases
            all_agent_tests = dataset.get("agent_tests", [])
            if not args.quick:
                all_agent_tests.extend(dataset.get("edge_cases", []))
            
            agent_results = run_agent_evaluation(agent, all_agent_tests)
            agent_report = agent_results.get("report", "")
        except Exception as e:
            print(f"\n❌ Agent评估出错: {e}")
    
    # 保存报告
    if args.save and (rag_report or agent_report):
        save_report(rag_report, agent_report)
    
    print("\n" + "=" * 60)
    print("🎉 评估完成!")
    print("=" * 60)
    
    # 面试话术提示
    print("\n💡 面试话术建议:")
    print("   \"我给Agent系统设计了完整的评估体系，包括RAG检索质量评估")
    print("   （Hit Rate、MRR、Recall）和Agent工具调用准确率评估，")
    print("   并编写了自动化评估脚本，可以持续监控系统质量。\"")


if __name__ == "__main__":
    main()

