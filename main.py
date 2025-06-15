"""
Aura AI - 终极修复版本，彻底解决模型输出解析问题
主要修复：
1. 极简化Agent，避免复杂的ReAct解析
2. 直接使用LLM，绕过LangChain的Agent解析器
3. 手动实现工具调用逻辑
4. 增强输出清理机制
"""

import os
import json
import re
from datetime import datetime
import logging
from typing import Dict, List, Any, Union, Optional

from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA

from rag import RAGSystem
import tools
from memory import LongTermMemory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("aura.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AuraUltimate")

class UltraCleanOllama(Ollama):
    """终极增强的Ollama包装器，彻底清理输出"""
    
    def _call(self, prompt: str, stop=None, run_manager=None, **kwargs):
        """重写调用方法，彻底清理输出"""
        try:
            raw_output = super()._call(prompt, stop, run_manager, **kwargs)
            cleaned = self._ultra_clean_output(raw_output)
            logger.debug(f"原始输出: {raw_output[:100]}...")
            logger.debug(f"清理后输出: {cleaned[:100]}...")
            return cleaned
        except Exception as e:
            logger.error(f"LLM调用错误: {e}")
            return "抱歉，我现在无法回答这个问题，请稍后再试。"
    
    def _ultra_clean_output(self, output: str) -> str:
        """终极清理输出"""
        if not output or not isinstance(output, str):
            return "我理解了您的问题，让我为您提供帮助。"
        
        # 移除所有可能的思考标签（贪婪匹配）
        patterns_to_remove = [
            r'<think>.*?</think>',
            r'<thinking>.*?</thinking>',
            r'<reasoning>.*?</reasoning>',
            r'<analysis>.*?</analysis>',
            r'<reflection>.*?</reflection>',
            r'<考虑>.*?</考虑>',
            r'<思考>.*?</思考>',
            # 移除不完整的标签
            r'<think>.*',
            r'<thinking>.*',
            r'<reasoning>.*',
            r'.*</think>',
            r'.*</thinking>',
            r'.*</reasoning>',
        ]
        
        cleaned = output
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除LangChain相关的格式标记
        langchain_patterns = [
            r'Thought:.*?(?=Action:|Final Answer:|$)',
            r'Action:.*?(?=Action Input:|Observation:|Final Answer:|$)',
            r'Action Input:.*?(?=Observation:|Final Answer:|$)',
            r'Observation:.*?(?=Thought:|Final Answer:|$)',
            r'Final Answer:\s*',
        ]
        
        for pattern in langchain_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # 清理多余的空白
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # 移除可能的引号包围
        if cleaned.startswith('`') and cleaned.endswith('`'):
            cleaned = cleaned[1:-1].strip()
        
        # 如果清理后内容为空或太短，返回默认响应
        if not cleaned or len(cleaned) < 5:
            cleaned = "我理解了您的问题，让我为您提供帮助。"
        
        return cleaned

