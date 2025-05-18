# Aura Query Handlers System

这个系统提供了一种灵活、可扩展的方式来处理不同类型的复杂查询。它通过模式识别来确定最适合处理特定查询的专门处理器，并使用定制的提示词来生成高质量的回复。

## 系统架构

查询处理系统由以下部分组成：

1. **查询处理器基类** (`QueryHandler`): 定义了所有处理器必须实现的接口
2. **处理器工厂** (`QueryHandlerFactory`): 管理和创建处理器实例
3. **专门处理器**: 处理特定类型的查询，例如：
   - `InvestmentHandler`: 处理股市、投资分析
   - `LongTextHandler`: 处理长文本生成如摘要、报告
   - `TechnicalHandler`: 处理技术文档和代码生成

## 工作流程

1. 当用户输入查询时，系统首先使用Agent获取中间结果（如搜索结果）
2. 然后，查询处理器工厂检查是否有适合处理该查询的专门处理器
3. 如果找到合适的处理器，系统使用它生成定制回复
4. 如果没有合适的处理器，系统回退到标准的Agent处理

## 扩展系统

### 添加新的查询处理器

1. 创建一个新的处理器类，继承自`QueryHandler`基类
2. 实现`can_handle`和`handle`方法
3. 在`registry.py`中注册新处理器

```python
# 处理器类模板
class NewHandler(QueryHandler):
    def can_handle(self, query: str) -> bool:
        # 识别这个处理器适用的查询类型
        pattern = r'(关键词1|关键词2|关键词3)'
        return bool(re.search(pattern, query))
    
    def handle(self, query: str, agent_result: Any, memory=None) -> str:
        # 处理查询并生成回复
        search_results = self.extract_search_results(agent_result)
        prompt = self._get_custom_prompt(query, search_results)
        response = self.llm.invoke(prompt).strip()
        return response
```

### 注册新处理器

```python
# registry.py
def register_all_handlers():
    factory.register_handler(InvestmentHandler)
    factory.register_handler(LongTextHandler)
    factory.register_handler(TechnicalHandler)
    factory.register_handler(NewHandler)  # 添加新处理器
```

## 优势

- **可扩展性**: 易于添加新的处理器来支持更多类型的查询
- **模块化**: 每个处理器负责特定类型的查询，便于维护
- **可靠性**: 如果处理器失败，系统会回退到标准处理
- **定制化**: 针对不同类型的查询使用定制的提示词
