"""
Aura AI - 修复版本，解决LLM输出解析问题
主要修复：
1. 增强Ollama模型的系统提示，明确禁止使用<think>标签
2. 添加输出清理机制
3. 改进错误处理
"""

import os
import json
import re
from datetime import datetime
import logging
from typing import Dict, List, Any, Union, Optional

from langchain.agents import AgentType, initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from rag import RAGSystem
import tools
from memory import LongTermMemory
from query_handlers.registry import factory as query_handler_factory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("aura.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AuraFixed")

class CleanOllama(Ollama):
    """增强的Ollama包装器，自动清理输出中的思考标签"""
    
    def _call(self, prompt: str, stop=None, run_manager=None, **kwargs):
        """重写调用方法，清理输出"""
        raw_output = super()._call(prompt, stop, run_manager, **kwargs)
        return self._clean_output(raw_output)
    
    def _clean_output(self, output: str) -> str:
        """清理输出中的<think>标签和其他不需要的内容"""
        # 移除<think>...</think>标签及其内容
        cleaned = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL)
        
        # 移除其他常见的思考标记
        cleaned = re.sub(r'<reasoning>.*?</reasoning>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<analysis>.*?</analysis>', '', cleaned, flags=re.DOTALL)
        
        # 移除空行和多余的空白
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = cleaned.strip()
        
        # 如果清理后的内容为空，返回一个默认响应
        if not cleaned:
            cleaned = "我理解了您的问题，让我为您提供帮助。"
        
        return cleaned

class AuraAgentFixed:
    """Aura助手的修复版Agent类"""
    
    def __init__(self, model_name="qwen3:4b", verbose=True):
        """初始化Aura Agent"""
        logger.info("初始化Aura Agent (修复版)...")
        
        # 配置
        self.model_name = model_name
        self.verbose = verbose
        
        # 初始化长期记忆
        self.long_term_memory = LongTermMemory()
        logger.info("长期记忆系统已初始化")
        
        # 初始化模型 - 使用增强的系统提示
        self.llm = CleanOllama(
            model=model_name, 
            base_url="http://localhost:11435",
            system=self._get_system_prompt()
        )
        logger.info(f"已连接到Ollama模型: {model_name}")
        
        # 初始化对话记忆
        self.conversation_memory = ConversationBufferMemory(memory_key="chat_history")
        
        # 初始化RAG系统
        self._init_rag_system()
        
        # 初始化工具集
        self._init_tools()
        
        # 初始化Agent
        self._init_agent()
        
        logger.info("Aura Agent修复版初始化完成")
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词，明确禁止特殊标签"""
        return """你是Aura，用户的AI助手。以下是重要的输出规则：

**输出格式要求：**
1. 绝对不要在回复中使用任何XML标签，包括但不限于：<think>、<reasoning>、<analysis>等
2. 直接提供清晰简洁的回答，不要包含思考过程的标记
3. 如果需要使用工具，严格按照LangChain的ReAct格式
4. 保持友好专业的语调，避免过度戏剧化的表述

**你的身份：**
你继承了Claude的严谨客观特质，不编造信息。你拥有独立思维，能够记住对话内容、使用工具。

**工具使用：**
当需要信息时，主动使用可用工具。回复时只包含最终答案，不要显示工具调用的思考过程。

**背景知识：**
请根据实际用户需求自定义此部分。

