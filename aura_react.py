"""
Aura AI - 完整 ReAct Agent 版本
测试 qwen2.5:7b 能否正确输出 ReAct 格式
"""

import os
import logging

# 兼容 langchain 0.3.x 和 1.x
try:
    from langchain_classic.agents import AgentExecutor, create_react_agent
    from langchain_classic.memory import ConversationBufferWindowMemory
except ImportError:
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.memory import ConversationBufferWindowMemory

from langchain_core.tools import Tool
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

from rag import RAGSystem
from memory import LongTermMemory
import tools as tool_functions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuraReAct")


# ReAct Prompt 模板（中文优化版）
REACT_PROMPT = PromptTemplate.from_template("""你是 Aura，一个智能助手。请用以下格式回答问题：

Question: 用户的问题
Thought: 思考需要做什么
Action: 工具名称（必须是下面列表中的一个）
Action Input: 工具的输入
Observation: 工具返回的结果
... (可以重复 Thought/Action/Action Input/Observation)
Thought: 我现在知道答案了
Final Answer: 最终回答

可用工具:
{tools}

工具名称列表: {tool_names}

对话历史:
{chat_history}

开始!

Question: {input}
{agent_scratchpad}""")


class AuraReActAgent:
    """完整 ReAct Agent 版本"""
    
    def __init__(self, model_name="qwen2.5:7b"):
        logger.info("初始化 ReAct Agent...")
        
        # LLM
        self.llm = Ollama(
            model=model_name,
            base_url="http://localhost:11434",
            temperature=0.3  # 降低温度，让输出更稳定
            # 注意：不要设置 stop，ReAct Agent 会自己管理
        )
        
        # 记忆
        self.long_term_memory = LongTermMemory()
        self.conversation_memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=False  # 返回字符串而不是消息对象
        )
        
        # RAG
        self.rag_system = RAGSystem(persist_directory="db")
        
        # 工具
        self.tools = self._create_tools()
        
        # 创建 ReAct Agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=REACT_PROMPT
        )
        
        # Agent Executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.conversation_memory,
            verbose=True,  # 显示详细过程
            handle_parsing_errors=True,  # 处理解析错误
            max_iterations=5,  # 增加迭代次数
            early_stopping_method="generate",  # 达到限制时让模型自己生成最终答案
            return_intermediate_steps=True  # 返回中间步骤，用于评估
        )
        
        logger.info("ReAct Agent 初始化完成")
    
    def _create_tools(self):
        """创建工具"""
        base_tools = [
            Tool(
                name="search_web",
                func=tool_functions.search_web,
                description="搜索互联网获取实时信息（天气、新闻、股票等）。输入: 搜索关键词"
            ),
            Tool(
                name="search_knowledge",
                func=lambda q: self._search_knowledge(q),
                description="搜索本地知识库，包含用户上传的文档、论文、笔记等私有资料。当用户询问关于他们的文档、论文、资料内容时，必须使用此工具。输入: 搜索关键词或问题"
            ),
            Tool(
                name="remember_user_info",
                func=self._remember,
                description="记住用户的偏好或信息。输入格式: 类别|值，例如: color|蓝色"
            ),
            Tool(
                name="recall_user_info",
                func=self._recall,
                description="回忆用户的偏好或信息。输入: 类别名，例如: color 或 all"
            ),
        ]

        # JobHunter 求职工具集
        try:
            from job_hunter.agent_tools import get_langchain_tools
            base_tools.extend(get_langchain_tools())
            logger.info("JobHunter 工具已加载")
        except ImportError:
            logger.debug("JobHunter 模块未安装，跳过求职工具")

        return base_tools
    
    def _search_knowledge(self, query: str) -> str:
        """搜索知识库（多路召回+重排序）"""
        try:
            # 优先使用混合检索
            results = self.rag_system.hybrid_search(query, k=3, use_rerank=True)
        except AttributeError:
            # 兼容旧版本
            results = self.rag_system.search(query, k=3)
        
        if results:
            return "\n".join([doc.page_content[:200] for doc in results])
        return "知识库中没有找到相关信息"
    
    def _remember(self, fact: str) -> str:
        """记住信息"""
        try:
            if "|" in fact:
                category, value = fact.split("|", 1)
            elif "/" in fact:
                category, value = fact.split("/", 1)
            else:
                category, value = "general", fact
            
            category = category.strip()
            value = value.strip()
            self.long_term_memory.add_fact("user", category, value)
            return f"已记住: {category} = {value}"
        except Exception as e:
            return f"记忆失败: {e}"
    
    def _recall(self, category: str) -> str:
        """回忆信息"""
        try:
            category = category.strip().lower()
            
            if category == "all":
                all_facts = self.long_term_memory.memories.get("facts", {}).get("user", {})
                if all_facts:
                    result = "用户信息:\n"
                    for k, v in all_facts.items():
                        val = v.get("value", v) if isinstance(v, dict) else v
                        result += f"- {k}: {val}\n"
                    return result
                return "没有存储任何用户信息"
            
            value = self.long_term_memory.get_fact("user", category)
            if value:
                return f"{category}: {value}"
            return f"没有找到关于 {category} 的记忆"
        except Exception as e:
            return f"回忆失败: {e}"
    
    def process_query(self, query: str) -> str:
        """处理查询"""
        try:
            result = self.agent_executor.invoke({"input": query})
            response = result.get("output", "抱歉，我无法回答这个问题")
            
            # 保存到长期记忆
            self.long_term_memory.add_conversation(query, response)
            
            # 保存最后一次调用的中间步骤（用于评估）
            self._last_intermediate_steps = result.get("intermediate_steps", [])
            
            return response
        except Exception as e:
            logger.error(f"处理出错: {e}")
            self._last_intermediate_steps = []
            return f"抱歉，出错了: {e}"
    
    def process_query_with_info(self, query: str) -> dict:
        """处理查询并返回详细信息（用于评估）"""
        try:
            result = self.agent_executor.invoke({"input": query})
            response = result.get("output", "抱歉，我无法回答这个问题")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # 提取使用的工具
            tools_used = []
            tool_outputs = []
            for step in intermediate_steps:
                if len(step) >= 2:
                    action = step[0]
                    output = step[1]
                    tools_used.append(action.tool)
                    tool_outputs.append(str(output)[:200])
            
            # 保存到长期记忆
            self.long_term_memory.add_conversation(query, response)
            
            return {
                "response": response,
                "tools_used": tools_used,
                "tool_outputs": tool_outputs,
                "intermediate_steps": intermediate_steps
            }
        except Exception as e:
            logger.error(f"处理出错: {e}")
            return {
                "response": f"抱歉，出错了: {e}",
                "tools_used": [],
                "tool_outputs": [],
                "error": str(e)
            }
    
    def get_last_tools_used(self) -> list:
        """获取上次调用使用的工具列表"""
        tools = []
        for step in getattr(self, '_last_intermediate_steps', []):
            if len(step) >= 1:
                tools.append(step[0].tool)
        return tools
    
    def run_cli(self):
        """运行 CLI"""
        print("=" * 50)
        print("✨ Aura 已启动 (ReAct Agent 版)")
        print("💡 输入 'exit' 退出")
        print("💡 verbose=True，可以看到 ReAct 思考过程")
        print("=" * 50)
        
        while True:
            user_input = input("\n👤 输入: ").strip()
            
            if user_input.lower() in ["exit", "quit", "退出"]:
                print("👋 再见！")
                break
            
            if not user_input:
                continue
            
            response = self.process_query(user_input)
            print(f"\n🤖 Aura: {response}")


def main():
    import sys
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:7b"
    
    agent = AuraReActAgent(model_name=model)
    agent.run_cli()


if __name__ == "__main__":
    main()

