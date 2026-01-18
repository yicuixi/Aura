# -*- coding: utf-8 -*-
"""验证检索结果是否真实"""
from rag import RAGSystem

rag = RAGSystem()

# 测试几个问题
test_questions = [
    ("半线天竺鲷的体长可达多少公分？", "12公分"),
    ("默哀通常用于哀悼哪些人？", "重要人物"),
    ("嘉兴南站建筑总面积为多少平方米？", "5.6万平方米"),
]

for q, expected in test_questions:
    print("=" * 50)
    print(f"问题: {q}")
    print(f"期望答案: {expected}")
    print()
    
    results = rag.search(q, k=3)
    for i, doc in enumerate(results):
        content = doc.page_content[:200]
        # 检查答案是否在结果中
        has_answer = expected in doc.page_content
        status = "✅ 包含答案" if has_answer else "❌ 不包含答案"
        print(f"结果 {i+1} {status}:")
        print(f"  {content}...")
        print()

