"""
Aura AI - 长期记忆模块
支持可选加密存储：设置 AURA_MASTER_KEY 环境变量后自动启用
兼容旧版明文 memory.json（首次加载后自动迁移为加密格式）
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger("AuraMemory")

ENCRYPTED_MARKER = "AURA_ENC:"

_encrypt_available = False
try:
    from security import encrypt_text, decrypt_text
    _encrypt_available = True
except ImportError:
    pass


def _should_encrypt() -> bool:
    return _encrypt_available and bool(os.environ.get("AURA_MASTER_KEY"))


class LongTermMemory:
    def __init__(self, memory_file="memory.json"):
        self.memory_file = memory_file
        self.memories = self._load_memories()

    # ------------------------------------------------------------------
    # 持久化（加密/明文自适应）
    # ------------------------------------------------------------------
    def _load_memories(self) -> Dict[str, Any]:
        """从文件加载记忆，自动识别加密 / 明文格式"""
        default = {"conversations": [], "facts": {}, "preferences": {}}

        if not os.path.exists(self.memory_file):
            return default

        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                raw = f.read()
        except Exception:
            logger.warning("读取记忆文件失败，使用空记忆")
            return default

        if not raw.strip():
            return default

        if raw.startswith(ENCRYPTED_MARKER):
            if not _encrypt_available:
                logger.error("记忆已加密但 security 模块不可用，无法解密")
                return default
            try:
                decrypted = decrypt_text(raw[len(ENCRYPTED_MARKER):])
                data = json.loads(decrypted)
                logger.info("已加载加密记忆")
                return data
            except Exception as e:
                logger.error("解密记忆失败（密钥可能已变更）: %s", e)
                return default

        try:
            data = json.loads(raw)
            if _should_encrypt():
                logger.info("检测到明文记忆，将自动迁移为加密格式")
                self.memories = data
                self._save_memories()
            return data
        except json.JSONDecodeError:
            logger.warning("记忆文件格式错误，使用空记忆")
            return default

    def _save_memories(self):
        """保存记忆到文件"""
        payload = json.dumps(self.memories, ensure_ascii=False, indent=2)

        if _should_encrypt():
            try:
                encrypted = encrypt_text(payload)
                with open(self.memory_file, "w", encoding="utf-8") as f:
                    f.write(ENCRYPTED_MARKER + encrypted)
                return
            except Exception as e:
                logger.error("加密保存失败，回退为明文: %s", e)

        with open(self.memory_file, "w", encoding="utf-8") as f:
            f.write(payload)

    # ------------------------------------------------------------------
    # 对话记录
    # ------------------------------------------------------------------
    def add_conversation(self, user_input: str, ai_response: str):
        """添加对话记录"""
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "ai_response": ai_response,
        }
        self.memories["conversations"].append(conversation)

        max_conversations = 500
        if len(self.memories["conversations"]) > max_conversations:
            self.memories["conversations"] = self.memories["conversations"][
                -max_conversations:
            ]

        self._save_memories()

    # ------------------------------------------------------------------
    # 事实 / 偏好
    # ------------------------------------------------------------------
    def add_fact(self, category: str, key: str, value: Any):
        """添加事实性知识"""
        if category not in self.memories["facts"]:
            self.memories["facts"][category] = {}

        self.memories["facts"][category][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_memories()

    def get_fact(self, category: str, key: str) -> Any:
        """获取事实性知识"""
        cat = self.memories["facts"].get(category, {})
        entry = cat.get(key)
        if entry:
            return entry["value"]
        return None

    def set_preference(self, key: str, value: Any):
        """设置用户偏好"""
        self.memories["preferences"][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_memories()

    def get_preference(self, key: str) -> Any:
        """获取用户偏好"""
        entry = self.memories["preferences"].get(key)
        if entry:
            return entry["value"]
        return None

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的对话"""
        return self.memories["conversations"][-limit:]

    def clear_conversations(self):
        """清除所有对话记录（隐私操作）"""
        self.memories["conversations"] = []
        self._save_memories()
        logger.info("对话记录已清除")


if __name__ == "__main__":
    memory = LongTermMemory()
    memory.add_conversation("你好，Aura", "你好！我是Aura，有什么可以帮助你的？")
    memory.add_fact("user", "name", "Lydia")
    memory.set_preference("reply_style", "友好")
    print(memory.get_fact("user", "name"))
    print(memory.get_preference("reply_style"))
