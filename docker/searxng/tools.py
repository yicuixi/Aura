import os
import requests
from typing import List, Dict, Any

def search_web(query: str) -> str:
    try:
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
        print(f"请求URL: {search_url}")
        print(f"请求参数: {params}")
        
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        
        # 打印响应状态
        print(f"状态码: {response.status_code}")
        
        if response.status_code != 200:
            return f"搜索请求失败，状态码: {response.status_code}, 响应: {response.text[:200]}"
            
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
        
        return formatted_results
    except Exception as e:
        return f"搜索出错: {str(e)}"

# 同名函数别名以兼容原来的代码
search_searxng = search_web

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

# 兼容原来的函数定义，保持向后兼容性
def write_file_old(file_path: str, content: str) -> str:
    """
    写入文件内容（旧版方法）
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
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
