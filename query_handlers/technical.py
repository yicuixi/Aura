"""
技术文档和代码生成处理器
"""
import re
import logging
from typing import Dict, Any, Optional

from query_handlers import QueryHandler

logger = logging.getLogger("Aura.QueryHandlers.TechDocs")

class TechnicalHandler(QueryHandler):
    """处理技术文档和代码生成相关查询"""
    
    def can_handle(self, query: str) -> bool:
        """
        检查是否是技术或代码相关查询
        
        Args:
            query: 用户查询
            
        Returns:
            布尔值表示是否可以处理
        """
        # 匹配模式：包含代码/编程/开发/技术文档等词
        tech_pattern = r'(代码|编程|程序|开发|API|函数|类|对象|接口|技术文档|算法)'
        action_pattern = r'(生成|编写|实现|创建|写一个|开发|设计)'
        
        has_tech_terms = bool(re.search(tech_pattern, query))
        has_action_terms = bool(re.search(action_pattern, query))
        
        return has_tech_terms and has_action_terms
    
    def handle(self, query: str, agent_result: Any, memory=None) -> str:
        """
        处理技术和代码相关查询
        
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
        if "代码" in query or "程序" in query or "函数" in query:
            prompt_template = self._get_code_generation_prompt(query, search_results)
        elif "API" in query or "接口" in query:
            prompt_template = self._get_api_doc_prompt(query, search_results)
        elif "算法" in query:
            prompt_template = self._get_algorithm_prompt(query, search_results)
        else:
            prompt_template = self._get_general_tech_prompt(query, search_results)
        
        # 使用LLM生成回复
        logger.info("使用定制提示词生成技术相关回复")
        response = self.llm.invoke(prompt_template).strip()
        
        # 如果有记忆系统，记录对话
        if memory:
            memory.add_conversation(query, response)
            
        return response
    
    def _get_code_generation_prompt(self, query: str, search_results: str) -> str:
        """生成代码提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于用户的请求，生成高质量的代码实现。代码应该：

1. 完整且可运行，不缺少关键部分
2. 遵循编程最佳实践和设计模式
3. 包含适当的注释和文档字符串
4. 考虑边缘情况和错误处理

请在代码前后提供简短的解释，说明实现思路和使用方法。如果有多种实现方式，可以简要说明不同方法的优缺点。

请使用清晰的代码块格式（使用```标记），确保代码可以被轻松复制使用。
"""
    
    def _get_api_doc_prompt(self, query: str, search_results: str) -> str:
        """生成API文档提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于用户的请求，生成清晰详细的API文档。文档应该包含：

1. API概述和用途
2. 详细的端点/函数说明
3. 请求/参数格式和示例
4. 响应格式和示例
5. 错误处理和状态码说明
6. 使用限制或注意事项（如果有）

文档应使用标准的技术文档格式，易于阅读和理解。如有需要，提供简洁的示例代码来演示API的使用方法。
"""
    
    def _get_algorithm_prompt(self, query: str, search_results: str) -> str:
        """生成算法提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于用户的请求，实现并解释所需的算法。回答应包含：

1. 算法的原理和背景介绍
2. 清晰的伪代码或实际代码实现
3. 算法的时间和空间复杂度分析
4. 实际应用场景和限制
5. 优化思路或变种算法（如果适用）

确保代码高效且正确，并提供足够的注释。对于复杂算法，可以提供步骤分解和具体示例来帮助理解。
"""
    
    def _get_general_tech_prompt(self, query: str, search_results: str) -> str:
        """生成通用技术提示词"""
        return f"""用户查询: {query}
        
搜索结果:
{search_results}
        
请基于用户的技术相关请求，提供详细而准确的回答。回答应该：

1. 直接解决用户的问题或需求
2. 提供足够的技术细节和背景知识
3. 使用清晰的结构组织信息
4. 在适当的情况下提供代码示例或技术参考

回答应该既适合技术人员理解，又尽可能简明易懂。如涉及多种技术或解决方案，请比较它们的优缺点，帮助用户做出明智的选择。
"""
