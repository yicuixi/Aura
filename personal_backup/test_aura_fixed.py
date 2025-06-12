"""
Aura修复版本快速测试脚本
测试基本功能是否正常工作
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_import():
    """测试基本导入"""
    try:
        from aura_fixed import AuraAgentFixed
        print("✅ 成功导入AuraAgentFixed")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_agent_initialization():
    """测试Agent初始化"""
    try:
        from aura_fixed import AuraAgentFixed
        aura = AuraAgentFixed(model_name="qwen3:4b", verbose=False)
        print("✅ Agent初始化成功")
        return True, aura
    except Exception as e:
        print(f"❌ Agent初始化失败: {e}")
        return False, None

def test_simple_query(aura):
    """测试简单查询"""
    try:
        response = aura.process_query("你好")
        print(f"✅ 简单查询成功: {response[:50]}...")
        return True
    except Exception as e:
        print(f"❌ 简单查询失败: {e}")
        return False

def test_memory_operations(aura):
    """测试记忆操作"""
    try:
        # 测试记忆存储
        result = aura.remember_fact("test/color/蓝色")
        print(f"✅ 记忆存储: {result}")
        
        # 测试记忆检索
        result = aura.recall_fact("test/color")
        print(f"✅ 记忆检索: {result}")
        return True
    except Exception as e:
        print(f"❌ 记忆操作失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("🧪 Aura修复版本功能测试")
    print("=" * 50)
    
    # 1. 测试导入
    if not test_basic_import():
        print("❌ 基础导入测试失败，退出测试")
        return
    
    # 2. 测试初始化
    success, aura = test_agent_initialization()
    if not success:
        print("❌ Agent初始化失败，退出测试")
        return
    
    # 3. 测试简单查询
    if test_simple_query(aura):
        print("✅ 解析错误已修复!")
    
    # 4. 测试记忆功能
    test_memory_operations(aura)
    
    print("=" * 50)
    print("🎉 测试完成，如果所有项目显示✅，说明修复成功!")
    print("💡 现在可以运行: python aura_fixed.py")
    print("=" * 50)

if __name__ == "__main__":
    main()
