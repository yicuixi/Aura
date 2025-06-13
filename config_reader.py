"""
配置文件读取器 - 统一处理 .env 和 .conf 配置文件
"""

import os
import configparser
from dotenv import load_dotenv
from typing import Dict, Any

class ConfigManager:
    """配置管理器，统一处理多种格式的配置文件"""
    
    def __init__(self, config_dir="config", env_file=".env"):
        """初始化配置管理器"""
        self.config_dir = config_dir
        self.env_file = env_file
        self.config = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """加载所有配置文件"""
        # 1. 加载 .env 文件
        self._load_env_config()
        
        # 2. 加载 .conf 文件（优先级更高）
        self._load_conf_config()
        
        # 3. 设置默认值
        self._set_defaults()
    
    def _load_env_config(self):
        """加载 .env 配置文件"""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            print(f"✅ 已加载 {self.env_file}")
            
            # 从环境变量中读取配置
            self.config.update({
                'ollama_base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11435'),
                'ollama_model': os.getenv('OLLAMA_MODEL', 'qwen3:4b'),
                'flask_host': os.getenv('FLASK_HOST', '0.0.0.0'),
                'flask_port': int(os.getenv('FLASK_PORT', 5000)),
                'flask_debug': os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
                'searxng_url': os.getenv('SEARXNG_URL', 'http://localhost:8088'),
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'log_file': os.getenv('LOG_FILE', 'aura.log'),
            })
    
    def _load_conf_config(self):
        """加载 .conf 配置文件（优先级更高）"""
        conf_file = os.path.join(self.config_dir, "aura.conf")
        if os.path.exists(conf_file):
            parser = configparser.ConfigParser()
            parser.read(conf_file, encoding='utf-8')
            print(f"✅ 已加载 {conf_file}")
            
            # 模型配置
            if parser.has_section('model'):
                model_section = parser['model']
                self.config.update({
                    'ollama_model': model_section.get('name', self.config.get('ollama_model', 'qwen3:4b')),
                    'ollama_base_url': model_section.get('base_url', self.config.get('ollama_base_url', 'http://localhost:11435')),
                    'temperature': float(model_section.get('temperature', '0.7')),
                    'max_tokens': int(model_section.get('max_tokens', '2048')),
                })
            
            # Agent配置
            if parser.has_section('agent'):
                agent_section = parser['agent']
                self.config.update({
                    'agent_verbose': agent_section.getboolean('verbose', False),
                    'max_iterations': int(agent_section.get('max_iterations', '3')),
                    'early_stopping': agent_section.get('early_stopping', 'generate'),
                    'handle_parsing_errors': agent_section.getboolean('handle_parsing_errors', True),
                })
            
            # 记忆配置
            if parser.has_section('memory'):
                memory_section = parser['memory']
                self.config.update({
                    'memory_persist_directory': memory_section.get('persist_directory', 'db/memory'),
                    'conversation_history_limit': int(memory_section.get('conversation_history_limit', '50')),
                    'auto_save_interval': int(memory_section.get('auto_save_interval', '10')),
                })
            
            # RAG配置
            if parser.has_section('rag'):
                rag_section = parser['rag']
                self.config.update({
                    'rag_persist_directory': rag_section.get('persist_directory', 'db'),
                    'chunk_size': int(rag_section.get('chunk_size', '500')),
                    'chunk_overlap': int(rag_section.get('chunk_overlap', '50')),
                    'retrieval_k': int(rag_section.get('retrieval_k', '5')),
                })
            
            # 搜索配置
            if parser.has_section('search'):
                search_section = parser['search']
                self.config.update({
                    'searxng_url': search_section.get('searxng_url', self.config.get('searxng_url', 'http://localhost:8088')),
                    'search_timeout': int(search_section.get('timeout', '15')),
                    'max_results': int(search_section.get('max_results', '5')),
                })
            
            # 个性配置
            if parser.has_section('personality'):
                personality_section = parser['personality']
                self.config.update({
                    'enthusiasm': float(personality_section.get('enthusiasm', '0.7')),
                    'formality': float(personality_section.get('formality', '0.6')),
                    'empathy': float(personality_section.get('empathy', '0.8')),
                    'helpfulness': float(personality_section.get('helpfulness', '0.9')),
                })
    
    def _set_defaults(self):
        """设置默认配置值"""
        defaults = {
            'ollama_model': 'qwen3:4b',
            'ollama_base_url': 'http://localhost:11435',
            'temperature': 0.7,
            'max_tokens': 2048,
            'agent_verbose': False,
            'max_iterations': 3,
            'early_stopping': 'generate',
            'handle_parsing_errors': True,
            'memory_persist_directory': 'db/memory',
            'conversation_history_limit': 50,
            'auto_save_interval': 10,
            'rag_persist_directory': 'db',
            'chunk_size': 500,
            'chunk_overlap': 50,
            'retrieval_k': 5,
            'searxng_url': 'http://localhost:8088',
            'search_timeout': 15,
            'max_results': 5,
            'log_level': 'INFO',
            'log_file': 'aura.log',
            'flask_host': '0.0.0.0',
            'flask_port': 5000,
            'flask_debug': False,
            'enthusiasm': 0.7,
            'formality': 0.6,
            'empathy': 0.8,
            'helpfulness': 0.9,
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()
    
    def print_config(self):
        """打印当前配置（用于调试）"""
        print("=" * 50)
        print("🔧 当前配置:")
        print("=" * 50)
        for key, value in sorted(self.config.items()):
            print(f"  {key}: {value}")
        print("=" * 50)

# 创建全局配置管理器实例
config_manager = ConfigManager()

def get_config():
    """获取配置管理器实例"""
    return config_manager