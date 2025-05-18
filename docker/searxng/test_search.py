import sys
import os
import requests

# 直接使用当前目录的tools.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import tools

# 直接实现搜索函数，确保我们的测试不依赖于导入
def direct_search_test(query):
    """直接测试SearXNG搜索，绕过tools模块"""
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
        
        print(f"正在访问: {search_url}")
        print(f"使用参数: {params}")
        print(f"使用头信息: {headers}")
        
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        
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

# 测试搜索功能
def test_search():
    print("测试SearXNG搜索功能...")
    query = "PyTorch 教程"
    print(f"搜索查询: '{query}'")
    print("=" * 50)
    
    # 直接测试SearXNG，使用我们自定义的函数
    print("直接测试SearXNG API:")
    result = direct_search_test(query)
    print(result)
    
    print("=" * 50)
    print("测试本地tools模块:")
    try:
        if hasattr(tools, 'search_web'):
            result = tools.search_web(query)
            print(result)
        else:
            print("tools模块中没有search_web函数")
            if hasattr(tools, 'search_searxng'):
                result = tools.search_searxng(query)
                print(result)
            else:
                print("tools模块中也没有search_searxng函数")
                print("可用的函数有:", [f for f in dir(tools) if callable(getattr(tools, f)) and not f.startswith('_')])
    except Exception as e:
        print(f"工具测试失败: {e}")
    
    print("=" * 50)
    
    # 提示用户输入自定义查询
    print("请输入您的搜索查询(留空退出):")
    
    while True:
        user_query = input("> ")
        if not user_query:
            break
            
        print("=" * 50)
        result = tools.search_web(user_query)
        print(result)
        print("=" * 50)
        print("请输入新的搜索查询(留空退出):")

if __name__ == "__main__":
    test_search()
