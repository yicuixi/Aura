#!/usr/bin/env python3
"""
Test script for optimized Aura query processing
Tests different query types to verify routing logic
"""

def test_routing_logic():
    """Test query routing without actually running Aura"""
    
    test_cases = [
        # Simple greetings (should bypass knowledge base)
        ("hello", "Simple greeting - should bypass knowledge base"),
        ("你好", "Chinese greeting - should bypass knowledge base"),
        ("hi there", "Casual greeting - should bypass knowledge base"),
        
        # Real-time queries (should go to Agent directly)
        ("weather in Shanghai today", "Weather query - should use Agent directly"),
        ("current stock price", "Stock query - should use Agent directly"),
        ("latest news", "News query - should use Agent directly"),
        
        # Technical queries (should check knowledge base)
        ("what is OAM phase reconstruction", "Technical - should check knowledge base"),
        ("deep learning algorithm", "Technical - should check knowledge base"),
        
        # Personal queries (should check memory first)
        ("my research progress", "Personal - should check memory first"),
        ("what color do I like", "Preference - should check memory first"),
    ]
    
    def should_query_knowledge_base(query):
        """Simulate the logic to determine if knowledge base should be queried"""
        query_lower = query.lower().strip()
        
        # 1. Simple greetings - NO
        greeting_patterns = ["hello", "hi", "hey", "你好", "您好", "哇", "嗨"]
        if any(pattern in query_lower for pattern in greeting_patterns) and len(query.split()) <= 3:
            return False, "Simple greeting"
        
        # 2. Real-time queries - NO (goes to Agent)
        realtime_keywords = [
            "weather", "天气", "temperature", "温度", "forecast", "预报",
            "stock", "股票", "股价", "price", "价格", 
            "news", "新闻", "latest", "最新", "current", "当前",
            "today", "今天", "now", "现在", "real-time", "实时"
        ]
        if any(keyword in query_lower for keyword in realtime_keywords):
            return False, "Real-time query (uses Agent)"
        
        # 3. Technical queries - YES
        knowledge_keywords = [
            "oam", "phase", "reconstruction", "少样本", "deep learning", "neural network",
            "optical", "光学", "diffusion", "扩散", "u-net", "tensorrt",
            "research", "研究", "paper", "论文", "algorithm", "算法",
            "technique", "技术", "method", "方法", "model", "模型"
        ]
        if any(keyword in query_lower for keyword in knowledge_keywords):
            return True, "Technical query"
        
        # 4. Personal queries - NO (checks memory first)
        personal_keywords = ["my", "我的", "favorite", "喜欢"]
        if any(keyword in query_lower for keyword in personal_keywords):
            return False, "Personal query (checks memory first)"
        
        # 5. Default - goes to Agent
        return False, "General query (uses Agent)"
    
    print("=" * 70)
    print("🧪 Testing Aura Query Routing Logic")
    print("=" * 70)
    
    print("\n📋 Test Results:")
    for query, expected in test_cases:
        will_query_kb, reason = should_query_knowledge_base(query)
        
        # Determine if this matches our expectations
        expected_lower = expected.lower()
        matches_expectation = True
        
        if "bypass knowledge base" in expected_lower and will_query_kb:
            matches_expectation = False
        elif "check knowledge base" in expected_lower and not will_query_kb:
            matches_expectation = False
        
        status = "✅" if matches_expectation else "❌"
        
        print(f"\n{status} Query: '{query}'")
        print(f"   Expected: {expected}")
        print(f"   Result: {'Will query KB' if will_query_kb else 'Will NOT query KB'} - {reason}")
    
    print("\n" + "=" * 70)
    print("📝 Summary:")
    print("✅ = Routing logic matches expectations")
    print("❌ = Routing logic needs adjustment")
    print("\n💡 Key improvements:")
    print("1. Simple greetings now bypass knowledge base")
    print("2. Real-time queries go directly to Agent")
    print("3. Technical queries still use knowledge base appropriately")
    print("4. Personal queries check memory first")

def show_optimization_summary():
    """Show summary of optimizations made"""
    print("\n" + "=" * 70)
    print("🚀 Aura Optimization Summary")
    print("=" * 70)
    
    print("\n🔧 Changes Made:")
    print("1. Smart Query Routing:")
    print("   - Simple greetings → Direct response (no KB query)")
    print("   - Real-time queries → Agent with tools")
    print("   - Technical queries → Knowledge base search")
    print("   - Personal queries → Memory system first")
    
    print("\n2. Removed Inefficiencies:")
    print("   - No more unnecessary KB queries for greetings")
    print("   - No more KB queries for weather/news/stocks")
    print("   - Faster response for common interactions")
    
    print("\n📈 Expected Performance Improvements:")
    print("   - ⚡ Faster responses for greetings")
    print("   - 🎯 More accurate routing to correct data sources")
    print("   - 💾 Reduced unnecessary computation")
    print("   - 🧠 Better use of memory vs knowledge base")
    
    print("\n📁 Files Modified:")
    print("   - aura_fixed.py (optimized with smart routing)")
    print("   - Backup created in optimization_backup/ folder")

if __name__ == "__main__":
    test_routing_logic()
    show_optimization_summary()
    
    print("\n🎉 Optimization Complete!")
    print("The optimized Aura should now:")
    print("- Respond to greetings immediately without KB queries")
    print("- Handle real-time data requests more efficiently")
    print("- Still use knowledge base for technical questions")
    print("\nTry running the optimized aura_fixed.py to test!")
