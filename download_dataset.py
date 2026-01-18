# -*- coding: utf-8 -*-
"""
下载公开问答数据集 - 重构版
"""
from datasets import load_dataset
import json
import random

def download_cmrc():
    """下载 CMRC2018 中文阅读理解数据集"""
    print("正在下载 CMRC2018 数据集...")
    ds = load_dataset('cmrc2018', split='validation', trust_remote_code=True)
    
    qa_pairs = []
    for item in ds:
        q = item.get('question', '')
        answers = item.get('answers', {}).get('text', [])
        a = answers[0] if answers else ''
        context = item.get('context', '')
        
        if q and a and len(a) > 1:
            qa_pairs.append({
                'question': q,
                'answer': a,
                'context': context[:500],  # 限制上下文长度
                'source': 'cmrc2018'
            })
    
    print(f"获取了 {len(qa_pairs)} 条问答")
    return qa_pairs


def download_webqa():
    """尝试下载 WebQA 或其他中文 QA 数据集"""
    print("正在尝试下载 DuReader 数据集...")
    try:
        # DuReader Robust
        ds = load_dataset('PaddlePaddle/dureader_robust', split='validation', trust_remote_code=True)
        
        qa_pairs = []
        for item in ds:
            q = item.get('question', '')
            a = item.get('answers', [''])[0] if item.get('answers') else ''
            context = item.get('context', '')
            
            if q and a:
                qa_pairs.append({
                    'question': q,
                    'answer': a,
                    'context': context[:500],
                    'source': 'dureader'
                })
                if len(qa_pairs) >= 100:
                    break
        
        print(f"获取了 {len(qa_pairs)} 条 DuReader 问答")
        return qa_pairs
    except Exception as e:
        print(f"DuReader 下载失败: {e}")
        return []


if __name__ == '__main__':
    # 下载数据集
    cmrc_data = download_cmrc()
    dureader_data = download_webqa()
    
    # 合并并随机采样
    all_data = cmrc_data + dureader_data
    random.shuffle(all_data)
    
    # 取100条用于评估
    sample_data = all_data[:100]
    
    # 保存原始数据
    with open('evaluation/chinese_qa_100.json', 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(sample_data)} 条中文问答到 evaluation/chinese_qa_100.json")
    
    # 生成评估格式的数据集
    eval_dataset = {
        "metadata": {
            "version": "4.0",
            "description": "公开中文问答数据集 - CMRC2018 + DuReader",
            "source": ["CMRC2018 (哈工大)", "DuReader (百度)"],
            "total_cases": len(sample_data),
            "note": "这是真实的公开数据集，非自己编造"
        },
        "rag_tests": [
            {
                "id": f"open_{i:03d}",
                "question": item["question"],
                "expected_answer": item["answer"],
                "context": item.get("context", "")[:200],
                "source": item.get("source", "unknown"),
                "relevant_docs": []
            }
            for i, item in enumerate(sample_data[:50])
        ],
        "agent_tests": [
            {
                "id": f"agent_open_{i:03d}",
                "question": item["question"],
                "expected_tool": "search_web",  # 开放域问题用网络搜索
                "expected_contains": [],
                "ground_truth": item["answer"],  # 真实答案作为参考
                "match_any": True
            }
            for i, item in enumerate(sample_data[50:100])
        ]
    }
    
    with open('evaluation/open_dataset.json', 'w', encoding='utf-8') as f:
        json.dump(eval_dataset, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 生成评估数据集: evaluation/open_dataset.json")
    print(f"   - RAG 测试: {len(eval_dataset['rag_tests'])} 条")
    print(f"   - Agent 测试: {len(eval_dataset['agent_tests'])} 条")
    print(f"\n📌 数据来源:")
    print(f"   - CMRC2018: 哈工大中文机器阅读理解数据集")
    print(f"   - DuReader: 百度中文阅读理解数据集")
