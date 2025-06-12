"""
Aura AI Web API服务
提供HTTP API接口，兼容OpenAI格式
"""

import os
import time
import logging
from flask import Flask, request, jsonify
from aura import AuraAgentFixed

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化Aura Agent
try:
    aura = AuraAgentFixed(model_name="qwen3:4b", verbose=False)
    logger.info("Aura Agent初始化成功")
except Exception as e:
    logger.error(f"Aura Agent初始化失败: {e}")
    aura = None

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    if aura is None:
        return jsonify({
            "status": "unhealthy",
            "error": "Aura Agent not initialized"
        }), 503
    
    return jsonify({
        "status": "healthy",
        "service": "Aura AI API",
        "timestamp": time.time()
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI兼容的聊天完成API"""
    try:
        if aura is None:
            return jsonify({
                "error": {
                    "message": "Aura Agent not available",
                    "type": "service_unavailable"
                }
            }), 503
        
        data = request.json
        if not data or 'messages' not in data:
            return jsonify({
                "error": {
                    "message": "Invalid request format",
                    "type": "invalid_request"
                }
            }), 400
        
        messages = data.get('messages', [])
        
        # 提取最后一条用户消息
        user_message = None
        for message in reversed(messages):
            if message.get('role') == 'user':
                user_message = message.get('content', '')
                break
        
        if not user_message:
            return jsonify({
                "error": {
                    "message": "No user message found",
                    "type": "invalid_request"
                }
            }), 400
        
        # 使用Aura处理查询
        logger.info(f"处理用户查询: {user_message}")
        response = aura.process_query(user_message)
        
        return jsonify({
            "id": f"aura-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "aura",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(response.split()),
                "total_tokens": len(user_message.split()) + len(response.split())
            }
        })
        
    except Exception as e:
        logger.error(f"API处理错误: {e}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_error"
            }
        }), 500

@app.route('/api/knowledge/load', methods=['POST'])
def load_knowledge():
    """加载知识库API"""
    try:
        if aura is None:
            return jsonify({
                "error": "Aura Agent not available"
            }), 503
        
        data = request.json
        extension = data.get('extension', '.md')
        
        result = aura.load_knowledge(extension)
        
        return jsonify({
            "result": result,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"加载知识库错误: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/api/memory/add', methods=['POST'])
def add_memory():
    """添加记忆API"""
    try:
        if aura is None:
            return jsonify({
                "error": "Aura Agent not available"
            }), 503
        
        data = request.json
        category = data.get('category')
        key = data.get('key')
        value = data.get('value')
        
        if not all([category, key, value]):
            return jsonify({
                "error": "Missing required fields: category, key, value"
            }), 400
        
        fact_str = f"{category}/{key}/{value}"
        result = aura.remember_fact(fact_str)
        
        return jsonify({
            "result": result,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"添加记忆错误: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/api/memory/get', methods=['GET'])
def get_memory():
    """获取记忆API"""
    try:
        if aura is None:
            return jsonify({
                "error": "Aura Agent not available"
            }), 503
        
        category = request.args.get('category')
        key = request.args.get('key')
        
        if not all([category, key]):
            return jsonify({
                "error": "Missing required parameters: category, key"
            }), 400
        
        fact_str = f"{category}/{key}"
        result = aura.recall_fact(fact_str)
        
        return jsonify({
            "result": result,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"获取记忆错误: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": {
            "message": "Endpoint not found",
            "type": "not_found"
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": {
            "message": "Internal server error",
            "type": "internal_error"
        }
    }), 500

if __name__ == '__main__':
    print("🚀 启动Aura AI API服务...")
    print("📡 API端点:")
    print("  - GET  /health - 健康检查")
    print("  - POST /v1/chat/completions - OpenAI兼容聊天API")
    print("  - POST /api/knowledge/load - 加载知识库")
    print("  - POST /api/memory/add - 添加记忆")
    print("  - GET  /api/memory/get - 获取记忆")
    print("🌐 访问地址: http://0.0.0.0:5000")
    
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    app.run(host=host, port=port, debug=False)
