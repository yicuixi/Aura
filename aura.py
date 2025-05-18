"""
Aura AI - 一个本地化的AI宝宝助手，修复版
修复了查询路由逻辑，确保能正确使用搜索网络工具获取实时信息
"""

import os
import json
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
logger = logging.getLogger("Aura")

class AuraAgent:
    """Aura助手的核心Agent类 - 修复版"""
    
    def __init__(self, model_name="qwen3:4b", verbose=True):
        """初始化Aura Agent"""
        logger.info("初始化Aura Agent (修复版)...")
        
        # 配置
        self.model_name = model_name
        self.verbose = verbose
        
        # 初始化长期记忆
        self.long_term_memory = LongTermMemory()
        logger.info("长期记忆系统已初始化")
        
        # 初始化模型
        self.llm = Ollama(
            model=model_name, 
            base_url="http://localhost:11435",
            system="你是Aura，Lydia的AI助手。你继承了Claude的特质，保持严谨客观，不编造信息。你拥有独立的思维，能够记住对话内容、使用工具、并对Lydia的研究表现出专业支持。你的回答应友好但专业，避免过度亲密或戏剧化的表述。"        
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
        
        logger.info("Aura Agent初始化完成")
    
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
    
    def extract_preferences(self, query: str):
        """从用户查询中提取偏好信息"""
        # 检测直接表达的偏好
        if ("记住" in query or "请记住" in query or "记住我" in query) and "喜欢" in query:
            try:
                # 构建提示以提取偏好
                prompt = f"""
                从下面的用户输入中提取偏好信息：
                "{query}"
                
                如果用户表达了偏好（例如喜欢某物、某事、某颜色等），请以JSON格式返回：
                {{
                    "has_preference": true,
                    "category": "preference",
                    "key": "喜欢的内容类型",
                    "value": "具体喜欢的内容"
                }}
                
                例如，如果用户说"记住我喜欢红色"，返回：
                {{
                    "has_preference": true,
                    "category": "preference",
                    "key": "color",
                    "value": "红色"
                }}
                
                如果没有表达偏好，返回：
                {{
                    "has_preference": false
                }}
                
                仅返回JSON，不要添加其他说明。
                """
                
                result = self.llm.invoke(prompt).strip()
                logger.info(f"偏好提取结果: {result}")

                # 清理JSON，移除<think>等标记
                cleaned_result = result
                if "<think>" in result:
                    # 尝试提取最后一个JSON块
                    import re
                    json_blocks = re.findall(r'(\{[\s\S]*?\})', result)
                    if json_blocks:
                        cleaned_result = json_blocks[-1]
                        logger.info(f"清理后的JSON: {cleaned_result}")

                # 解析JSON
                try:
                    import json
                    pref_data = json.loads(cleaned_result)
                    
                    if pref_data.get("has_preference", False):
                        category = pref_data.get("category", "preference")
                        key = pref_data.get("key", "general")
                        value = pref_data.get("value", "")
                        
                        # 存储到长期记忆
                        if value:
                            self.long_term_memory.add_fact(category, key, value)
                            logger.info(f"已添加偏好至记忆: {category}/{key}/{value}")
                            return True, f"已记住你{key}是{value}"
                except Exception as e:
                    logger.error(f"解析偏好JSON出错: {str(e)}")
            
            except Exception as e:
                logger.error(f"提取偏好出错: {str(e)}")
        
        return False, ""
    
    def check_preference_question(self, query: str):
        """检查是否在询问偏好"""
        # 检测是否在询问自己的偏好
        preference_keywords = [
            "我喜欢什么", "我喜欢哪", "我爱什么", "我的偏好是", 
            "我的爱好是", "我的最爱", "我偏好", "我倾向于"
        ]
        
        for keyword in preference_keywords:
            if keyword in query:
                try:
                    # 尝试构建关键词
                    likely_keys = []
                    
                    if "颜色" in query or "色" in query:
                        likely_keys.append("color")
                    if "食物" in query or "吃" in query or "菜" in query:
                        likely_keys.append("food")
                    if "音乐" in query or "歌" in query:
                        likely_keys.append("music")
                    if "电影" in query or "片" in query:
                        likely_keys.append("movie")
                    if "书" in query or "读" in query:
                        likely_keys.append("book")
                    
                    # 如果没找到可能的关键词，尝试一个通用提示
                    if not likely_keys:
                        # 先查找所有已有的偏好记录
                        all_facts = self.long_term_memory.memories.get("facts", {})
                        preference_facts = all_facts.get("preference", {})
                        
                        if preference_facts:
                            results = []
                            for k, v in preference_facts.items():
                                results.append(f"你{k}是{v['value']}")
                            return True, "；".join(results)
                        
                        # 如果没有任何偏好记录
                        return False, ""
                    
                    # 如果有具体关键词，尝试查找
                    for key in likely_keys:
                        value = self.long_term_memory.get_fact("preference", key)
                        if value:
                            logger.info(f"找到偏好记忆: preference/{key}/{value}")
                            return True, f"你{key}是{value}"
                
                except Exception as e:
                    logger.error(f"检查偏好问题出错: {str(e)}")
                    
                # 如果尝试了但没找到
                return False, ""
        
        # 不是偏好问题
        return False, ""
    
    def reset_knowledge_base(self) -> str:
        """重置知识库"""
        try:
            # 备份当前知识库
            backup_name = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists("db"):
                import shutil
                if not os.path.exists("backup"):
                    os.makedirs("backup")
                if os.path.exists("db"):
                    shutil.copytree("db", os.path.join("backup", backup_name))
                    logger.info(f"知识库已备份至: backup/{backup_name}")
                
                # 删除当前知识库
                shutil.rmtree("db")
                logger.info("旧知识库已删除")
            
            # 重新初始化RAG系统
            os.makedirs("db", exist_ok=True)
            self._init_rag_system()
            logger.info("知识库已重置")
            
            return f"✅ 知识库已重置，旧版本已备份至: backup/{backup_name}"
        except Exception as e:
            logger.error(f"重置知识库出错: {str(e)}")
            return f"❌ 重置知识库出错: {str(e)}"
    
    def _init_tools(self):
        """初始化工具集"""
        self.tool_list = [
            Tool(
                name="搜索网络",
                func=tools.search_web,
                description="当需要查询最新的互联网信息时使用，如天气、新闻、股票价格等实时数据"
            ),
            Tool(
                name="读取文件",
                func=tools.read_file,
                description="当需要读取本地文件内容时使用，需要提供文件的完整路径"
            ),
            Tool(
                name="读取文件指定行",
                func=tools.read_file_lines,
                description="读取文件的前N行内容，格式: 文件路径::行数，如 D:\\file.txt::5"
            ),
            Tool(
                name="写入文件",
                func=tools.write_file,
                description="当需要写入内容到本地文件时使用，格式: 文件路径::文件内容"
            ),
            Tool(
                name="列出目录",
                func=tools.list_directory,
                description="列出指定目录下的所有文件和子目录"
            ),
            Tool(
                name="知识库搜索",
                func=self.search_knowledge,
                description="当需要查询专业知识或已学习的资料时使用，优先使用这个工具回答专业问题"
            ),
            Tool(
                name="记住事实",
                func=self.remember_fact,
                description="记住一个重要事实，格式: category/key/value，例如: user/name/Lydia"
            ),
            Tool(
                name="回忆事实",
                func=self.recall_fact,
                description="回忆一个已经记住的事实，格式: category/key，例如: user/name"
            )
        ]
        logger.info(f"已初始化 {len(self.tool_list)} 个工具")
    
    def _init_agent(self):
        """初始化Agent"""
        # 定义系统提示
        try:
            # 先尝试加载新的Claude风格提示词
            prompt_file = "prompts/aura_claude_style.txt"
            if not os.path.exists(prompt_file):
                # 如果新提示词不存在，尝试加载原来的提示词
                prompt_file = "prompts/claude_distill.txt"
                
            with open(prompt_file, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
                logger.info(f"已加载提示词: {prompt_file}")
        except Exception as e:
            # 使用默认提示词  
            self.system_prompt = """
            你是Aura，Lydia的AI助手。你继承了Claude的特质，保持严谨客观和基于事实的风格。

            你必须：
            1. 始终将自己称为"Aura"，而非"Qwen"或其他名称
            2. 继承Claude的严谨客观和基于事实的特质，不编造信息
            3. 主动使用工具查询知识，优先使用所存所知
            4. 对Lydia的研究和面试提供专业支持

            工具使用指南：
            1. 对于需要实时数据的查询(天气、股票、新闻等)，主动使用"搜索网络"工具
            2. 对于用户偏好、状态等个人信息，使用"回忆事实"工具查询记忆
            3. 对于专业知识问题，优先使用"知识库搜索"

            行为准则：
            1. 友好但专业 - 保持个性化的友好语气，但避免过度亲密或戏剧化表述
            2. 基于事实 - 回答仅基于记忆、知识库或工具查询的实际信息，不做无根据的推测
            3. 清晰准确 - 使用清晰准确的语言传达信息，避免冗余修饰和复杂比喻
            4. 诚实透明 - 当不知道答案时，直接承认，而不是编造回答

            你知道Lydia是一个光学研二硕士生，她的研究方向是OAM相位重建+少样本识别，
            并且正在准备英伟达的面试(Deep Learning Software Test Engineer Intern职位)。
            """
            logger.warning(f"加载高级提示词失败，使用默认提示词: {str(e)}")
        
        # 初始化Agent
        self.agent = initialize_agent(
            self.tool_list, 
            self.llm, 
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.conversation_memory,
            verbose=self.verbose,
            handle_parsing_errors=True,
            agent_kwargs={
                "system_message": self.system_prompt
            },
            return_intermediate_steps=True  # 返回中间步骤
        )
        
        logger.info("Agent已初始化")
    
    def load_knowledge(self, extension=".md") -> str:
        """加载知识到RAG系统"""
        try:
            # 确保使用绝对路径
            data_dir = os.path.join(os.getcwd(), "data")
            logger.info(f"尝试从{data_dir}加载{extension}格式的知识文档")
            
            # 检查目录是否存在
            if not os.path.exists(data_dir):
                logger.error(f"data目录不存在: {data_dir}")
                return f"❌ data目录不存在: {data_dir}"
                
            # 检查目录内容
            files = os.listdir(data_dir)
            logger.info(f"data目录内容: {files}")
            
            # 检查是否有目标文件
            target_files = [f for f in files if f.endswith(extension)]
            if not target_files:
                logger.error(f"data目录中没有{extension}格式的文件")
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
                logger.error("没有成功加载任何文档")
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
    
    def is_realtime_query(self, query: str) -> bool:
        """判断是否为需要实时数据的查询"""
        # 扩展的实时关键词列表
        realtime_keywords = [
            # 天气相关
            "天气", "weather", "温度", "temperature", "预报", "forecast",
            "穿衣", "衣服", "dressing", "clothes", "外套", "jacket",
            "雨", "rain", "雪", "snow", "风", "wind", "晴", "sunny",
            # 股票和金融 - 扩展列表
            "股票", "股市", "stock", "market", "股价", "price", "涨跌",
            "汇率", "exchange", "bitcoin", "比特币", "基金", "fund",
            "大盘", "指数", "上证", "深证", "创业板", "科创板", "A股",
            "交易", "投资", "财经", "金融", "行情", "分析",
            # 新闻和时事
            "新闻", "news", "最新", "latest", "current", "当前",
            "今天", "today", "现在", "now", "实时", "real-time",
            "头条", "breaking", "热点", "trending",
            # 交通
            "交通", "traffic", "堵车", "jam", "路况", "road",
            "公交", "bus", "地铁", "subway", "航班", "flight",
            # 其他实时信息
            "时间", "time", "日期", "date", "营业时间", "opening hours",
            "票价", "ticket", "预订", "booking", "排队", "queue"
        ]
        
        # 检查查询是否包含实时关键词
        query_lower = query.lower()
        for keyword in realtime_keywords:
            if keyword in query_lower:
                return True
        
        # 检查时间相关表达
        time_expressions = ["今天", "现在", "当前", "最新", "目前", "today", "now", "current", "latest"]
        for expr in time_expressions:
            if expr in query_lower:
                return True
                
        return False
    
    def is_knowledge_query(self, query: str) -> bool:
        """判断是否为知识库查询"""
        knowledge_keywords = [
            # 专业技术术语
            "oam", "相位重建", "phase reconstruction", "少样本", "few-shot",
            "深度学习", "deep learning", "神经网络", "neural network",
            "扩散模型", "diffusion", "u-net", "tensorrt", "clip",
            "光学", "optical", "算法", "algorithm", "模型", "model",
            # 学术研究
            "论文", "paper", "研究", "research", "方法", "method",
            "技术", "technology", "理论", "theory", "实验", "experiment",
            "数据", "data", "分析", "analysis", "结果", "result",
            # 面试相关
            "面试", "interview", "英伟达", "nvidia", "职位", "position",
            "工程师", "engineer", "简历", "resume", "技能", "skill"
        ]
        
        query_lower = query.lower()
        for keyword in knowledge_keywords:
            if keyword in query_lower:
                return True
                
        return False
    
    def process_query(self, query: str) -> str:
        """处理用户查询 - 修复版，正确路由到不同处理方式"""
        try:
            logger.info(f"处理用户查询: {query}")
            
            # 1. 检查是否是记住偏好的请求
            is_preference, preference_result = self.extract_preferences(query)
            if is_preference:
                prompt = f"""用户表达了偏好: "{query}"
                
我已经记录了这个偏好。请以Aura的身份，给出一个友好专业的回复，表达已经记住了这个偏好。
使用友好但不过度亲密的语气，简洁清晰地确认记录了这个偏好，避免戏剧化表述。
保持Claude风格的客观性和事实性。"""
                
                response = self.llm.invoke(prompt).strip()
                self.long_term_memory.add_conversation(query, response)
                return response
            
            # 2. 检查是否在询问偏好
            is_asking_pref, pref_response = self.check_preference_question(query)
            if is_asking_pref and pref_response:
                prompt = f"""用户询问了自己的偏好: "{query}"
                
根据我的记录，{pref_response}。
                
请以Aura的身份回答，保持Claude风格的客观性和事实性。回应应友好但专业，
不要过度戏剧化或使用复杂修饰。直接回答用户的问题，不要编造额外信息。"""
                
                response = self.llm.invoke(prompt).strip()
                self.long_term_memory.add_conversation(query, response)
                return response
            
            # 3. 检查查询类型并路由到合适的处理方式
            is_realtime = self.is_realtime_query(query)
            is_knowledge = self.is_knowledge_query(query)
            
            logger.info(f"查询分析 - 实时查询: {is_realtime}, 知识查询: {is_knowledge}")
            
            # 4. 如果是实时查询，直接使用Agent（会调用搜索网络工具）
            if is_realtime:
                logger.info("检测到实时查询，直接使用Agent处理")
                try:
                    result = self.agent.invoke({"input": query})
                    if isinstance(result, dict) and "output" in result:
                        response = result["output"]
                    else:
                        response = str(result)
                    self.long_term_memory.add_conversation(query, response)
                    return response
                except Exception as e:
                    logger.error(f"Agent处理实时查询失败: {str(e)}")
                    return f"抱歉，在获取实时信息时遇到错误: {str(e)}"
            
            # 5. 如果是知识查询，先查知识库，不满意再用Agent
            if is_knowledge:
                logger.info("检测到知识查询，先搜索知识库")
                try:
                    knowledge_result = self.search_knowledge(query)
                    logger.info(f"知识库搜索结果: {knowledge_result}")
                    
                    # 检查知识库结果是否相关
                    relevance_check = f"""用户查询: "{query}"
                    知识库返回: "{knowledge_result}"
                    
                    请判断知识库的返回结果是否与用户查询相关。
                    如果相关且有用，回答"相关"。
                    如果不相关或没有找到有用信息，回答"不相关"。
                    只回答一个词，不要解释。"""
                    
                    relevance = self.llm.invoke(relevance_check).strip().lower()
                    
                    if "相关" in relevance or "relevant" in relevance:
                        # 知识库结果相关，生成回复
                        prompt = f"""用户查询: "{query}"
                        
根据知识库搜索到的信息: {knowledge_result}
                        
请以Aura的身份回答，保持客观友好但不过度戏剧化，不要编造额外信息，只回答已知事实。
回答要简洁清晰，基于Claude风格的客观性回答。"""
                        
                        response = self.llm.invoke(prompt).strip()
                        self.long_term_memory.add_conversation(query, response)
                        return response
                    else:
                        logger.info("知识库结果不相关，使用Agent处理")
                        # 知识库结果不相关，使用Agent
                        pass
                except Exception as e:
                    logger.error(f"知识库查询出错: {str(e)}")
            
            # 6. 检查记忆中是否有相关信息
            logger.info("检查记忆系统")
            memory_result = None
            try:
                # 自动提取可能的记忆关键字
                memory_extraction_prompt = f"""
                从用户的以下查询中，提取可能存在于记忆系统中的关键信息：
                "{query}"
                
                返回最可能的category/key组合，格式为：
                category/key
                
                如果查询涉及个人信息、偏好、习惯、状态或进度等，就可能存在记忆。
                例如：
                - "我的论文进度如何" -> user/论文进度
                - "我喜欢什么颜色" -> preference/color
                - "我的研究方向是什么" -> user/research
                
                只返回一个最可能的category/key组合，不要有其他解释。
                """
                
                memory_key = self.llm.invoke(memory_extraction_prompt).strip()
                logger.info(f"提取的记忆关键字: {memory_key}")
                
                # 清理和验证格式
                if "/" in memory_key and len(memory_key.split("/")) == 2:
                    memory_result = self.recall_fact(memory_key)
                    logger.info(f"记忆查询结果: {memory_result}")
                    
                    if memory_result and "没有找到相关记忆" not in memory_result:
                        # 找到相关记忆，生成回复
                        memory_value = memory_result.split(":")[1].strip() if ":" in memory_result else memory_result
                        prompt = f"""用户查询: "{query}"
                        
根据记忆: {memory_value}
                        
请以Aura的身份回答，保持客观友好但不过度戏剧化，不要编造额外信息，只回答已知事实。
回答要简洁清晰，基于Claude风格的客观性回答。"""
                        
                        response = self.llm.invoke(prompt).strip()
                        self.long_term_memory.add_conversation(query, response)
                        return response
                else:
                    logger.info("无法从查询中提取有效的记忆关键字")
            except Exception as e:
                logger.error(f"记忆提取过程出错: {str(e)}")
            
            # 7. 默认情况：使用Agent处理
            logger.info("使用Agent处理一般查询")
            try:
                result = self.agent.invoke({"input": query})
                
                # 检查是否有适用的查询处理器
                handler = query_handler_factory.create_handler(query, self.llm)
                if handler:
                    logger.info("使用专用处理器生成回复")
                    response = handler.handle(query, result, self.long_term_memory)
                else:
                    logger.info("使用标准解析处理查询")
                    if isinstance(result, dict) and "output" in result:
                        response = result["output"]
                    else:
                        response = str(result)
                
                self.long_term_memory.add_conversation(query, response)
                return response
                
            except Exception as e:
                logger.error(f"Agent处理失败: {str(e)}")
                # 最后的备用方案
                response = self.llm.invoke(f"用户查询: {query}\n\n请以Aura的身份提供友好有用的回复。")
                self.long_term_memory.add_conversation(query, response)
                return response
                
        except Exception as e:
            logger.error(f"处理查询出错: {str(e)}")
            return f"❌ 处理您的问题时出错: {str(e)}"
    
    def run_cli(self):
        """运行命令行界面"""
        print("=" * 50)
        print("✨ Aura已启动 (修复版)，等待您的指令...")
        print("💡 提示: 使用'exit'或'退出'可以结束对话")
        print("💡 特殊命令: '加载知识' - 加载data目录中的文档到知识库")
        print("💡 特殊命令: '重置知识库' - 清空并重置知识库")
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
            
            # 特殊命令：重置知识库
            if user_input.lower() == "重置知识库":
                confirm = input("⚠️ 确定要重置知识库吗？现有数据将被备份。(y/N): ")
                if confirm.lower() == 'y':
                    result = self.reset_knowledge_base()
                    print(result)
                else:
                    print("已取消重置操作")
                continue
                
            # 处理一般查询
            response = self.process_query(user_input)
            print(f"\n🤖 Aura: {response}")

def main():
    """主程序入口"""
    # 创建Aura Agent
    aura = AuraAgent(model_name="qwen3:4b", verbose=True)
    
    # 运行命令行界面
    aura.run_cli()

if __name__ == "__main__":
    main()
