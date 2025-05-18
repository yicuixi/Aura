import json
import os
from datetime import datetime
from typing import Dict, List, Any

class LongTermMemory:
    def __init__(self, memory_file="memory.json"):
        self.memory_file = memory_file
        self.memories = self._load_memories()
    
    def _load_memories(self) -> Dict[str, Any]:
        """从文件加载记忆"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"conversations": [], "facts": {}, "preferences": {}}
        else:
            return {"conversations": [], "facts": {}, "preferences": {}}
    
    def _save_memories(self):
        """保存记忆到文件"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)
    
    def add_conversation(self, user_input: str, ai_response: str):
        """添加对话记录"""
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "ai_response": ai_response
        }
        self.memories["conversations"].append(conversation)
        self._save_memories()
    
    def add_fact(self, category: str, key: str, value: Any):
        """添加事实性知识"""
        if category not in self.memories["facts"]:
            self.memories["facts"][category] = {}
            
        self.memories["facts"][category][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._save_memories()
    
    def get_fact(self, category: str, key: str) -> Any:
        """获取事实性知识"""
        if category in self.memories["facts"] and key in self.memories["facts"][category]:
            return self.memories["facts"][category][key]["value"]
        return None
    
    def set_preference(self, key: str, value: Any):
        """设置用户偏好"""
        self.memories["preferences"][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._save_memories()
    
    def get_preference(self, key: str) -> Any:
        """获取用户偏好"""
        if key in self.memories["preferences"]:
            return self.memories["preferences"][key]["value"]
        return None
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的对话"""
        return self.memories["conversations"][-limit:]

# 使用示例
if __name__ == "__main__":
    memory = LongTermMemory()
    
    # 添加对话
    memory.add_conversation("你好，Aura", "你好！我是Aura，有什么可以帮助你的？")
    
    # 添加事实
    memory.add_fact("user", "name", "Lydia")
    memory.add_fact("user", "research", "OAM相位重建+少样本识别")
    
    # 设置偏好
    memory.set_preference("reply_style", "友好")
    
    # 获取信息
    print(memory.get_fact("user", "name"))
    print(memory.get_preference("reply_style"))
