"""
长文本生成与分析处理器
"""
import re
import logging
from typing import Dict, Any, Optional

from query_handlers import QueryHandler

logger = logging.getLogger("Aura.QueryHandlers.TextGeneration")

class LongTextHandler(QueryHandler):
    """处理需要生成长文本的查询，如文章摘要、报告分析等"""
    
    def can_handle(self, query: str) -> bool:
        """
        检查是否是需要生成长文本的查询
        
        Args:
            query: 用户查询
            
        Returns:
            布尔值表示是否可以处理
        """
        # 匹配模式：包含摘要/总结/分析/报告等词，且查询较长
        generation_pattern = r'(摘要|总结|概述|分析|报告|文章|写一篇|生成|写作)'
        
        has_generation_terms = bool(re.search(generation_pattern, query))
        is_complex_query = len(query) > 15  # 简单判断查询复杂度
        
        return has_generation_terms and is_complex_query
    
    def handle(self, query: str, agent_result: Any, memory=None) -> str:
        """
        处理长文本生成查询
        
        Args:
            query: 用户查询
            agent_result: Agent的中间结果
            memory: 可选的记忆系统引用
            
        Returns:
            处理后的响应
        """
        # 提取搜索结果
        search_results = self.extract_search_results(agent_result)
        
        # 根据查询类型定制提示词
        if "摘要" in query or "总结" in query:
            prompt_template = self._get_summarization_prompt(query, search_results)
        elif "报告" in query:
            prompt_template = self._get_report_prompt(query, search_results)
        elif "分析" in query:
            prompt_template = self._get_analysis_prompt(query, search_results)
        else:
            prompt_template = self._get_general_writing_prompt(query, search_results)
        
        # 使用LLM生成回复
        logger.info("使用定制提示词生成长文本回复")
        response = self.llm.invoke(prompt_template).strip()
        
        # 如果有记忆系统，记录对话
        if memory:
            memory.add_conversation(query, response)
            
        return response
    
    def _get_summarization_prompt(self, query: str, search_results: str) -> str:
        """生成摘要提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于以上搜索结果，生成一份简洁而全面的摘要。摘要应该：

1. 捕捉主要观点和关键信息
2. 保持客观，不添加未提及的内容
3. 使用清晰、流畅的语言
4. 保持逻辑结构，便于理解

请确保摘要涵盖所有重要内容，同时避免冗余和不必要的细节。
"""
    
    def _get_report_prompt(self, query: str, search_results: str) -> str:
        """生成报告提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于上述搜索结果，生成一份专业的报告。报告应包含：

1. 简明的概述部分，说明主题和关键发现
2. 主体内容，按逻辑顺序组织，使用小标题分隔
3. 相关数据和趋势分析（如果适用）
4. 结论和建议部分

报告应当专业、客观，使用清晰的结构和准确的语言。确保内容基于事实，避免无根据的推测。
"""
    
    def _get_analysis_prompt(self, query: str, search_results: str) -> str:
        """生成分析提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于上述搜索结果，提供一份深入分析。分析应该：

1. 识别核心问题或主题
2. 探讨相关因素和影响
3. 考虑不同角度和观点
4. 提供基于证据的见解
5. 在适当情况下提出建议或预测

分析应该客观、全面，关注事实和逻辑推理。避免过度简化复杂问题，并承认不确定性存在的地方。
"""
    
    def _get_general_writing_prompt(self, query: str, search_results: str) -> str:
        """生成通用写作提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于上述搜索结果和用户的请求，创作一篇文章。文章应该：

1. 符合用户指定的主题和要求
2. 结构清晰，包括引言、主体和结论
3. 语言流畅自然，适合目标读者
4. 信息准确，观点合理

如果用户指定了特定格式、风格或长度要求，请务必遵循。创作时应注重原创性和质量，避免简单拼凑搜索结果。
"""
