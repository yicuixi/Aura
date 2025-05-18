"""
投资和股市相关查询处理器
"""
import re
import logging
from typing import Dict, Any, Optional

from query_handlers import QueryHandler

logger = logging.getLogger("Aura.QueryHandlers.Investment")

class InvestmentHandler(QueryHandler):
    """处理与投资、股市、金融市场相关的查询"""
    
    def can_handle(self, query: str) -> bool:
        """
        检查是否是投资/股市相关查询
        
        Args:
            query: 用户查询
            
        Returns:
            布尔值表示是否可以处理
        """
        # 匹配模式：包含股市/投资/基金等词，且包含建议/分析/资讯等词
        investment_pattern = r'(股市|投资|基金|股票|证券|金融市场|理财|债券)'
        analysis_pattern = r'(建议|分析|资讯|行情|走势|预测|策略|报告)'
        
        has_investment = bool(re.search(investment_pattern, query))
        has_analysis = bool(re.search(analysis_pattern, query))
        
        return has_investment and has_analysis
    
    def handle(self, query: str, agent_result: Any, memory=None) -> str:
        """
        处理投资相关查询
        
        Args:
            query: 用户查询
            agent_result: Agent的中间结果
            memory: 可选的记忆系统引用
            
        Returns:
            处理后的响应
        """
        # 提取搜索结果
        search_results = self.extract_search_results(agent_result)
        
        if not search_results:
            logger.warning("投资处理器没有找到搜索结果，返回默认回复")
            return "很抱歉，我无法获取相关的市场信息。请尝试更具体的查询，或稍后再试。"
        
        # 根据查询类型定制提示词
        if "股市" in query and "资讯" in query:
            prompt_template = self._get_market_news_prompt(query, search_results)
        elif "投资建议" in query or "投资策略" in query:
            prompt_template = self._get_investment_advice_prompt(query, search_results)
        elif "分析" in query:
            prompt_template = self._get_market_analysis_prompt(query, search_results)
        else:
            prompt_template = self._get_general_finance_prompt(query, search_results)
        
        # 使用LLM生成回复
        logger.info("使用定制提示词生成投资相关回复")
        response = self.llm.invoke(prompt_template).strip()
        
        # 如果有记忆系统，记录对话
        if memory:
            memory.add_conversation(query, response)
            
        return response
    
    def _get_market_news_prompt(self, query: str, search_results: str) -> str:
        """生成市场新闻提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于以上搜索结果，提供今日市场资讯概述。请涵盖以下内容:

1. 主要指数表现与重要涨跌数据
2. 热门板块与个股动向
3. 关键市场新闻与事件
4. 可能的市场走势分析

请使用客观、专业的语言，避免过度预测。回复应简洁清晰，便于快速理解。
"""
    
    def _get_investment_advice_prompt(self, query: str, search_results: str) -> str:
        """生成投资建议提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于以上搜索结果，为用户提供一份简洁清晰的投资策略建议。包括以下几个方面：

1. 主要行业板块机会与风险（如科技、金融、消费等）
2. 短期与长期投资策略区分
3. 风险管理建议
4. 需要关注的具体指标或新闻

请确保:
- 用语简洁易懂，避免使用过多专业术语
- 不做绝对的买卖建议
- 在最后注明投资有风险，本建议仅供参考

这不构成正式的投资建议，请用户结合自身风险承受能力和财务状况做决策。
"""
    
    def _get_market_analysis_prompt(self, query: str, search_results: str) -> str:
        """生成市场分析提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于以上搜索结果，提供一份市场分析。请包含：

1. 市场环境总体评估
2. 主要指数技术面分析
3. 影响市场的宏观因素
4. 行业轮动或资金流向分析
5. 未来可能的变化因素

分析应该客观且基于事实，避免过度主观判断。使用清晰的结构和简洁的语言，便于用户理解复杂的市场情况。
"""
    
    def _get_general_finance_prompt(self, query: str, search_results: str) -> str:
        """生成通用金融提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于以上搜索结果，回答用户的金融相关问题。回答应该：

1. 直接针对用户问题
2. 使用清晰、易懂的语言
3. 提供有用的背景信息
4. 在合适的情况下提供后续行动建议

避免使用过多专业术语，并确保信息准确、客观。如搜索结果不足以完全回答问题，请明确指出并提供基于可用信息的最佳回答。
"""
