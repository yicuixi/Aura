"""
查询处理器注册
"""
from query_handlers import factory
from query_handlers.investment import InvestmentHandler
from query_handlers.text_generation import LongTextHandler
from query_handlers.technical import TechnicalHandler

# 注册所有处理器
def register_all_handlers():
    """注册所有查询处理器"""
    factory.register_handler(InvestmentHandler)
    factory.register_handler(LongTextHandler)
    factory.register_handler(TechnicalHandler)
    # 在这里注册更多处理器...

# 确保处理器已注册
register_all_handlers()
