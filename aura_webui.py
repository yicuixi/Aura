"""
Aura OpenWebUI 集成脚本

这个脚本创建一个API服务器，将Aura的核心功能暴露给OpenWebUI。
它允许通过OpenWebUI使用Aura的RAG系统、记忆系统和工具调用。
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# 导入Aura核心组件
from rag import RAGSystem
from memory import LongTermMemory
import tools
from query_handlers.registry import factory as query_handler_factory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("aura_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Aura.API")

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化Aura组件
rag_system = RAGSystem(persist_directory="db")
memory = LongTermMemory()

# 添加仪表盘路由
@app.route('/', methods=['GET'])
def dashboard():
    """渲染Aura仪表盘"""
    return render_template('dashboard.html')

@app.route('/docs', methods=['GET'])
def docs():
    """Aura文档"""
    return render_template('docs.html')

@app.route('/api/system_status', methods=['GET'])
def system_status():
    """获取系统状态"""
    try:
        # 获取Ollama状态
        ollama_status = "running"
        try:
            import subprocess
            result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
            if "aura_new" in result.stdout:
                ollama_status = "running"
            else:
                ollama_status = "stopped"
        except Exception:
            ollama_status = "unknown"
            
        # 获取知识库状态
        doc_count = len(rag_system.get_documents())
        
        # 获取记忆状态
        memory_count = sum(len(facts) for category, facts in memory.memories.get("facts", {}).items())
        
        return jsonify({
            "status": "success",
            "ollama": ollama_status,
            "doc_count": doc_count,
            "memory_count": memory_count,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取系统状态错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search_knowledge', methods=['POST'])
def search_knowledge():
    """在知识库中搜索"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "查询不能为空"}), 400
    
    try:
        results = rag_system.search(query)
        return jsonify({
            "status": "success",
            "results": results
        })
    except Exception as e:
        logger.error(f"知识库搜索错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_memory', methods=['POST'])
def save_memory():
    """保存记忆"""
    data = request.json
    category = data.get('category', '')
    key = data.get('key', '')
    value = data.get('value', '')
    
    if not all([category, key, value]):
        return jsonify({"error": "category, key, 和 value 不能为空"}), 400
    
    try:
        memory.add_fact(category, key, value)
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"保存记忆错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/recall_memory', methods=['POST'])
def recall_memory():
    """回忆记忆"""
    data = request.json
    category = data.get('category', '')
    key = data.get('key', '')
    
    if not all([category, key]):
        return jsonify({"error": "category 和 key 不能为空"}), 400
    
    try:
        value = memory.get_fact(category, key)
        return jsonify({
            "status": "success",
            "value": value
        })
    except Exception as e:
        logger.error(f"回忆记忆错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search_web', methods=['POST'])
def search_web():
    """网络搜索"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "查询不能为空"}), 400
    
    try:
        results = tools.search_web(query)
        return jsonify({
            "status": "success",
            "results": results
        })
    except Exception as e:
        logger.error(f"网络搜索错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/read_file', methods=['POST'])
def read_file():
    """读取文件"""
    data = request.json
    file_path = data.get('path', '')
    
    if not file_path:
        return jsonify({"error": "文件路径不能为空"}), 400
    
    try:
        content = tools.read_file(file_path)
        return jsonify({
            "status": "success",
            "content": content
        })
    except Exception as e:
        logger.error(f"读取文件错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/write_file', methods=['POST'])
def write_file():
    """写入文件"""
    data = request.json
    file_path = data.get('path', '')
    content = data.get('content', '')
    
    if not file_path or not content:
        return jsonify({"error": "文件路径和内容不能为空"}), 400
    
    try:
        result = tools.write_file(f"{file_path}::{content}")
        return jsonify({
            "status": "success",
            "result": result
        })
    except Exception as e:
        logger.error(f"写入文件错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/add_document', methods=['POST'])
def add_document():
    """添加文档到知识库"""
    if 'file' not in request.files:
        return jsonify({"error": "没有文件部分"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
        
    try:
        # 保存到临时位置
        temp_path = os.path.join('data', file.filename)
        file.save(temp_path)
        
        # 添加到知识库
        docs = rag_system.load_documents([temp_path])
        rag_system.add_documents(docs)
        
        return jsonify({
            "status": "success",
            "message": f"文档 {file.filename} 已添加到知识库"
        })
    except Exception as e:
        logger.error(f"添加文档错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Aura API服务器')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='主机地址')
    parser.add_argument('--port', type=int, default=5000, help='端口号')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    logger.info(f"启动Aura API服务器在 {args.host}:{args.port}")
    
    # 启动Flask服务器
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
