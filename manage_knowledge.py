# manage_knowledge.py
# 知识库管理工具

import os
import sys
import shutil
from datetime import datetime
import argparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag import RAGSystem

def backup_db(db_path="db"):
    """备份现有知识库"""
    if not os.path.exists(db_path):
        print(f"知识库不存在: {db_path}")
        return False
        
    backup_name = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = os.path.join(os.path.dirname(db_path), backup_name)
    
    try:
        shutil.copytree(db_path, backup_path)
        print(f"✅ 知识库已备份至: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 备份失败: {str(e)}")
        return False

def clear_db(db_path="db"):
    """清除知识库"""
    if not os.path.exists(db_path):
        print(f"知识库不存在: {db_path}")
        return True
        
    try:
        shutil.rmtree(db_path)
        os.makedirs(db_path)
        print(f"✅ 知识库已清空: {db_path}")
        return True
    except Exception as e:
        print(f"❌ 清除失败: {str(e)}")
        return False

def load_documents(data_path="data", extension=".md", db_path="db"):
    """加载文档到知识库"""
    if not os.path.exists(data_path):
        print(f"数据目录不存在: {data_path}")
        return False
        
    try:
        rag = RAGSystem(persist_directory=db_path)
        rag.add_documents(data_path, extension=extension)
        print(f"✅ 已将{extension}格式的文档加载到知识库")
        return True
    except Exception as e:
        print(f"❌ 加载文档出错: {str(e)}")
        return False

def list_documents(data_path="data", extension=None):
    """列出可加载的文档"""
    if not os.path.exists(data_path):
        print(f"数据目录不存在: {data_path}")
        return False
    
    try:
        files = os.listdir(data_path)
        if extension:
            files = [f for f in files if f.endswith(extension)]
            
        if not files:
            print(f"没有{extension or '任何'}文件在{data_path}目录")
            return False
            
        print(f"\n可用文档 ({len(files)}):")
        for i, file in enumerate(files, 1):
            file_path = os.path.join(data_path, file)
            size = os.path.getsize(file_path)
            print(f"{i}. {file} ({size/1024:.1f} KB)")
            
        return True
    except Exception as e:
        print(f"❌ 列出文档出错: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aura知识库管理工具")
    parser.add_argument("action", choices=["backup", "clear", "load", "list", "rebuild"], 
                       help="要执行的操作")
    parser.add_argument("--db", default="db", help="知识库目录路径")
    parser.add_argument("--data", default="data", help="数据目录路径")
    parser.add_argument("--ext", default=".md", help="要加载的文件扩展名")
    
    args = parser.parse_args()
    
    if args.action == "backup":
        backup_db(args.db)
    elif args.action == "clear":
        confirm = input("⚠️ 确定要清空知识库吗? 此操作不可撤销! (y/N): ")
        if confirm.lower() == 'y':
            clear_db(args.db)
        else:
            print("已取消")
    elif args.action == "load":
        list_documents(args.data, args.ext)
        confirm = input(f"确定要加载这些文档到知识库 {args.db}? (y/N): ")
        if confirm.lower() == 'y':
            load_documents(args.data, args.ext, args.db)
        else:
            print("已取消")
    elif args.action == "list":
        list_documents(args.data, args.ext)
    elif args.action == "rebuild":
        confirm = input("⚠️ 确定要重建知识库吗? 将先备份、清空然后重新加载! (y/N): ")
        if confirm.lower() == 'y':
            backup_db(args.db)
            if clear_db(args.db):
                list_documents(args.data, args.ext)
                load = input(f"要加载这些文档到新知识库吗? (y/N): ")
                if load.lower() == 'y':
                    load_documents(args.data, args.ext, args.db)
                else:
                    print("已跳过加载，知识库已清空")
        else:
            print("已取消")
