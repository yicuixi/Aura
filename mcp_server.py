#!/usr/bin/env python3
"""
Aura MCP Server - 私有知识库检索服务
支持 Cursor / Claude Desktop 通过 MCP 协议调用

功能：
- search_knowledge: 语义搜索私有文档（论文、笔记等）
- list_documents: 列出知识库中的文档
- get_document_info: 获取文档元信息

使用方式：
1. stdio 模式（推荐，Cursor/Claude Desktop 默认）:
   python mcp_server.py

2. 测试模式：
   python mcp_server.py --test "搜索关键词"
"""

import sys
import json
import os
import logging
from typing import Any

# 设置日志（写入文件，不干扰 stdio）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='mcp_server.log'
)
logger = logging.getLogger("AuraMCP")

# RAG 系统配置
RAG_DB_PATH = "db2"

def get_rag_system():
    """获取 RAG 系统（每次重新连接，确保使用最新数据）"""
    # 抑制所有警告和打印输出（MCP stdio 模式下必须保持 stdout 干净）
    import warnings
    warnings.filterwarnings("ignore")
    
    # 同时重定向 stdout 和 stderr，避免任何输出干扰 JSON-RPC
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    
    try:
        from rag import RAGSystem
        rag_system = RAGSystem(persist_directory=RAG_DB_PATH)
    finally:
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    return rag_system


# ============== MCP 工具函数 ==============

def search_knowledge(query: str, top_k: int = 5) -> dict:
    """
    语义搜索私有知识库
    
    Args:
        query: 搜索关键词或问题
        top_k: 返回结果数量
    
    Returns:
        匹配的文档片段列表
    """
    try:
        rag = get_rag_system()
        results = rag.search(query, k=top_k)
        
        matches = []
        for i, doc in enumerate(results):
            matches.append({
                "rank": i + 1,
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
            })
        
        return {
            "query": query,
            "total_matches": len(matches),
            "matches": matches
        }
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return {"error": str(e)}


def list_documents() -> dict:
    """
    列出知识库中已索引的文档
    """
    try:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        if not os.path.exists(data_dir):
            return {"documents": [], "total": 0}
        
        docs = []
        for fname in os.listdir(data_dir):
            fpath = os.path.join(data_dir, fname)
            if os.path.isfile(fpath):
                stat = os.stat(fpath)
                docs.append({
                    "name": fname,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "type": os.path.splitext(fname)[1]
                })
        
        return {"documents": docs, "total": len(docs)}
    except Exception as e:
        logger.error(f"列出文档失败: {e}")
        return {"error": str(e)}


def get_document_info(filename: str) -> dict:
    """
    获取指定文档的详细信息
    
    Args:
        filename: 文档文件名
    """
    try:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        fpath = os.path.join(data_dir, filename)
        
        if not os.path.exists(fpath):
            return {"error": f"文档不存在: {filename}"}
        
        stat = os.stat(fpath)
        
        # 尝试获取文档预览
        preview = ""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in [".txt", ".md"]:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                preview = f.read(500)
        elif ext == ".docx":
            try:
                import docx
                doc = docx.Document(fpath)
                preview = "\n".join([p.text for p in doc.paragraphs[:5]])[:500]
            except:
                preview = "[无法预览 docx 文件]"
        
        return {
            "filename": filename,
            "size_kb": round(stat.st_size / 1024, 2),
            "type": ext,
            "preview": preview + "..." if len(preview) >= 500 else preview
        }
    except Exception as e:
        logger.error(f"获取文档信息失败: {e}")
        return {"error": str(e)}


# ============== MCP 协议处理 ==============

# MCP 工具定义
MCP_TOOLS = {
    "search_knowledge": {
        "description": "语义搜索私有知识库（论文、文档、笔记等）。当用户询问关于他们的文档、论文内容时使用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词或问题"
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回结果数量，默认5",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    "list_documents": {
        "description": "列出知识库中已索引的所有文档",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    "get_document_info": {
        "description": "获取指定文档的详细信息和预览",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "文档文件名"
                }
            },
            "required": ["filename"]
        }
    }
}


def handle_request(request: dict) -> dict:
    """处理 MCP JSON-RPC 请求"""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")
    
    logger.info(f"收到请求: method={method}, params={params}")
    
    try:
        # MCP 协议方法
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "aura-knowledge-base",
                    "version": "1.0.0"
                }
            }
        
        elif method == "notifications/initialized":
            # 客户端初始化完成通知，无需响应
            return None
        
        elif method == "tools/list":
            tools = []
            for name, spec in MCP_TOOLS.items():
                tools.append({
                    "name": name,
                    "description": spec["description"],
                    "inputSchema": spec["inputSchema"]
                })
            result = {"tools": tools}
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "search_knowledge":
                tool_result = search_knowledge(
                    query=tool_args.get("query", ""),
                    top_k=tool_args.get("top_k", 5)
                )
            elif tool_name == "list_documents":
                tool_result = list_documents()
            elif tool_name == "get_document_info":
                tool_result = get_document_info(
                    filename=tool_args.get("filename", "")
                )
            else:
                tool_result = {"error": f"未知工具: {tool_name}"}
            
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(tool_result, ensure_ascii=False, indent=2)
                    }
                ]
            }
        
        else:
            result = {"error": f"未知方法: {method}"}
        
        if result is not None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }
        return None
        
    except Exception as e:
        logger.error(f"处理请求失败: {e}")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


def run_stdio():
    """通过 stdio 运行 MCP Server（Cursor/Claude Desktop 使用）"""
    logger.info("MCP Server 启动 (stdio 模式)")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            request = json.loads(line)
            response = handle_request(request)
            
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误: {e}")
        except Exception as e:
            logger.error(f"处理错误: {e}")


def test_search(query: str):
    """测试搜索功能"""
    print(f"测试搜索: {query}")
    print("-" * 50)
    result = search_knowledge(query, top_k=3)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Aura MCP Server")
    parser.add_argument("--test", type=str, help="测试搜索功能")
    args = parser.parse_args()
    
    if args.test:
        test_search(args.test)
    else:
        run_stdio()

