"""
Aura AI - 工具集
网络搜索、文件读写（沙箱保护）、目录列表
"""
import os
import requests
from typing import List
import json
import logging

logger = logging.getLogger("AuraTools")

# ---------------------------------------------------------------------------
# 文件操作沙箱
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

FILE_SANDBOX_DIRS = [
    os.path.join(_PROJECT_ROOT, "data"),
    os.path.join(_PROJECT_ROOT, "logs"),
]


def _safe_resolve(file_path: str) -> str:
    """将用户传入路径规范化，并校验是否在沙箱目录内"""
    normalized = os.path.normpath(os.path.abspath(file_path))
    for allowed in FILE_SANDBOX_DIRS:
        if normalized.startswith(os.path.normpath(os.path.abspath(allowed))):
            return normalized
    raise PermissionError(
        f"访问被拒绝: 路径 {file_path} 不在允许范围（{FILE_SANDBOX_DIRS}）"
    )


# ---------------------------------------------------------------------------
# 网络搜索
# ---------------------------------------------------------------------------

def search_web(query: str) -> str:
    """增强版网络搜索工具，支持多种搜索方式"""
    methods = [
        search_searxng,
        search_serper,
    ]

    errors = []
    for method in methods:
        try:
            result = method(query)
            if "搜索结果:" in result and "没有找到搜索结果" not in result:
                return result
            errors.append(result)
        except Exception as e:
            errors.append(f"{method.__name__} 错误: {str(e)}")

    if errors and "搜索结果:" in errors[0]:
        return errors[0]

    return f"搜索方法失败:\n" + "\n".join(errors)


def search_searxng(query: str) -> str:
    """使用本地 SearxNG 搜索"""
    try:
        search_url = "http://localhost:8088/search"
        headers = {
            "User-Agent": "Aura-AI/2.0",
            "Accept": "application/json",
        }
        params = {
            "q": query,
            "format": "json",
            "language": "zh",
            "time_range": "",
            "safesearch": "0",
        }

        response = requests.get(
            search_url, params=params, headers=headers, timeout=15
        )

        if response.status_code != 200:
            return f"搜索请求失败，状态码: {response.status_code}"

        results = response.json()
        formatted_results = "搜索结果:\n\n"

        if not results.get("results", []):
            return "没有找到搜索结果。"

        for i, result in enumerate(results.get("results", [])[:5], 1):
            title = result.get("title", "无标题")
            url = result.get("url", "")
            content = result.get("content", "")
            formatted_results += f"{i}. {title}\n   链接: {url}\n   {content}\n\n"

        return formatted_results
    except Exception as e:
        return f"SearxNG搜索出错: {str(e)}"


def search_serper(query: str) -> str:
    """使用 Serper.dev API 搜索"""
    api_key = os.environ.get("SERPER_API_KEY", "")
    if not api_key:
        return "错误: 未设置Serper API密钥。请设置环境变量SERPER_API_KEY。"

    try:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "gl": "cn", "hl": "zh-cn"})
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, data=payload, timeout=10)
        if response.status_code != 200:
            return f"Serper请求失败，状态码: {response.status_code}"

        results = response.json()
        formatted_results = "搜索结果:\n\n"
        organic = results.get("organic", [])
        if not organic:
            return "没有找到搜索结果。"

        for i, result in enumerate(organic[:5], 1):
            title = result.get("title", "无标题")
            link = result.get("link", "")
            snippet = result.get("snippet", "")
            formatted_results += f"{i}. {title}\n   链接: {link}\n   {snippet}\n\n"

        return formatted_results
    except Exception as e:
        return f"Serper搜索出错: {str(e)}"


# ---------------------------------------------------------------------------
# 文件操作（沙箱保护）
# ---------------------------------------------------------------------------

def read_file(file_path: str) -> str:
    """读取文件内容（限制在 data/logs 目录）"""
    try:
        safe_path = _safe_resolve(file_path)
        if not os.path.exists(safe_path):
            return f"文件不存在: {file_path}"

        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except PermissionError as e:
        logger.warning("文件读取被拒绝: %s", e)
        return f"权限不足: {e}"
    except Exception as e:
        return f"读取文件出错: {str(e)}"


def read_file_lines(file_input: str) -> str:
    """读取文件的前 N 行，格式: 文件路径::行数"""
    try:
        if "::" in file_input:
            file_path, lines_str = file_input.split("::", 1)
            try:
                num_lines = int(lines_str)
            except ValueError:
                return f"行数格式错误: {lines_str}，请输入数字"
        else:
            file_path = file_input
            num_lines = 10

        safe_path = _safe_resolve(file_path)
        if not os.path.exists(safe_path):
            return f"文件不存在: {file_path}"

        lines = []
        with open(safe_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= num_lines:
                    break
                lines.append(f"{i+1}: {line.rstrip()}")

        result = f"文件 {file_path} 的前 {len(lines)} 行:\n\n"
        result += "\n".join(lines)
        return result
    except PermissionError as e:
        return f"权限不足: {e}"
    except Exception as e:
        return f"读取文件出错: {str(e)}"


def write_file(file_input: str) -> str:
    """写入文件内容（限制在 data/logs 目录），格式: 文件路径::文件内容"""
    try:
        if "::" not in file_input:
            return "格式错误，请使用: 文件路径::文件内容"

        file_path, content = file_input.split("::", 1)
        safe_path = _safe_resolve(file_path)

        directory = os.path.dirname(safe_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"内容已成功写入: {safe_path}"
    except PermissionError as e:
        logger.warning("文件写入被拒绝: %s", e)
        return f"权限不足: {e}"
    except Exception as e:
        return f"写入文件出错: {str(e)}"


def list_directory(directory_path: str) -> List[str]:
    """列出目录内容（限制在沙箱目录）"""
    try:
        safe_path = _safe_resolve(directory_path)
        if not os.path.exists(safe_path):
            return [f"目录不存在: {directory_path}"]
        return os.listdir(safe_path)
    except PermissionError as e:
        return [f"权限不足: {e}"]
    except Exception as e:
        return [f"列出目录出错: {str(e)}"]
