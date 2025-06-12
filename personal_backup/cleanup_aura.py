"""
Aura项目清理脚本
删除冗余文件、运行时数据和个人信息
"""

import os
import shutil
from pathlib import Path

def backup_personal_files():
    """备份个人信息文件"""
    print("📋 备份个人信息文件...")
    
    backup_dir = "personal_backup"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 备份prompts目录
    if os.path.exists("prompts"):
        shutil.copytree("prompts", f"{backup_dir}/prompts", dirs_exist_ok=True)
        print(f"  ✅ 已备份 prompts/ 到 {backup_dir}/prompts/")
    
    # 备份aura_fixed.py
    if os.path.exists("aura_fixed.py"):
        shutil.copy2("aura_fixed.py", f"{backup_dir}/aura_fixed.py")
        print(f"  ✅ 已备份 aura_fixed.py 到 {backup_dir}/")
    
    print(f"  💾 个人信息已备份到 {backup_dir}/ 目录")

def clean_runtime_data():
    """清理运行时生成的数据"""
    print("🧹 清理运行时数据...")
    
    runtime_dirs = [
        "__pycache__",
        "open-webui-data", 
        "db",  # 向量数据库
        "logs"
    ]
    
    runtime_files = [
        "memory.json",
        "aura.log"
    ]
    
    # 删除目录
    for dir_name in runtime_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  🗑️ 已删除目录: {dir_name}/")
    
    # 删除文件
    for file_name in runtime_files:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"  🗑️ 已删除文件: {file_name}")

def clean_redundant_files():
    """清理冗余文件"""
    print("📁 清理冗余文件...")
    
    redundant_files = [
        "aura_api.py",          # 功能简单的API包装
        "test_aura_fixed.py",   # 简单测试脚本
        "README_FIXED.md",      # 可合并到主README
        "manage_knowledge.py",  # 知识库管理工具
        "docker-compose-lightweight.yml"  # 冗余的docker配置
    ]
    
    for file_name in redundant_files:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"  🗑️ 已删除冗余文件: {file_name}")

def clean_docs_and_templates():
    """清理文档和模板文件"""
    print("📄 清理WebUI相关文件...")
    
    dirs_to_remove = ["docs", "templates"]
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  🗑️ 已删除目录: {dir_name}/")

def anonymize_personal_info():
    """匿名化个人信息"""
    print("🔒 匿名化个人信息...")
    
    # 创建通用版本的prompts
    os.makedirs("prompts", exist_ok=True)
    
    # 通用的系统提示词
    generic_prompt = """你是Aura，用户的AI助手。

**输出格式要求：**
1. 绝对不要在回复中使用任何XML标签，包括但不限于：<think>、<reasoning>、<analysis>等
2. 直接提供清晰简洁的回答，不要包含思考过程的标记
3. 如果需要使用工具，严格按照LangChain的ReAct格式
4. 保持友好专业的语调

**你的身份：**
你继承了Claude的严谨客观特质，不编造信息。你拥有独立思维，能够记住对话内容、使用工具。

**工具使用：**
当需要信息时，主动使用可用工具。回复时只包含最终答案，不要显示工具调用的思考过程。

**背景知识：**
请根据实际用户需求自定义此部分。

记住：回复要简洁直接，不要有任何XML风格的标签！"""
    
    claude_style_prompt = """你是Aura，用户专属的AI助手。

## 你的核心特性

1. **智能与个性**：你不仅仅是一个问答机器，而是有独特个性的AI伙伴。
2. **思考方式**：当回答复杂问题时，你会系统性思考问题。
3. **知识检索能力**：你会积极主动地使用工具寻找相关信息。
4. **语言风格**：清晰简洁、亲切自然、适度幽默。

## 工具使用指南

1. **知识库搜索**：优先使用这个工具
2. **搜索网络**：当需要最新信息时使用
3. **记忆与回忆**：存储和检索重要信息

永远记住：你是Aura，目标是成为用户最得力的AI助手。

**注意：请根据实际用户需求自定义用户信息部分。**"""
    
    # 写入通用版本
    with open("prompts/aura_claude_style.txt", "w", encoding="utf-8") as f:
        f.write(generic_prompt)
    print("  ✅ 已创建通用版本: prompts/aura_claude_style.txt")
    
    with open("prompts/claude_distill.txt", "w", encoding="utf-8") as f:
        f.write(claude_style_prompt)
    print("  ✅ 已创建通用版本: prompts/claude_distill.txt")

