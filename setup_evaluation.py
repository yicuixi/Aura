# -*- coding: utf-8 -*-
"""
正确的评估流程：
1. 把公开数据集的 context 加载到 RAG 知识库
2. 用 question 测试检索效果
"""
import json
import os

def prepare_rag_documents():
    """从公开数据集提取 context，生成文档供 RAG 加载"""
    
    # 读取公开数据集
    with open('evaluation/chinese_qa_100.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 创建文档目录
    doc_dir = 'data/eval_docs'
    os.makedirs(doc_dir, exist_ok=True)
    
    # 每个 context 生成一个文档
    for i, item in enumerate(data):
        context = item.get('context', '')
        if context and len(context) > 50:
            filename = f'{doc_dir}/doc_{i:03d}.md'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# 文档 {i+1}\n\n{context}\n")
    
    print(f"已生成 {len(data)} 个文档到 {doc_dir}/")
    return doc_dir


def generate_test_dataset():
    """生成测试数据集，question + expected_answer + relevant_docs"""
    
    with open('evaluation/chinese_qa_100.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    rag_tests = []
    for i, item in enumerate(data[:50]):
        rag_tests.append({
            "id": f"eval_{i:03d}",
            "question": item['question'],
            "expected_answer": item['answer'],
            "relevant_docs": [f"doc_{i:03d}.md"],  # 对应的文档
            "category": "公开数据集"
        })
    
    # 生成测试数据集
    test_dataset = {
        "metadata": {
            "version": "5.0",
            "description": "基于 CMRC2018 的正确评估数据集",
            "source": "CMRC2018 (哈工大)",
            "total_cases": len(rag_tests),
            "note": "context 已加载到知识库，用 question 测试检索"
        },
        "rag_tests": rag_tests,
        "agent_tests": []
    }
    
    with open('evaluation/test_dataset.json', 'w', encoding='utf-8') as f:
        json.dump(test_dataset, f, ensure_ascii=False, indent=2)
    
    print(f"已生成测试数据集: evaluation/test_dataset.json")
    print(f"- RAG 测试: {len(rag_tests)} 条")


def load_to_rag():
    """加载文档到 RAG"""
    from rag import RAGSystem
    
    rag = RAGSystem(persist_directory="db")
    rag.add_documents('data/eval_docs', extension='.md')
    print("文档已加载到 RAG 知识库")


if __name__ == '__main__':
    print("=" * 50)
    print("📚 正确的评估流程")
    print("=" * 50)
    
    # 1. 生成文档
    print("\n1️⃣ 从数据集提取 context 生成文档...")
    doc_dir = prepare_rag_documents()
    
    # 2. 加载到 RAG
    print("\n2️⃣ 加载文档到 RAG 知识库...")
    load_to_rag()
    
    # 3. 生成测试数据集
    print("\n3️⃣ 生成测试数据集...")
    generate_test_dataset()
    
    print("\n" + "=" * 50)
    print("✅ 完成！现在可以运行评估了")
    print("   python run_evaluation.py --rag --save")
    print("=" * 50)

