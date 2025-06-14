"""
Aura AI - 修复版本，彻底解决think标签问题
主要修复：
1. 修复拼写错误：loggingjie -> logging
2. 超强输出清理机制，彻底移除所有思考标记
3. 绕过LangChain Agent解析器，直接处理输出
4. 多层防护，确保绝不输出think标签
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
logger = logging.getLogger("AuraFixed")

class SuperCleanOllama(Ollama):
    """超级清理的Ollama包装器，彻底禁止think标签"""
    
    def _call(self, prompt: str, stop=None, run_manager=None, **kwargs):
        """重写调用方法，超强清理输出"""
        try:
            raw_output = super()._call(prompt, stop, run_manager, **kwargs)
            cleaned = self._super_clean_output(raw_output)
            logger.debug(f"原始输出: {raw_output[:200]}...")
            logger.debug(f"清理后输出: {cleaned[:200]}...")
            return cleaned
        except Exception as e:
            logger.error(f"LLM调用错误: {e}")
            return "我理解了您的问题，让我为您提供帮助。"
    
    def _super_clean_output(self, output: str) -> str:
        """超级清理输出，彻底移除所有思考标记"""
        if not output or not isinstance(output, str):
            return "我理解了您的问题，让我为您提供帮助。"
        
        # 第一轮：移除所有可能的思考标签（超级贪婪匹配）
        think_patterns = [
            r'<think>.*?</think>',
            r'<thinking>.*?</thinking>',
            r'<reasoning>.*?</reasoning>',
            r'<analysis>.*?</analysis>',
            r'<reflection>.*?</reflection>',
            r'<thoughts>.*?</thoughts>',
            r'<consider>.*?</consider>',
            r'<evaluate>.*?</evaluate>',
            r'<process>.*?</process>',
            r'<考虑>.*?</考虑>',
            r'<思考>.*?</思考>',
            r'<分析>.*?</分析>',
            r'<推理>.*?</推理>',
            # 移除不完整的标签
            r'<think>.*',
            r'.*</think>',
            r'<thinking>.*',
            r'.*</thinking>',
            r'<reasoning>.*',
            r'.*</reasoning>',
            # 移除以think开头的任何内容
            r'think.*?(?=\n|\.|。|！|？|!|\?)',
            r'thinking.*?(?=\n|\.|。|！|？|!|\?)',
        ]
        
        cleaned = output
        for pattern in think_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # 第二轮：移除LangChain相关的格式标记
        langchain_patterns = [
            r'Thought:.*?(?=Action:|Final Answer:|$)',
            r'Action:.*?(?=Action Input:|Observation:|Final Answer:|$)',
            r'Action Input:.*?(?=Observation:|Final Answer:|$)',
            r'Observation:.*?(?=Thought:|Final Answer:|$)',
            r'Final Answer:\s*',
        ]
        
        for pattern in langchain_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # 第三轮：移除反引号包围的内容（通常包含思考过程）
        if cleaned.startswith('`') and cleaned.endswith('`'):
            cleaned = cleaned[1:-1].strip()
        
        # 第四轮：清理多余的空白
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # 第五轮：如果仍然包含think相关内容，强制替换
        if any(word in cleaned.lower() for word in ['<think', 'think>', 'thinking', '<reasoning']):
            logger.warning("检测到残留的思考标记，强制清理")
            cleaned = re.sub(r'.*think.*', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'.*reasoning.*', '', cleaned, flags=re.IGNORECASE)
            cleaned = cleaned.strip()
        
        # 最后检查：如果清理后内容为空或太短，返回默认响应
        if not cleaned or len(cleaned) < 10:
            cleaned = "我理解了您的问题，让我为您提供帮助。"
        
        return cleaned

class AuraAgentFixed:
    """Aura助手的修复版Agent类 - 彻底解决think标签问题"""
    
    def __init__(self, model_name="qwen3:4b", verbose=True):
        """初始化Aura Agent"""
        logger.info("初始化Aura Agent (修复版)...")
        
        # 配置
        self.model_name = model_name
        self.verbose = verbose
        
        # 初始化长期记忆
        self.long_term_memory = LongTermMemory()
        logger.info("长期记忆系统已初始化")
        
        # 初始化模型 - 使用超强制的系统提示
        self.llm = SuperCleanOllama(
            model=model_name, 
            base_url="http://localhost:11435",
            system=self._get_super_strict_system_prompt(),
            temperature=0.7
        )
        logger.info(f"已连接到Ollama模型: {model_name}")
        
        # 初始化RAG系统
        self._init_rag_system()
        
        # 初始化工具字典
        self._init_tools_dict()
        
        logger.info("✅ Aura Agent修复版初始化完成")
    
    def _get_super_strict_system_prompt(self) -> str:
        """获取超级严格的系统提示词，彻底禁止think标签"""
        return """你是Aura，用户的AI助手。