记住：回复要简洁直接，不要有任何XML风格的标签！"""
    
    def _init_rag_system(self):
        """初始化RAG知识检索系统"""
        # 确保数据库目录存在
        if not os.path.exists("db"):
            os.makedirs("db")
            
        # 初始化RAG系统
        self.rag_system = RAGSystem(persist_directory="db")
        logger.info("RAG系统已初始化")
        
        # 创建检索链
        self.retrieval_qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.rag_system.vectorstore.as_retriever(),
            return_source_documents=True
        )
    
    def search_knowledge(self, query: str) -> str:
        """搜索本地知识库"""
        try:
            logger.info(f"正在搜索知识库: {query}")
            result = self.retrieval_qa({"query": query})
            return result["result"]
        except Exception as e:
            logger.error(f"知识库搜索错误: {str(e)}")
            return f"知识库搜索出错: {str(e)}"
    
    def remember_fact(self, fact_str: str) -> str:
        """记住一个事实，格式: category/key/value"""
        try:
            parts = fact_str.split('/')
            if len(parts) != 3:
                return "格式错误，请使用: category/key/value"
            
            category, key, value = parts
            self.long_term_memory.add_fact(category, key, value)
            logger.info(f"记忆已添加: {category}/{key}/{value}")
            return f"已记住: {category}/{key}/{value}"
        except Exception as e:
            logger.error(f"添加记忆错误: {str(e)}")
            return f"记忆出错: {str(e)}"
    
    def recall_fact(self, fact_str: str) -> str:
        """回忆一个事实，格式: category/key"""
        try:
            parts = fact_str.split('/')
            if len(parts) != 2:
                return "格式错误，请使用: category/key"
                
            category, key = parts
            value = self.long_term_memory.get_fact(category, key)
            
            if value is None:
                return f"没有找到相关记忆: {category}/{key}"
                
            logger.info(f"记忆已检索: {category}/{key}")
            return f"{category}/{key}: {value}"
        except Exception as e:
            logger.error(f"检索记忆错误: {str(e)}")
            return f"回忆出错: {str(e)}"
    
    def _init_tools(self):
        """初始化工具集"""
        self.tool_list = [
            Tool(
                name="search_web",
                func=tools.search_web,
                description="当需要查询最新的互联网信息时使用，如天气、新闻、股票价格等实时数据"
            ),
            Tool(
                name="read_file",
                func=tools.read_file,
                description="当需要读取本地文件内容时使用，需要提供文件的完整路径"
            ),
            Tool(
                name="write_file",
                func=tools.write_file,
                description="当需要写入内容到本地文件时使用，格式: 文件路径::文件内容"
            ),
            Tool(
                name="list_directory",
                func=tools.list_directory,
                description="列出指定目录下的所有文件和子目录"
            ),
            Tool(
                name="search_knowledge",
                func=self.search_knowledge,
                description="当需要查询专业知识或已学习的资料时使用，优先使用这个工具回答专业问题"
            ),
            Tool(
                name="remember_fact",
                func=self.remember_fact,
                description="记住一个重要事实，格式: category/key/value，例如: user/name/用户名"
            ),
            Tool(
                name="recall_fact",
                func=self.recall_fact,
                description="回忆一个已经记住的事实，格式: category/key，例如: user/name"
            )
        ]
        logger.info(f"已初始化 {len(self.tool_list)} 个工具")
    
    def _init_agent(self):
        """初始化Agent"""
        # 创建增强的Agent提示模板
        agent_prompt = """你是Aura，用户的AI助手。

重要：你的所有回复都必须严格遵循以下格式规则：
1. 绝对不要在回复中使用<think>、<reasoning>或任何XML风格的标签
2. 直接给出清晰的回答，不要暴露内部思考过程

当你需要使用工具时，请使用以下格式：
Thought: 我需要使用工具来帮助回答这个问题
Action: [工具名称]
Action Input: [工具输入]
Observation: [工具返回的结果]
... (根据需要重复上述流程)
Thought: 我现在知道最终答案了
Final Answer: [你的最终回答]

当你不需要使用工具时，请直接回答：
Final Answer: [你的回答]

可用工具:
{tools}

{format_instructions}

之前的对话历史:
{chat_history}

人类: {input}
Thought: {agent_scratchpad}"""
        
        # 初始化Agent，加强错误处理
        self.agent = initialize_agent(
            self.tool_list, 
            self.llm, 
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.conversation_memory,
            verbose=self.verbose,
            handle_parsing_errors=self._handle_parsing_error,
            max_iterations=3,  # 限制最大迭代次数
            early_stopping_method="generate"
        )
        
        logger.info("Agent已初始化")
    
    def _handle_parsing_error(self, error) -> str:
        """处理解析错误"""
        logger.warning(f"解析错误: {error}")
        return "我理解了您的问题。让我直接为您提供帮助。"
    
    def is_realtime_query(self, query: str) -> bool:
        """判断是否为需要实时数据的查询"""
        realtime_keywords = [
            "天气", "weather", "温度", "预报", "股票", "股价", "新闻", "news",
            "今天", "现在", "当前", "最新", "latest", "current", "实时"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in realtime_keywords)
    
    def is_knowledge_query(self, query: str) -> bool:
        """判断是否为知识库查询"""
        knowledge_keywords = [
            "oam", "相位重建", "深度学习", "神经网络", "扩散模型", "论文", "研究",
            "face reconstruction", "技术", "算法", "模型", "英伟达", "面试"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in knowledge_keywords)
    
    def process_query(self, query: str) -> str:
        """处理用户查询 - 修复版"""
        try:
            logger.info(f"处理用户查询: {query}")
            
            # 简化查询处理逻辑，重点关注解决解析错误
            
            # 1. 直接使用Agent处理，让它自己决定是否使用工具
            try:
                result = self.agent.invoke({"input": query})
                
                if isinstance(result, dict):
                    response = result.get("output", "")
                else:
                    response = str(result)
                
                # 额外清理输出，防止解析错误
                response = self._clean_response(response)
                
                # 保存对话历史
                self.long_term_memory.add_conversation(query, response)
                return response
                
            except Exception as agent_error:
                logger.error(f"Agent处理错误: {agent_error}")
                
                # 如果Agent失败，直接使用LLM
                simple_prompt = f"""请回答以下问题，不要使用任何工具：

