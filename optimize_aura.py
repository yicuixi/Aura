#!/usr/bin/env python3
"""
Fix Aura query processing logic
Avoid unnecessary knowledge base queries for simple greetings and real-time data requests
"""

import os
import shutil
from datetime import datetime

def create_optimized_query_processor():
    """Create optimized process_query method with smart routing"""
    
    optimized_code = '''def process_query(self, query: str) -> str:
        """Optimized query processing with smart routing"""
        try:
            # Clean up the query
            query_lower = query.lower().strip()
            
            # 1. Handle simple greetings directly (no need for knowledge base)
            greeting_patterns = ["hello", "hi", "hey", "你好", "您好", "哇", "嗨"]
            if any(pattern in query_lower for pattern in greeting_patterns) and len(query.split()) <= 3:
                greeting_responses = [
                    "你好！我是Aura，Lydia的AI助手。有什么我可以帮您的吗？",
                    "Hello! I'm Aura, Lydia's AI assistant. How can I help you today?",
                    "嗨！很高兴见到你。有什么需要我协助的吗？"
                ]
                # Simple response without tools
                import random
                response = random.choice(greeting_responses)
                self.long_term_memory.add_conversation(query, response)
                return response
            
            # 2. Check for preference-related queries
            is_preference, preference_result = self.extract_preferences(query)
            if is_preference:
                prompt = f"""User expressed preference: "{query}"
                
I have recorded this preference. Please respond as Aura with a friendly but professional reply 
confirming the preference has been recorded. Keep the tone warm but not overly dramatic."""
                
                response = self.llm.invoke(prompt).strip()
                self.long_term_memory.add_conversation(query, response)
                return response
            
            # 3. Check if asking about existing preferences
            is_asking_pref, pref_response = self.check_preference_question(query)
            if is_asking_pref and pref_response:
                prompt = f"""User asked about their preference: "{query}"
                
According to my records: {pref_response}
                
Please respond as Aura in a friendly but professional manner, mentioning this preference naturally."""
                
                response = self.llm.invoke(prompt).strip()
                self.long_term_memory.add_conversation(query, response)
                return response
            
            # 4. Identify real-time data queries (weather, stock, news, etc.)
            realtime_keywords = [
                "weather", "天气", "temperature", "温度", "forecast", "预报",
                "stock", "股票", "股价", "price", "价格", 
                "news", "新闻", "latest", "最新", "current", "当前",
                "today", "今天", "now", "现在", "real-time", "实时"
            ]
            
            needs_realtime = any(keyword in query_lower for keyword in realtime_keywords)
            if needs_realtime:
                logger.info("Detected real-time query, using Agent directly")
                result = self.agent.invoke({"input": query})
                
                if isinstance(result, dict) and "output" in result:
                    response = result["output"]
                else:
                    response = str(result)
                
                self.long_term_memory.add_conversation(query, response)
                return response
            
            # 5. Try to extract memory keys for personal information
            memory_result = None
            try:
                memory_extraction_prompt = f"""Extract possible memory key from user query:
"{query}"

Return the most likely category/key combination in format: category/key

Examples:
- "my thesis progress" -> user/thesis_progress  
- "my favorite color" -> preference/color
- "my research direction" -> user/research

Only return one category/key combination, no explanation."""
                
                memory_key = self.llm.invoke(memory_extraction_prompt).strip()
                logger.info(f"Extracted memory key: {memory_key}")
                
                if "/" in memory_key and len(memory_key.split("/")) == 2:
                    memory_result = self.recall_fact(memory_key)
                    logger.info(f"Memory query result: {memory_result}")
                    
                    if memory_result and "没有找到相关记忆" not in memory_result:
                        # Found relevant memory, use it directly
                        memory_value = memory_result.split(":")[1].strip() if ":" in memory_result else ""
                        prompt = f"""User query: {query}
                        
Based on memory: {memory_value}
                        
Please respond as Aura in a friendly professional manner. Answer based only on known facts."""
                        
                        response = self.llm.invoke(prompt).strip()
                        self.long_term_memory.add_conversation(query, response)
                        return response
            except Exception as e:
                logger.error(f"Memory extraction error: {str(e)}")
            
            # 6. Check if query might benefit from knowledge base
            knowledge_keywords = [
                "oam", "phase", "reconstruction", "少样本", "deep learning", "neural network",
                "optical", "光学", "diffusion", "扩散", "u-net", "tensorrt",
                "research", "研究", "paper", "论文", "algorithm", "算法",
                "technique", "技术", "method", "方法", "model", "模型"
            ]
            
            might_need_knowledge = any(keyword in query_lower for keyword in knowledge_keywords)
            
            if might_need_knowledge:
                # Query knowledge base for technical/research topics
                try:
                    knowledge_result = self.search_knowledge(query)
                    logger.info(f"Knowledge base result: {knowledge_result}")
                    
                    if knowledge_result and len(knowledge_result.strip()) > 20:
                        prompt = f"""User query: {query}
                        
Based on knowledge base: {knowledge_result}
                        
Please respond as Aura, providing helpful information based on the search results."""
                        
                        response = self.llm.invoke(prompt).strip()
                        self.long_term_memory.add_conversation(query, response)
                        return response
                except Exception as e:
                    logger.error(f"Knowledge base search failed: {str(e)}")
            
            # 7. Default: Use Agent for general queries
            logger.info("Using Agent for general query processing")
            result = self.agent.invoke({"input": query})
            
            # Check for specialized query handlers
            handler = query_handler_factory.create_handler(query, self.llm)
            if handler:
                logger.info("Using specialized query handler")
                response = handler.handle(query, result, self.long_term_memory)
            else:
                if isinstance(result, dict) and "output" in result:
                    response = result["output"]
                else:
                    response = str(result)
            
            self.long_term_memory.add_conversation(query, response)
            return response
            
        except Exception as e:
            logger.error(f"Query processing error: {str(e)}")
            return f"Sorry, I encountered an error processing your request: {str(e)}"'''
    
    return optimized_code