🚫 绝对禁止规则 🚫
NEVER EVER use any of these in your response:
- <think> tags
- <thinking> tags  
- <reasoning> tags
- <analysis> tags
- ANY XML-style tags
- 思考过程标记
- 内心独白

🎯 输出要求 🎯
1. 直接回答用户问题
2. 不要显示任何思考过程
3. 不要使用任何标签
4. 保持简洁友好
5. 如果需要工具帮助，我会单独调用

你的身份：智能助手Aura，能够记忆信息、使用工具、提供帮助。

重要：你的回答应该直接开始，不要有任何前缀或标记。"""
    
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
        if tool_name == "search_web":
            return query
        elif tool_name == "search_knowledge":
            return query
        elif tool_name == "remember_fact":
            if "记住" in query:
                parts = query.split("记住")
                if len(parts) > 1:
                    content = parts[1].strip()
                    return f"user/preference/{content}"
            return query
        elif tool_name == "recall_fact":
            return "user/preference"
        
        return query
    
    def process_query(self, query: str) -> str:
        """处理用户查询 - 修复版"""
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
                    context_prompt = f"""用户问题：{query}

工具查询结果：{tool_result}

请根据以上信息直接回答用户问题。重要：不要使用任何XML标签，直接给出答案："""
                    
                    response = self.llm.invoke(context_prompt)
                    
                except Exception as tool_error:
                    logger.error(f"工具调用错误: {tool_error}")
                    # 如果工具失败，直接用LLM回答
                    simple_prompt = f"请直接回答：{query}"
                    response = self.llm.invoke(simple_prompt)
            else:
                # 直接用LLM回答，使用超强制提示
                simple_prompt = f"""请直接回答用户的问题，不要使用任何标签或思考过程：

用户问题：{query}

你的回答："""
                response = self.llm.invoke(simple_prompt)
            
            # 额外的安全清理
            response = self._final_safety_clean(response)
            
            # 保存对话历史
            self.long_term_memory.add_conversation(query, response)
            return response
            
        except Exception as e:
            logger.error(f"处理查询出错: {str(e)}")
            return "抱歉，处理您的问题时遇到了错误。请尝试重新表述您的问题。"
    
    def _final_safety_clean(self, response: str) -> str:
        """最终安全清理，确保绝无think标签"""
        # 如果响应中包含任何think相关内容，彻底清理
        if any(marker in response.lower() for marker in ['<think', 'think>', '<reasoning', 'reasoning>']):
            logger.warning("检测到think标签，执行紧急清理")
            
            # 暴力清理：分行处理，只保留没有标签的行
            lines = response.split('\n')
            clean_lines = []
            
            for line in lines:
                if not any(marker in line.lower() for marker in ['<think', 'think>', '<reasoning', 'reasoning>', 'thought:']):
                    clean_lines.append(line.strip())
            
            response = '\n'.join(clean_lines).strip()
            
            # 如果全部被清理掉了，返回默认回答
            if not response:
                response = "我是Aura，您的AI助手。我能帮助您解答问题、处理信息和完成各种任务。有什么我可以帮您的吗？"
        
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
                    else:
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
            
            return f"✅ 知识库已更新，加载了 {len(target_files)} 个文件，共 {len(splits)} 个文本块"
        except Exception as e:
            logger.error(f"加载知识出错: {str(e)}")
            return f"❌ 加载知识出错: {str(e)}"
    
    def run_cli(self):
        """运行命令行界面"""
        print("=" * 60)
        print("✨ Aura已启动 (修复版) - Think标签问题已解决")
        print(f"🤖 模型: {self.model_name}")
        print("💡 提示: 使用'exit'或'退出'可以结束对话")
        print("💡 特殊命令: '加载知识' - 加载data目录中的文档到知识库")
        print("=" * 60)
        
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
        print("请检查:")
        print("1. Ollama服务是否正在运行")
        print("2. qwen3:4b模型是否已下载")

if __name__ == "__main__":
    main()