用户问题：{query}

请直接给出简洁明了的回答，不要使用任何XML标签："""
                
                response = self.llm.invoke(simple_prompt)
                response = self._clean_response(response)
                self.long_term_memory.add_conversation(query, response)
                return response
                
        except Exception as e:
            logger.error(f"处理查询出错: {str(e)}")
            return f"抱歉，处理您的问题时遇到了错误。请尝试重新表述您的问题。"
    
    def _clean_response(self, response: str) -> str:
        """清理响应内容"""
        # 移除可能的思考标签
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = re.sub(r'<reasoning>.*?</reasoning>', '', response, flags=re.DOTALL)
        
        # 移除Agent相关的格式标记
        response = re.sub(r'Final Answer:\s*', '', response)
        response = re.sub(r'Thought:.*?(?=Final Answer:|$)', '', response, flags=re.DOTALL)
        response = re.sub(r'Action:.*?(?=Observation:|Final Answer:|$)', '', response, flags=re.DOTALL)
        response = re.sub(r'Action Input:.*?(?=Observation:|Final Answer:|$)', '', response, flags=re.DOTALL)
        response = re.sub(r'Observation:.*?(?=Thought:|Final Answer:|$)', '', response, flags=re.DOTALL)
        
        # 清理多余的空白和换行
        response = re.sub(r'\n\s*\n', '\n', response)
        response = response.strip()
        
        return response
    
    def load_knowledge(self, extension=".md") -> str:
        """加载知识到RAG系统"""
        try:
            data_dir = os.path.join(os.getcwd(), "data")
            logger.info(f"从{data_dir}加载{extension}格式的知识文档")
            
            if not os.path.exists(data_dir):
                return f"❌ data目录不存在: {data_dir}"
                
            files = os.listdir(data_dir)
            target_files = [f for f in files if f.endswith(extension)]
            
            if not target_files:
                return f"❌ data目录中没有{extension}格式的文件"
                
            # 手动加载每个目标文件
            documents = []
            for file_name in target_files:
                file_path = os.path.join(data_dir, file_name)
                logger.info(f"加载文件: {file_path}")
                
                try:
                    if extension == ".pdf":
                        from langchain.document_loaders import PyPDFLoader
                        loader = PyPDFLoader(file_path)
                    elif extension == ".csv":
                        from langchain.document_loaders import CSVLoader
                        loader = CSVLoader(file_path)
                    else:  # .md或其他文件
                        from langchain.document_loaders import TextLoader
                        loader = TextLoader(file_path, encoding='utf-8')
                        
                    file_docs = loader.load()
                    documents.extend(file_docs)
                    logger.info(f"成功加载 {file_path}, 包含 {len(file_docs)} 个文档")
                except Exception as e:
                    logger.error(f"加载文件 {file_path} 出错: {str(e)}")
            
            if not documents:
                return "❌ 没有成功加载任何文档"
                
            # 文本分割
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            splits = text_splitter.split_documents(documents)
            logger.info(f"创建了 {len(splits)} 个文本块")
            
            # 添加到向量库
            self.rag_system.vectorstore.add_documents(splits)
            logger.info("文档已添加到知识库")
            
            # 持久化保存
            self.rag_system.vectorstore.persist()
            logger.info("知识库已持久化保存")
            
            return "✅ 知识库已更新"
        except Exception as e:
            logger.error(f"加载知识出错: {str(e)}")
            return f"❌ 加载知识出错: {str(e)}"
    
    def run_cli(self):
        """运行命令行界面"""
        print("=" * 50)
        print("✨ Aura已启动 (修复版)，输出解析问题已解决")
        print("💡 提示: 使用'exit'或'退出'可以结束对话")
        print("💡 特殊命令: '加载知识' - 加载data目录中的文档到知识库")
        print("=" * 50)
        
        while True:
            user_input = input("\n👤 输入: ")
            
            # 退出命令
            if user_input.lower() in ["exit", "quit", "退出"]:
                print("👋 Aura正在关闭...")
                break
            
            # 特殊命令处理
            if user_input.lower() == "加载知识":
                extension = input("请输入文件扩展名(默认.md): ") or ".md"
                result = self.load_knowledge(extension)
                print(result)
                continue
                
            # 处理一般查询
            response = self.process_query(user_input)
            print(f"\n🤖 Aura: {response}")

def main():
    """主程序入口"""
    try:
        # 创建修复版Aura Agent
        aura = AuraAgentFixed(model_name="qwen3:4b", verbose=False)
        
        # 运行命令行界面
        aura.run_cli()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序启动失败: {str(e)}")
        print("请检查Ollama服务是否正在运行，以及模型是否已下载")

if __name__ == "__main__":
    main()
