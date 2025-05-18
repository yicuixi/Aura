"""
优化知识查询处理器
"""
import re
import logging
from typing import Dict, Any, Optional

from query_handlers import QueryHandler

logger = logging.getLogger("Aura.QueryHandlers.Knowledge")

class KnowledgeQueryHandler(QueryHandler):
    """处理需要从知识库中查找信息的查询"""
    
    def can_handle(self, query: str) -> bool:
        """
        检查是否是知识库相关查询
        
        Args:
            query: 用户查询
            
        Returns:
            布尔值表示是否可以处理
        """
        # 匹配模式：包含"我的""你的""什么""如何""怎么""进度""状态"等关键词
        knowledge_pattern = r'(我的|你的|什么|如何|怎么|进度|状态|论文|研究|项目|学习|工作|准备|面试|英伟达|nvidia)'
        
        # 排除模式：明确指示使用网络搜索或其他工具的查询
        exclude_pattern = r'(联网搜索|搜索网络|使用工具)'
        
        has_knowledge_terms = bool(re.search(knowledge_pattern, query.lower()))
        is_excluded = bool(re.search(exclude_pattern, query.lower()))
        
        return has_knowledge_terms and not is_excluded
    
    def handle(self, query: str, agent_result: Any, memory=None) -> str:
        """
        处理知识库查询
        
        Args:
            query: 用户查询
            agent_result: Agent的中间结果
            memory: 可选的记忆系统引用
            
        Returns:
            处理后的响应
        """
        # 直接使用知识库搜索
        logger.info(f"使用知识库搜索: {query}")
        
        try:
            # 提取搜索结果
            knowledge_results = self.llm.client.chains.retrieval_qa.invoke({"query": query})
            
            if not knowledge_results or not knowledge_results.get("result"):
                # 如果知识库没有找到结果，尝试使用记忆
                if memory:
                    # 构建可能的记忆查询关键词
                    memory_keys = []
                    if "论文" in query:
                        memory_keys.append("user/论文进度")
                    if "面试" in query or "英伟达" in query or "nvidia" in query:
                        memory_keys.append("user/面试")
                    
                    # 尝试从记忆中查找
                    for key in memory_keys:
                        parts = key.split('/')
                        if len(parts) == 2:
                            category, key_name = parts
                            value = memory.get_fact(category, key_name)
                            if value:
                                return f"根据我记录的信息，{key_name}是{value}"
                
                # 如果记忆也没有，则返回一般回答
                response = self.llm.invoke(f"""用户询问: "{query}"
                
看起来我的知识库中没有关于这个问题的详细信息。请以Aura的身份，友好地告诉用户我没有找到相关信息，并询问用户是否需要提供更多上下文。保持礼貌和支持的态度。""").strip()
                
            else:
                # 使用知识库结果生成回答
                response = self.llm.invoke(f"""用户询问: "{query}"
                
从知识库中找到的相关信息:
{knowledge_results["result"]}

请以Aura的身份，给用户一个友好、专业的回答，基于上面的信息。使用自然的对话语气，不要提及"根据知识库"或"从信息中看到"等短语。直接回答用户的问题，就像你非常了解这些信息一样。""").strip()
            
            # 如果有记忆系统，记录对话
            if memory:
                memory.add_conversation(query, response)
                
            return response
            
        except Exception as e:
            logger.error(f"知识库查询失败: {str(e)}")
            return f"我尝试查找相关信息时遇到了一些问题。能请你详细说明一下你的问题，或者换个方式提问吗？"