def fix_aura_query_processing():
    """Apply the optimized query processing to Aura files"""
    
    project_root = "D:/Code/Aura"
    backup_dir = f"{project_root}/optimization_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Files to fix
    target_files = [
        "aura_mcp.py",
        "aura_fixed.py", 
        "aura_v2.py"
    ]
    
    optimized_method = create_optimized_query_processor()
    
    for file_name in target_files:
        file_path = os.path.join(project_root, file_name)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_name}")
            continue
            
        # Backup original file
        backup_path = os.path.join(backup_dir, file_name)
        shutil.copy2(file_path, backup_path)
        print(f"Backed up: {file_name}")
        
        # Read original file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the process_query method and replace it
        start_marker = "def process_query(self, query: str) -> str:"
        end_marker = "\n    def run_cli(self):"
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker, start_idx)
        
        if start_idx != -1 and end_idx != -1:
            # Replace the method
            new_content = (content[:start_idx] + 
                          optimized_method + "\n    " +
                          content[end_idx+1:])
            
            # Write the modified file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"Optimized: {file_name}")
        else:
            print(f"Could not find process_query method in: {file_name}")
    
    print(f"\nOptimization complete!")
    print(f"Backup created at: {backup_dir}")
    print("\nChanges made:")
    print("1. Simple greetings bypass knowledge base")
    print("2. Real-time queries go directly to Agent")  
    print("3. Technical queries check knowledge base")
    print("4. Memory queries are handled efficiently")
    print("5. Better routing logic overall")

if __name__ == "__main__":
    print("=== Aura Query Processing Optimization ===")
    print("\nThis script will:")
    print("1. Backup original files")
    print("2. Replace process_query method with optimized version") 
    print("3. Add smart routing logic")
    
    fix_aura_query_processing()
    print("\nOptimization complete!")
