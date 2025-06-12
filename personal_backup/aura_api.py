# 补充aura_api.py中的缺失引用
import time
from flask import Flask, request, jsonify
from aura import AuraAgent

app = Flask(__name__)
aura = AuraAgent(model_name="qwen3:4b", verbose=False)

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    messages = data.get('messages', [])
    
    # 提取最后一条用户消息
    user_message = next((m['content'] for m in reversed(messages) 
                         if m['role'] == 'user'), "")
    
    # 使用Aura处理查询
    response = aura.process_query(user_message)
    
    return jsonify({
        "id": "aura-response",
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
        ]
    })

if __name__ == '__main__':
    print("启动Aura API服务...")
    app.run(host='0.0.0.0', port=5000)