class AuraAgentUltimate:
    """Aura助手的终极修复版Agent类 - 不使用LangChain Agent"""
    
    def __init__(self, model_name="qwen3:4b", verbose=True):
        """初始化Aura Agent"""
        logger.info("初始化Aura Agent (终极版)...")
        
        # 配置
        self.model_name = model_name
        self.verbose = verbose
        
        # 初始化长期记忆
        self.long_term_memory = LongTermMemory()
        logger.info("长期记忆系统已初始化")
        
        # 初始化模型 - 使用极简的系统提示
        self.llm = UltraCleanOllama(
            model=model_name, 
            base_url="http://localhost:11434",
            system=self._get_ultra_simple_system_prompt(),
            temperature=0.7
        )
        logger.info(f"已连接到Ollama模型: {model_name}")
        
        # 初始化RAG系统
        self._init_rag_system()
        
        # 初始化工具字典
        self._init_tools_dict()
        
        logger.info("Aura Agent终极版初始化完成")
    
    def _get_ultra_simple_system_prompt(self) -> str:
        """获取极简系统提示词"""
        return """你是Aura，用户的AI助手。

严格遵守以下规则：
1. 直接回答用户问题，不要使用任何XML标签
2. 不要输出思考过程，只输出最终答案
3. 保持简洁友好的语调
4. 如果需要工具帮助，我会单独调用

你的身份：智能助手Aura，能够回答问题、记忆信息、搜索网络。

请直接回答用户的问题，不要有任何多余的标记或格式。"""
    
    def _init_rag_system(self):
        """初始化RAG知识检索系统"""
        if not os.path.exists("db"):
            os.makedirs("db")
            
        self.rag_system = RAGSystem(persist_directory="db")
        logger.info("RAG系统已初始化")
        
        self.retrieval_qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.rag_system.vectorstore.as_retriever(),
            return_source_documents=True
        )
    
    def _init_tools_dict(self):
        """初始化工具字典"""
        self.tools_dict = {
            "search_web": tools.search_web,
            "read_file": tools.read_file,
            "write_file": tools.write_file,
            "list_directory": tools.list_directory,
            "search_knowledge": self.search_knowledge,
            "remember_fact": self.remember_fact,
            "recall_fact": self.recall_fact
        }
        logger.info(f"已初始化 {len(self.tools_dict)} 个工具")
    
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
        """记住一个事实"""
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
        """回忆一个事实"""
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
    
    def _should_use_tool(self, query: str) -> tuple[bool, str]:
        """判断是否需要使用工具"""
        query_lower = query.lower()
        
        # 实时信息查询
        realtime_keywords = ["天气", "weather", "新闻", "news", "股票", "今天", "现在", "最新"]
        if any(keyword in query_lower for keyword in realtime_keywords):
            return True, "search_web"
        
        # 知识库查询
        knowledge_keywords = ["什么是", "解释", "原理", "如何", "技术", "算法", "模型"]
        if any(keyword in query_lower for keyword in knowledge_keywords):
            return True, "search_knowledge"
        
        # 记忆操作
        if "记住" in query or "remember" in query_lower:
            return True, "remember_fact"
        
        if "回忆" in query or "记得" in query or "recall" in query_lower:
            return True, "recall_fact"
        
        # 文件操作
        if "读取文件" in query or "read file" in query_lower:
            return True, "read_file"
        
        if "写入文件" in query or "write file" in query_lower:
            return True, "write_file"
        
        return False, ""
    
    def _extract_tool_input(self, query: str, tool_name: str) -> str:
        """从查询中提取工具输入"""
        # 这里可以添加更智能的参数提取逻辑
        if tool_name == "search_web":
            return query
        elif tool_name == "search_knowledge":
            return query
        elif tool_name == "remember_fact":
            # 提取要记住的信息
            if "记住" in query:
                parts = query.split("记住")
                if len(parts) > 1:
                    content = parts[1].strip()
                    # 简单格式化为 category/key/value
                    return f"user/preference/{content}"
            return query
        elif tool_name == "recall_fact":
            # 提取要回忆的信息
            return "user/preference"  # 默认查询用户偏好
        
        return query
    
    def process_query(self, query: str) -> str:
        """处理用户查询 - 终极修复版"""
        try:
            logger.info(f"处理用户查询: {query}")
            
            # 首先判断是否需要工具
            need_tool, tool_name = self._should_use_tool(query)
            
            if need_tool and tool_name in self.tools_dict:
                logger.info(f"使用工具: {tool_name}")
                try:
                    tool_input = self._extract_tool_input(query, tool_name)
                    tool_result = self.tools_dict[tool_name](tool_input)
                    
                    # 基于工具结果生成回答
                    context_prompt = f"""基于以下工具查询结果回答用户问题：

用户问题：{query}
工具结果：{tool_result}

请直接给出简洁的回答，不要使用任何XML标签或格式标记："""
                    
                    response = self.llm.invoke(context_prompt)
                    
                except Exception as tool_error:
                    logger.error(f"工具调用错误: {tool_error}")
                    # 如果工具失败，直接用LLM回答
                    simple_prompt = f"请简洁地回答：{query}"
                    response = self.llm.invoke(simple_prompt)
            else:
                # 直接用LLM回答
                simple_prompt = f"请简洁地回答：{query}"
                response = self.llm.invoke(simple_prompt)
            
            # 保存对话历史
            self.long_term_memory.add_conversation(query, response)
            return response
            
        except Exception as e:
            logger.error(f"处理查询出错: {str(e)}")
            return "抱歉，处理您的问题时遇到了错误。请尝试重新表述您的问题。"
    
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
        print("✨ Aura已启动 (终极修复版)，彻底解决解析问题")
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
        # 创建终极修复版Aura Agent
        aura = AuraAgentUltimate(model_name="qwen3:4b", verbose=False)
        
        # 运行命令行界面
        aura.run_cli()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序启动失败: {str(e)}")
        print("请检查Ollama服务是否正在运行，以及模型是否已下载")

if __name__ == "__main__":
    main()
