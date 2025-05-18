"""
查询处理器基类与工厂
"""
import re
import logging
from typing import Dict, List, Any, Optional, Callable, Type, Union

# 设置日志
logger = logging.getLogger("Aura.QueryHandlers")

class QueryHandler:
    """所有查询处理器的基类"""
    
    def __init__(self, llm=None):
        """初始化查询处理器"""
        self.llm = llm
    
    def can_handle(self, query: str) -> bool:
        """
        确定此处理器是否可以处理给定的查询
        
        Args:
            query: 用户的原始查询文本
            
        Returns:
            布尔值表示该处理器是否适合处理此查询
        """
        raise NotImplementedError("子类必须实现can_handle方法")
    
    def handle(self, query: str, agent_result: Any, memory=None) -> str:
        """
        处理查询并返回结果
        
        Args:
            query: 用户的原始查询
            agent_result: 从Agent获取的中间结果(通常包含工具调用等)
            memory: 可选的记忆系统引用
            
        Returns:
            处理后的响应文本
        """
        raise NotImplementedError("子类必须实现handle方法")
    
    def extract_search_results(self, agent_result: Any) -> str:
        """
        从Agent结果中提取搜索结果
        
        Args:
            agent_result: Agent返回的结果对象
            
        Returns:
            搜索结果文本，如果没有则返回空字符串
        """
        search_results = ""
        # 检查中间步骤
        if isinstance(agent_result, dict) and "intermediate_steps" in agent_result:
            for action, observation in agent_result["intermediate_steps"]:
                if hasattr(action, "tool") and action.tool == "搜索网络" and isinstance(observation, str):
                    if "搜索结果:" in observation:
                        search_results = observation
                        break
        return search_results


class QueryHandlerFactory:
    """查询处理器工厂，负责创建和管理查询处理器"""
    
    def __init__(self):
        """初始化工厂"""
        self.handlers: List[Type[QueryHandler]] = []
        
    def register_handler(self, handler_class: Type[QueryHandler]):
        """
        注册一个查询处理器类
        
        Args:
            handler_class: 要注册的查询处理器类
        """
        self.handlers.append(handler_class)
        logger.info(f"已注册查询处理器: {handler_class.__name__}")
        
    def create_handler(self, query: str, llm) -> Optional[QueryHandler]:
        """
        为给定查询创建合适的处理器实例
        
        Args:
            query: 用户查询
            llm: 语言模型实例
            
        Returns:
            适合处理查询的处理器实例，如果没有找到则返回None
        """
        for handler_class in self.handlers:
            handler = handler_class(llm)
            if handler.can_handle(query):
                logger.info(f"使用 {handler_class.__name__} 处理查询: {query[:50]}...")
                return handler
        
        logger.info(f"没有找到合适的处理器，将使用默认处理: {query[:50]}...")
        return None


# 全局工厂实例
factory = QueryHandlerFactory()
