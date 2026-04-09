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

# Windows PowerShell 默认 GBK，强制 UTF-8 避免 emoji 报错
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aura_react import AuraReActAgent
from evaluation.rag_eval import RAGEvaluator
from evaluation.agent_eval import AgentEvaluator, CapabilityAnalyzer, ModelComparator


class DeepSeekJudge:
    """DeepSeek API wrapper compatible with langchain .invoke() interface"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        self.model = model

    def invoke(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=16,
        )
        return resp.choices[0].message.content.strip()


def load_test_dataset(filepath: str = "evaluation/test_dataset.json") -> dict:
    """加载测试数据集"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def _build_retrieval_qa(agent: AuraReActAgent):
    """构建 RetrievalQA 链，直接用 RAG 检索+LLM 生成，不走 Agent 工具链"""
    try:
        from langchain.chains import RetrievalQA
    except ImportError:
        from langchain_classic.chains import RetrievalQA

    retriever = agent.rag_system.vectorstore.as_retriever(search_kwargs={"k": 3})
    return RetrievalQA.from_chain_type(
        llm=agent.llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )


def run_rag_evaluation(agent: AuraReActAgent, test_cases: list, use_llm: bool = False, judge_llm=None) -> dict:
    """运行RAG评估"""
    print("\n" + "=" * 60)
    print("RAG系统评估")
    print("=" * 60)

    retrieval_qa = _build_retrieval_qa(agent) if use_llm else None
    eval_llm = judge_llm if judge_llm else (agent.llm if use_llm else None)

    rag_evaluator = RAGEvaluator(
        rag_system=agent.rag_system,
        retrieval_qa=retrieval_qa,
        llm=eval_llm,
        agent=None,
    )

    print("\n正在评估检索质量...")
    retrieval_results = rag_evaluator.evaluate_retrieval(test_cases, k=3)

    print(f"\n检索评估结果:")
    print(f"   Hit Rate@3:     {retrieval_results['hit_rate']:.2%}")
    print(f"   MRR:            {retrieval_results['mrr']:.3f}")
    print(f"   Avg Recall:     {retrieval_results['avg_recall']:.2%}")
    print(f"   Avg Time:       {retrieval_results['avg_retrieval_time_ms']:.0f}ms")

    if use_llm:
        print("\n正在评估 Faithfulness (RAG 直接生成 + LLM-as-Judge)...")
        faith_test_cases = test_cases[:10]
        faith_results = rag_evaluator.evaluate_generation(faith_test_cases)

        print(f"\nFaithfulness 评估结果:")
        print(f"   Faithfulness:   {faith_results['avg_faithfulness']:.2f}/5")
        print(f"   Relevance:      {faith_results['avg_relevance']:.2f}/5")
        print(f"   Avg Gen Time:   {faith_results['avg_generation_time_ms']:.0f}ms")
        print(f"   测试用例数:     {faith_results['total_cases']}")

    return {
        "retrieval": retrieval_results,
        "generation": rag_evaluator.to_dict(),
        "report": rag_evaluator.generate_report()
    }


def run_agent_evaluation(agent: AuraReActAgent, test_cases: list) -> dict:
    """运行Agent评估（含能力维度分析）"""
    print("\n" + "=" * 60)
    print("Agent评估")
    print("=" * 60)

    agent_evaluator = AgentEvaluator(agent)
    capability = CapabilityAnalyzer()

    print(f"\n正在评估 {len(test_cases)} 个测试用例...")
    results = agent_evaluator.evaluate(test_cases)

    # 将结果喂入能力维度分析器
    for case, result in zip(test_cases, agent_evaluator.results.test_results):
        capability.feed(case, result)

    print(agent_evaluator.generate_summary())

    print("\n工具使用统计:")
    for tool, count in agent_evaluator.results.tool_usage_stats.items():
        tool_name = tool if tool != "none" else "无工具"
        print(f"   • {tool_name}: {count}次")

    print("\n能力维度得分:")
    for dim, data in capability.to_dict().items():
        bar = "█" * int(data["score"] * 10) + "░" * (10 - int(data["score"] * 10))
        print(f"   • {data['display_name']}: {data['score']:.2%} [{bar}]  ({data['passed']}/{data['total']})")

    dim_report = capability.generate_report()
    agent_report = agent_evaluator.generate_report() + "\n\n" + dim_report

    return {
        "results": results,
        "full_results": agent_evaluator.to_dict(),
        "report": agent_report,
        "capability": capability.to_dict(),
    }


def run_model_comparison(model_names: list, test_cases: list,
                         api_key: str = None, api_base: str = None) -> dict:
    """多模型横向对比评估"""
    print("\n" + "=" * 60)
    print("多模型横向对比评估")
    print(f"模型列表: {', '.join(model_names)}")
    print("=" * 60)

    def agent_factory(model_name: str) -> AuraReActAgent:
        return AuraReActAgent(
            model_name=model_name,
            enable_reranker=False,
            api_key=api_key,
            base_url=api_base,
        )

    comparator = ModelComparator(agent_factory, test_cases)
    comparator.run(model_names)
    report = comparator.generate_report()

    print("\n" + report)
    return {
        "results": comparator.to_dict(),
        "report": report,
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
    parser.add_argument("--deepseek-judge", type=str, default=None, help="DeepSeek API key, 用DeepSeek当Judge替代本地模型自评")
    parser.add_argument(
        "--compare",
        type=str,
        default=None,
        metavar="MODEL1,MODEL2,...",
        help="多模型横向对比，逗号分隔模型名称，例如: qwen2.5:7b,qwen3:4b,llama3:8b",
    )
    parser.add_argument(
        "--api",
        type=str,
        default=None,
        metavar="API_KEY",
        help="使用 OpenAI 兼容 API（如 DeepSeek）作为 Agent 后端，不走本地 Ollama",
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default="https://api.deepseek.com",
        help="API base URL（默认 DeepSeek）",
    )

    args = parser.parse_args()
    
    # --compare 模式：多模型横向对比，优先执行
    if args.compare:
        model_names = [m.strip() for m in args.compare.split(",") if m.strip()]
        try:
            dataset = load_test_dataset()
            test_cases = dataset.get("agent_tests", [])
            if args.quick:
                test_cases = test_cases[:3]
            compare_results = run_model_comparison(
                model_names, test_cases,
                api_key=args.api, api_base=args.api_base,
            )
            if args.save:
                save_report("", compare_results.get("report", ""))
        except FileNotFoundError:
            print("找不到测试数据集文件: evaluation/test_dataset.json")
        print("\n" + "=" * 60)
        print("多模型对比完成!")
        print("=" * 60)
        return

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
    backend = f"API ({args.api_base})" if args.api else "Ollama (本地)"
    print(f"\n🔧 初始化Aura Agent (模型: {args.model}, 后端: {backend})...")
    try:
        agent = AuraReActAgent(
            model_name=args.model,
            enable_reranker=False,
            api_key=args.api,
            base_url=args.api_base,
        )
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
    
    # 构建 Judge LLM
    judge_llm = None
    if args.deepseek_judge:
        print("\n🧠 使用 DeepSeek 作为外部 Judge（替代本地模型自评）")
        judge_llm = DeepSeekJudge(api_key=args.deepseek_judge)
        args.llm_eval = True

    # 运行RAG评估
    if run_rag and dataset.get("rag_tests"):
        try:
            rag_results = run_rag_evaluation(
                agent, 
                dataset["rag_tests"],
                use_llm=args.llm_eval,
                judge_llm=judge_llm,
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

