import os
import requests
from typing import List, Dict, Any
import json
import random
import time

def search_web(query: str) -> str:
    """
    增强版网络搜索工具，支持多种搜索方式
    """
    # 尝试不同的搜索方法，按优先级排序
    methods = [
        search_searxng,        # 本地SearxNG (首选)
        # search_serpapi_duckduckgo,  # SerpAPI DuckDuckGo (需要API密钥，已禁用)
        search_serper           # Serper API (备选，需要API密钥)
    ]
    
    # 尝试每种方法，直到成功
    errors = []
    for method in methods:
        try:
            result = method(query)
            
            # 修改判断条件: 只要结果包含搜索结果，就认为成功
            if "搜索结果:" in result and "没有找到搜索结果" not in result:
                return result  # 直接返回成功的结果
            
            # 如果有错误，添加到错误列表
            errors.append(result)
        except Exception as e:
            errors.append(f"{method.__name__} 错误: {str(e)}")
    
    # 所有方法都失败，返回错误信息
    # 如果第一个方法返回了结果，即使有错误信息，也优先返回第一个方法的结果
    if errors and "搜索结果:" in errors[0]:
        return errors[0]
    
    return f"搜索方法失败:\n" + "\n".join(errors)

def search_searxng(query: str) -> str:
    """使用本地SearxNG搜索"""
    try:
        # 修改请求方式，添加headers
        search_url = "http://localhost:8088/search"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept": "application/json",
            "Referer": "http://localhost:8088/",
            "Origin": "http://localhost:8088"
        }
        params = {
            "q": query,
            "format": "json",
            "language": "zh",
            "time_range": "",
            "safesearch": "0"
        }
        
        # 打印调试信息
        print(f"SearxNG 搜索: {query}")
        
        response = requests.get(search_url, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"SearxNG 请求失败: 状态码 {response.status_code}")
            # 尝试获取错误信息
            error_text = response.text[:200] if response.text else "无错误信息"
            return f"搜索请求失败，状态码: {response.status_code}，错误: {error_text}"
            
        results = response.json()
        
        # 格式化返回结果
        formatted_results = "搜索结果:\n\n"
        
        if not results.get("results", []):
            return "没有找到搜索结果。"
        
        # 只取前5个结果
        for i, result in enumerate(results.get("results", [])[:5], 1):
            title = result.get("title", "无标题")
            url = result.get("url", "")
            content = result.get("content", "")
            
            formatted_results += f"{i}. {title}\n"
            formatted_results += f"   链接: {url}\n"
            formatted_results += f"   {content}\n\n"
        
        print(f"SearxNG 搜索成功: 找到 {len(results.get('results', []))} 条结果")
        return formatted_results
    except Exception as e:
        print(f"SearxNG 搜索出错: {str(e)}")
        return f"SearxNG搜索出错: {str(e)}"

def search_serpapi_duckduckgo(query: str) -> str:
    """使用SerpAPI的DuckDuckGo搜索"""
    try:
        # 获取API密钥 - 从环境变量或本地配置文件获取
        api_key = os.environ.get("SERPAPI_KEY", "")
        
        # 如果没有设置API密钥，通知用户
        if not api_key:
            return "错误: 未设置SerpAPI API密钥。请设置环境变量SERPAPI_KEY或使用其他搜索方法。"
            
        search_url = "https://serpapi.com/search.json"
        params = {
            "engine": "duckduckgo",
            "q": query,
            "kl": "cn-zh",  # 中文区域
            "api_key": api_key
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code != 200:
            return f"SerpAPI请求失败，状态码: {response.status_code}"
            
        results = response.json()
        
        # 格式化返回结果
        formatted_results = "搜索结果:\n\n"
        
        organic_results = results.get("organic_results", [])
        if not organic_results:
            return "没有找到搜索结果。"
        
        # 取前5个结果
        for i, result in enumerate(organic_results[:5], 1):
            title = result.get("title", "无标题")
            url = result.get("link", "")
            snippet = result.get("snippet", "")
            
            formatted_results += f"{i}. {title}\n"
            formatted_results += f"   链接: {url}\n"
            formatted_results += f"   {snippet}\n\n"
        
        return formatted_results
    except Exception as e:
        return f"SerpAPI搜索出错: {str(e)}"

def search_serper(query: str) -> str:
    """使用Serper.dev API搜索（需要API密钥）"""
    # 检查是否有API密钥
    api_key = os.environ.get("SERPER_API_KEY", "")
    if not api_key:
        return "错误: 未设置Serper API密钥。请设置环境变量SERPER_API_KEY。"
    
    try:
        url = "https://google.serper.dev/search"
        payload = json.dumps({
            "q": query,
            "gl": "cn",
            "hl": "zh-cn",
        })
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        
        if response.status_code != 200:
            return f"Serper请求失败，状态码: {response.status_code}"
            
        results = response.json()
        
        # 格式化返回结果
        formatted_results = "搜索结果:\n\n"
        
        organic = results.get("organic", [])
        if not organic:
            return "没有找到搜索结果。"
        
        # 取前5个结果
        for i, result in enumerate(organic[:5], 1):
            title = result.get("title", "无标题")
            url = result.get("link", "")
            snippet = result.get("snippet", "")
            
            formatted_results += f"{i}. {title}\n"
            formatted_results += f"   链接: {url}\n"
            formatted_results += f"   {snippet}\n\n"
        
        return formatted_results
    except Exception as e:
        return f"Serper搜索出错: {str(e)}"

def read_file(file_path: str) -> str:
    """
    读取文件内容
    """
    try:
        if not os.path.exists(file_path):
            return f"文件不存在: {file_path}"
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"读取文件出错: {str(e)}"

def read_file_lines(file_input: str) -> str:
    """
    读取文件的前N行内容，格式: 文件路径::行数
    例如: D:\\Code\\Aura\\aura.py::5
    如果不指定行数，默认读取前10行
    """
    try:
        # 解析输入参数
        if '::' in file_input:
            file_path, lines_str = file_input.split('::', 1)
            try:
                num_lines = int(lines_str)
            except ValueError:
                return f"行数格式错误: {lines_str}，请输入数字"
        else:
            file_path = file_input
            num_lines = 10  # 默认读取前10行
        
        if not os.path.exists(file_path):
            return f"文件不存在: {file_path}"
        
        lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= num_lines:
                    break
                lines.append(f"{i+1}: {line.rstrip()}")
        
        result = f"文件 {file_path} 的前 {len(lines)} 行:\n\n"
        result += "\n".join(lines)
        return result
        
    except Exception as e:
        return f"读取文件出错: {str(e)}"

def write_file(file_input: str) -> str:
    """
    写入文件内容，格式: 文件路径::文件内容
    """
    try:
        # 分离文件路径和内容
        if '::' not in file_input:
            return "格式错误，请使用: 文件路径::文件内容"
        
        file_path, content = file_input.split('::', 1)
        
        # 确保目录存在
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"内容已成功写入: {file_path}"
    except Exception as e:
        return f"写入文件出错: {str(e)}"

def list_directory(directory_path: str) -> List[str]:
    """
    列出目录内容
    """
    try:
        if not os.path.exists(directory_path):
            return [f"目录不存在: {directory_path}"]
            
        items = os.listdir(directory_path)
        return items
    except Exception as e:
        return [f"列出目录出错: {str(e)}"]
