from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader, CSVLoader, UnstructuredMarkdownLoader
import os

class RAGSystem:
    def __init__(self, persist_directory="db"):
        # 初始化嵌入模型 (使用Ollama代替HuggingFace)
        try:
            self.embeddings = OllamaEmbeddings(
                model="qwen3:4b",
                base_url="http://localhost:11435"
            )
            print("已连接到Ollama嵌入模型")
        except Exception as e:
            print(f"Ollama嵌入模型初始化失败: {str(e)}")
            print("回退到HuggingFace嵌入模型...")
            # 如果Ollama失败，回退到HuggingFace
            self.embeddings = HuggingFaceEmbeddings(
                model_name="moka-ai/m3e-base", 
                model_kwargs={'device': 'cpu'}
            )
        
        # 初始化或连接到向量存储
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        print(f"已连接到知识库位置: {persist_directory}")
    
    def add_documents(self, docs_path, extension=".md"):
        """添加文档到知识库"""
        # 确保文档路径存在
        if not os.path.exists(docs_path):
            raise FileNotFoundError(f"文档路径不存在: {docs_path}")
            
        # 检查是否有匹配的文件
        import glob
        # 将文件路径转换为绝对路径
        absolute_path = os.path.abspath(docs_path)
        pattern = os.path.join(absolute_path, f"*{extension}")
        matching_files = glob.glob(pattern)
        
        print(f"搜索模式: {pattern}")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"目标目录内容: {os.listdir(docs_path)}")
        
        if not matching_files:
            raise ValueError(f"在{docs_path}中没有找到{extension}格式的文件")
            
        print(f"找到{len(matching_files)}个{extension}文件: {matching_files}")
            
        # 根据文件类型选择加载器
        try:
            # 直接处理每个找到的文件
            documents = []
            
            for file_path in matching_files:
                try:
                    print(f"正在加载文件: {file_path}")
                    if extension == ".pdf":
                        loader = PyPDFLoader(file_path)
                    elif extension == ".csv":
                        loader = CSVLoader(file_path)
                    else:
                        # 对于MD和其他文本文件使用TextLoader
                        loader = TextLoader(file_path, encoding='utf-8')
                        
                    file_docs = loader.load()
                    documents.extend(file_docs)
                    print(f"成功加载文件 {file_path}, 包含 {len(file_docs)} 个文档")
                except Exception as e:
                    print(f"加载文件 {file_path} 时出错: {str(e)}")
            
            print(f"总计加载了 {len(documents)} 个文档")
            
            if not documents:
                raise ValueError(f"无法加载任何文档内容，请检查文件格式和权限")
            
            # 文本分割
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            splits = text_splitter.split_documents(documents)
            print(f"创建了 {len(splits)} 个文本块")
            
            if not splits:
                raise ValueError(f"文档分割后没有产生任何文本块，请检查文档内容")
            
            # 添加到向量库
            self.vectorstore.add_documents(splits)
            print("文档已添加到知识库")
            
            # 持久化保存
            self.vectorstore.persist()
            print("知识库已持久化保存")
            
            return True
        except Exception as e:
            import traceback
            print(f"加载文档时出错: {str(e)}")
            print(traceback.format_exc())
            raise e
    
    def search(self, query, k=3):
        """搜索相关文档"""
        results = self.vectorstore.similarity_search(query, k=k)
        return results

# 使用示例
if __name__ == "__main__":
    # 创建数据目录
    if not os.path.exists("data"):
        os.makedirs("data")
        print("创建data目录用于存放知识库文档")
        
    # 初始化RAG系统
    rag = RAGSystem(persist_directory="db")
    
    # 添加文档示例(取消注释使用)
    # rag.add_documents("data", extension=".txt")
    
    # 搜索示例(取消注释使用)
    # results = rag.search("查询内容")
    # for doc in results:
    #     print(doc.page_content)
