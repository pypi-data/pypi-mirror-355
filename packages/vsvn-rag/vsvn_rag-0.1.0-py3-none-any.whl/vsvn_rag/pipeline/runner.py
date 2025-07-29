import yaml
import os
import sys

from vsvn_rag.shared.schema import EmbeddingVector

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vsvn_rag.reader.pdf_loader import PDFLoader
from vsvn_rag.chunker.rule_chunker import RuleBasedChunker
from vsvn_rag.embedder.openai_embedder import OpenAIEmbedder
from vsvn_rag.embedder.offline_embedder import OfflineEmbedder  # Import OfflineEmbedder
from vsvn_rag.retriever.bm25 import BM25Retriever
from vsvn_rag.retriever.reranker import RerankRetriever
from vsvn_rag.retriever.hybrid import HybridRetriever
from vsvn_rag.generator.openai_generator import OpenAIGenerator
from vsvn_rag.logging.logger import setup_logger
from vsvn_rag.vectorstore.qdrant_store import QdrantVectorStore
from dotenv import load_dotenv
import os



class PipelineRunner:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = {}

    load_dotenv()

    def load_config(self):
        # self.logger.info(f"🔹 Loading configuration from {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:  # Thêm encoding='utf-8'
            self.config = yaml.safe_load(f)

        logging_cfg = self.config.get("logging", {})
        self.logger = setup_logger(logging_cfg)
        self.logger.info(f"🔹 Loaded configuration from {self.config_path}")

    def load_modules(self):
        # self.logger.info("🔹 Loading modules based on configuration")
        # loader_type = self.config["loader"]["type"]
        # if loader_type == "pdf":
        #     self.loader = PDFLoader()
        #
        # chunker_type = self.config["chunker"]["type"]
        # if chunker_type == "rule":
        #     self.chunker = RuleBasedChunker()

        # Chọn embedder tùy theo cấu hình mode
        embedder_config = self.config.get("embedder", {})
        qdrant_config = self.config.get("qdrant", {})
        mode = embedder_config.get("mode")

        if mode == "offline":
            model = embedder_config["model"]
            self.embedder = OfflineEmbedder(model_name_or_path=model)
        elif mode == "azure_openai":
            azure_config = embedder_config.get("azure", {})
            self.embedder = OpenAIEmbedder(
                azure_api_key=os.path.expandvars(azure_config["api_key"]),
                azure_endpoint=os.path.expandvars(azure_config["endpoint"]),
                embedding_model=os.path.expandvars(azure_config["embedding_model"])

            )
        else:
            raise ValueError(f"Invalid embedder mode: {mode}")

        self.qdrant = QdrantVectorStore(
            host=os.path.expandvars(qdrant_config["host"]),
            port=os.path.expandvars(qdrant_config["port"]),
            index_name=os.path.expandvars(qdrant_config["index_name"]),
            dimension=384,
            distance=os.path.expandvars(qdrant_config["distance"]),

        )
        retr_cfg = self.config["retriever"]
        method = retr_cfg["method"]
        top_k = retr_cfg["top_k"]
        self.logger.info(f"🔹 method:{method}")
        if method == "bm25":
            self.retriever = BM25Retriever(top_k=top_k)
        elif method == "rerank":
            base_ret = BM25Retriever(top_k=top_k * 5)  # lấy 5 lần top để rerank
            self.retriever = RerankRetriever(base_retriever=base_ret, embedder=self.embedder, top_m=top_k * 5)
        elif method == "hybrid":
            base_ret = BM25Retriever(top_k=top_k * 5)
            self.retriever = HybridRetriever(bm25_retriever=base_ret, embedder=self.embedder,
                                             alpha=retr_cfg.get("alpha", 0.5))
        else:
            raise ValueError(f"Invalid retriever method: {method}")
    # self.retriever = BM25Retriever(top_k=self.config["retriever"]["top_k"])
    # self.generator = OpenAIGenerator(model=self.config["generator"]["model"])

    def run(self):
        self.load_config()
        self.load_modules()

        # file_path = self.config["loader"]["path"]
        # self.logger.info(f"🔹 Loading document: {file_path}")
        # document = self.loader.load(file_path)
        #
        # self.logger.info("🔹 Chunking document...")
        # chunks = self.chunker.chunk(document)

        # self.logger.info("🔹 Embedding chunks...")
        # logger.info("🔹 Embedding input text...")
        # embeddings = self.embedder.embed([text])  # Sử dụng text trực tiếp để tạo embeddings
        # logger.info(f"🔹 Embedding completed :{embeddings}")
        # self.qdrant.add_embeddings(embeddings)
        # query_vec = embeddings[0].embedding
        # results = self.qdrant.search(query_vector=query_vec, top_k=2)
        # for hit in results:
        #     logger.info(f"  - id={hit.id}, score={hit.score}")

        chunks = [
            "Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to learn.",
            "In supervised learning, models are trained using labeled datasets to make predictions or decisions.",
            "Unsupervised learning finds hidden patterns or intrinsic structures in input data without explicit labels.",
            "Reinforcement learning teaches agents to make a sequence of decisions by rewarding desired behaviors."
        ]

        metadata = [
            {"source": "Chapter 1: Introduction"},
            {"source": "Chapter 2: Supervised Learning"},
            {"source": "Chapter 3: Unsupervised Learning"},
            {"source": "Chapter 4: Reinforcement Learning"}
        ]

        chunk_ids = ["c1", "c2", "c3", "c4"]
        # self.retriever.index([text], embeddings)  # Index văn bản đã embedding
        # Embedding and storing embeddings correctly
        self.logger.info("🔹 Embedding input text...")
        embeddings = self.embedder.embed(chunks)  # Embedding the chunks

        # Make sure the embeddings are the correct type (list of float arrays)
        embedding_vectors = [embedding.embedding for embedding in embeddings]

        # Indexing using retriever
        self.retriever.index(chunks, embeddings=embedding_vectors, metadata=metadata, chunk_ids=chunk_ids)
        #
        # # Search and retrieve top k results
        query = "Machine learning is"
        self.logger.info(f"🔹 Retrieving top results for query: {query}")
        top_chunks = self.retriever.retrieve(query, top_k=3)
        #
        self.logger.info(f"🔹 Retrieving completed: {top_chunks}")
        for result in top_chunks:
            self.logger.info(f"  - {result.chunk_id} | score: {result.score:.4f} | content: {result.content[:100]}...")


        # self.logger.info("🔹 Indexing and retrieving top chunks...")
        # self.retriever.index(chunks, embeddings)
        # query = input("❓ Enter your question: ")
        # top_chunks = self.retriever.retrieve(query)
        #
        # self.logger.info("🔹 Generating answer...")
        # answer = self.generator.generate(query, top_chunks)
        # self.logger.info("✅ Answer:", answer)
