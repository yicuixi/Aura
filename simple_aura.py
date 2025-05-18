import os
import json
from datetime import datetime
import requests

"""
Aura AI - 轻量级版本
直接调用Ollama API，不使用LangChain框架
"""

# 简单的记忆系统
class Memory:
    def __init__(self, file_path="memory.json"):
        self.file_path = file_path
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"conversations": [], "facts": {}}
        return {"conversations": [], "facts": {}}
    
    def save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_conversation(self, user_input, response):
        self.data["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": response
        })
        self.save()
    
    def add_fact(self, key, value):
        self.data["facts"][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self.save()
    
    def get_fact(self, key):
        return self.data["facts"].get(key, {}).get("value")
    
    def get_recent_conversations(self, limit=5):
        return self.data["conversations"][-limit:]

# Ollama API 客户端
class OllamaClient:
    def __init__(self, base_url="http://localhost:11435", model="qwen2"):
        self.base_url = base_url
        self.model = model
    
    def generate(self, prompt, system=""):
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False
                }
            )
            return response.json()["response"]
        except Exception as e:
            return f"生成失败: {str(e)}"

# 主程序
def main():
    print("✨ 正在初始化Aura...")
    
    # 初始化组件
    memory = Memory()
    ollama = OllamaClient(model="qwen2")  # 或 qwen2.5:7b
    
    # 系统提示
    system_prompt = """你是Aura，一个智能助手。你应该友好、乐于助人、诚实。
    你是Lydia的个人助手，她是一名光学研二硕士生，研究方向是OAM相位重建+少样本识别。
    她正在准备英伟达的Deep Learning Software Test Engineer Intern职位的面试。
    """
    
    print("✨ Aura已启动，等待指令...")
    
    while True:
        user_input = input("\n👤 输入: ")
        if user_input.lower() in ["exit", "quit", "退出"]:
            print("👋 Aura正在关闭...")
            break
        
        # 获取最近对话
        recent = memory.get_recent_conversations()
        conversation_context = "\\n".join([
            f"用户: {conv['user']}\\n助手: {conv['assistant']}" 
            for conv in recent
        ])
        
        # 构建完整提示
        full_prompt = f"{conversation_context}\\n用户: {user_input}\\n助手:"
        
        # 生成回复
        response = ollama.generate(full_prompt, system_prompt)
        print(f"\n🤖 Aura: {response}")
        
        # 记忆对话
        memory.add_conversation(user_input, response)

if __name__ == "__main__":
    main()