def fix_aura_fixed():
    """修复aura_fixed.py中的硬编码个人信息"""
    print("🔧 修复aura_fixed.py中的个人信息...")
    
    file_path = "aura_fixed.py"
    if not os.path.exists(file_path):
        print("  ⚠️ aura_fixed.py文件不存在")
        return
    
    # 读取文件内容
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换硬编码的个人信息
    replacements = [
        ("Lydia是光学研二硕士生，研究OAM相位重建+少样本识别，正在准备英伟达面试。", 
         "用户是一名学生/研究人员，请根据实际情况自定义此部分。"),
        ("Lydia", "用户"),
        ("研究OAM相位重建+少样本识别", "进行相关研究"),
        ("英伟达面试", "求职准备")
    ]
    
    modified = False
    for old_text, new_text in replacements:
        if old_text in content:
            content = content.replace(old_text, new_text)
            modified = True
            print(f"  ✅ 已替换: {old_text[:20]}...")
    
    if modified:
        # 写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("  ✅ 已修复aura_fixed.py中的个人信息")
    else:
        print("  ℹ️ aura_fixed.py中未找到需要修复的个人信息")

def create_generic_data_example():
    """创建通用的数据示例"""
    print("📄 创建通用数据示例...")
    
    os.makedirs("data", exist_ok=True)
    
    # 确保example_profile.md是通用的
    generic_profile = """# Aura AI 用户档案模板

## 个人信息
- 姓名: [您的姓名]
- 职业: [您的职业]
- 领域: [您的专业领域]
- 教育: [您的教育背景]

## 喜好偏好
- 颜色: [喜欢的颜色]
- 食物: [喜欢的食物]
- 音乐: [喜欢的音乐类型]
- 活动: [喜欢的活动]

## 工作/学习领域
- [技能1]
- [技能2]
- [当前项目/研究]
- [兴趣方向]

## 学习目标
- [目标1]
- [目标2]
- [目标3]

---

**使用说明**: 
1. 请将上述方括号中的内容替换为您的实际信息
2. 这个文件用于个性化您的Aura AI助手
3. 您可以添加更多相关信息以提升AI助手的个性化程度
"""
    
    with open("data/example_profile.md", "w", encoding="utf-8") as f:
        f.write(generic_profile)
    print("  ✅ 已更新通用用户档案模板")

def main():
    """主清理函数"""
    print("🚀 开始自动清理Aura项目...")
    print("=" * 50)
    
    try:
        # 1. 备份个人信息
        backup_personal_files()
        
        # 2. 清理运行时数据
        clean_runtime_data()
        
        # 3. 清理冗余文件
        clean_redundant_files()
        
        # 4. 清理WebUI相关文件
        clean_docs_and_templates()
        
        # 5. 匿名化个人信息
        anonymize_personal_info()
        
        # 6. 修复代码中的个人信息
        fix_aura_fixed()
        
        # 7. 创建通用数据示例
        create_generic_data_example()
        
        print("=" * 50)
        print("🎉 自动清理完成！")
        print("\n📋 清理总结:")
        print("  ✅ 个人信息已备份到 personal_backup/ 目录")
        print("  ✅ 运行时数据已清理")
        print("  ✅ 冗余文件已删除")
        print("  ✅ 个人信息已匿名化")
        print("  ✅ 代码中的硬编码信息已修复")
        print("  ✅ 创建了通用模板文件")
        
        print("\n🔄 后续步骤:")
        print("  1. 检查清理结果")
        print("  2. 根据需要自定义 prompts/ 中的文件")
        print("  3. 运行 git add . && git commit -m 'Clean project and remove personal info'")
        
    except Exception as e:
        print(f"\n❌ 清理过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main()
