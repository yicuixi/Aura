# 兼容 langchain 0.3.x 和 1.x
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    from langchain.embeddings import HuggingFaceEmbeddings

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader, CSVLoader, UnstructuredMarkdownLoader, Docx2txtLoader
from langchain_community.retrievers import BM25Retriever

try:
    from langchain_classic.retrievers import EnsembleRetriever
except ImportError:
    from langchain.retrievers import EnsembleRetriever
import os

# 可选：重排序模型（首次使用会自动下载）
try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("提示: 安装 sentence-transformers 可启用重排序功能")

class RAGSystem:
    def __init__(self, persist_directory="db", use_m3e=True):
        # 初始化嵌入模型
        if use_m3e:
            # 使用 m3e-base（中文语义匹配专用，效果最好）
            print("正在加载 m3e-base 嵌入模型...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="moka-ai/m3e-base", 
                model_kwargs={'device': 'cpu'}
            )
            print("已加载 m3e-base 嵌入模型")
        else:
            # 使用 Ollama（通用但效果一般）
            try:
                self.embeddings = OllamaEmbeddings(
                    model="qwen2.5:7b",
                    base_url="http://localhost:11434"
                )
                print("已连接到Ollama嵌入模型")
            except Exception as e:
                print(f"Ollama失败: {e}，回退到 m3e-base")
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
        
        # 初始化BM25检索器（延迟加载，需要文档）
        self.bm25_retriever = None
        self.all_documents = []  # 保存文档用于BM25
        
        # 初始化重排序模型
        self.reranker = None
        if RERANKER_AVAILABLE:
            try:
                # 使用轻量级中文重排序模型
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
                print("已加载重排序模型")
            except Exception as e:
                print(f"重排序模型加载失败: {e}")
    
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
                    elif extension in [".doc", ".docx"]:
                        loader = Docx2txtLoader(file_path)
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
            
            # 文本分割（论文等长文档建议用较大的chunk）
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,  # 增大块大小，保持上下文完整性
                chunk_overlap=100
            )
            splits = text_splitter.split_documents(documents)
            print(f"创建了 {len(splits)} 个文本块")
            
            if not splits:
                raise ValueError(f"文档分割后没有产生任何文本块，请检查文档内容")
            
            # 添加到向量库
            self.vectorstore.add_documents(splits)
            print("文档已添加到知识库")
            
            # 更新BM25检索器
            self.all_documents.extend(splits)
            self._init_bm25_retriever()
            
            return True
        except Exception as e:
            import traceback
            print(f"加载文档时出错: {str(e)}")
            print(traceback.format_exc())
            raise e
    
    def _init_bm25_retriever(self):
        """初始化BM25检索器"""
        if self.all_documents:
            self.bm25_retriever = BM25Retriever.from_documents(self.all_documents)
            self.bm25_retriever.k = 5  # BM25返回数量
            print(f"BM25检索器已初始化，文档数: {len(self.all_documents)}")
    
    def search(self, query, k=3):
        """搜索相关文档（原始向量检索）"""
        results = self.vectorstore.similarity_search(query, k=k)
        return results
    
    def hybrid_search(self, query, k=3, use_rerank=True):
        """
        多路召回 + 重排序
        1. 向量检索（语义相似）
        2. BM25检索（关键词匹配）
        3. 融合结果
        4. 重排序优化
        """
        # 向量检索
        vector_results = self.vectorstore.similarity_search(query, k=k*2)
        
        # BM25检索（如果可用）
        bm25_results = []
        if self.bm25_retriever:
            try:
                bm25_results = self.bm25_retriever.invoke(query)[:k*2]
            except Exception as e:
                print(f"BM25检索失败: {e}")
        
        # 融合结果（去重）
        seen_contents = set()
        merged_results = []
        
        for doc in vector_results + bm25_results:
            content_hash = hash(doc.page_content[:100])  # 用前100字符去重
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                merged_results.append(doc)
        
        print(f"多路召回: 向量{len(vector_results)}条 + BM25{len(bm25_results)}条 → 融合{len(merged_results)}条")
        
        # 重排序（如果可用）
        if use_rerank and self.reranker and merged_results:
            try:
                # 构建query-doc对
                pairs = [[query, doc.page_content] for doc in merged_results]
                scores = self.reranker.predict(pairs)
                
                # 按分数排序
                scored_results = list(zip(merged_results, scores))
                scored_results.sort(key=lambda x: x[1], reverse=True)
                
                reranked = [doc for doc, score in scored_results[:k]]
                print(f"重排序完成，返回top{k}")
                return reranked
            except Exception as e:
                print(f"重排序失败: {e}")
        
        return merged_results[:k]
    
    def search_with_scores(self, query, k=3):
        """搜索并返回相似度分数"""
        results = self.vectorstore.similarity_search_with_score(query, k=k)
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
