# project_root/main.py

import logging
import yaml
from typing import List  # <-- Thêm dòng này để sử dụng List[...] trong type hints

from vsvn_rag.embedder.offline_embedder import OfflineEmbedder
from vsvn_rag.embedder.openai_embedder import OpenAIEmbedder
from vsvn_rag.shared.schema import EmbeddingVector
from vsvn_rag.vectorstore.qdrant_store import QdrantVectorStore


def load_config(config_path=r"C:\Users\ChungBH\PycharmProjects\vsvn_RAG_module\vsvn_rag_common_modules\vsvn_rag\config\config.yaml"):
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config


def setup_logging(logging_config):
    log_level = logging_config.get('level', 'INFO').upper()
    log_format = logging_config.get('format', "%(asctime)s - %(levelname)s - %(message)s")
    logging.basicConfig(level=log_level, format=log_format)


def setup_embedder(embedder_config):
    mode = embedder_config['mode']
    if mode == 'offline':
        model = embedder_config['model']
        embedder = OfflineEmbedder(model_name_or_path=model)
    elif mode == 'azure_openai':
        azure_config = embedder_config['azure']
        api_key = azure_config['api_key']
        endpoint = azure_config['endpoint']
        embedding_model = azure_config['embedding_model']
        embedder = OpenAIEmbedder(
            azure_api_key=api_key,
            azure_endpoint=endpoint,
            embedding_model=embedding_model
        )
    else:
        raise ValueError(f"Invalid embedder mode: {mode}")
    return embedder


if __name__ == "__main__":
    # 1. Load cấu hình
    config = load_config(r"C:\Users\ChungBH\PycharmProjects\vsvn_RAG_module\vsvn_rag_common_modules\vsvn_rag\config\config.yaml")
    logging_config = config['logging']
    setup_logging(logging_config)

    # 2. Thiết lập embedder
    embedder_config = config['embedder']
    embedder = setup_embedder(embedder_config)

    # 3. Tạo embedding từ các câu ví dụ
    texts = ["This is a test sentence.", "Here's another one."]
    # embeddings: List[EmbeddingVector] = embedder.embed(texts)

    # 4. Lấy đúng chiều embedding (dimension) từ vector đầu tiên
    # dimension = len(embeddings[0].embedding)

    # 2. (Nếu muốn) Dùng AzureOpenAIEmbedder
    azure = OpenAIEmbedder(
        azure_api_key="ai-321be1c7610bf4f380c1d63d34de0e43",
        azure_endpoint="http://10.166.128.159:8011",
        embedding_model="text-embedding-ada-002"
    )
    azure_vectors: List[EmbeddingVector] = azure.embed(texts)
    dimension = len(azure_vectors[0].embedding)

    # 5. Khởi tạo QdrantVectorStore (dimension = chiều của mỗi embedding)
    qdrant = QdrantVectorStore(
        host="localhost",
        port=6333,
        index_name="my_collection",
        dimension=dimension,
        distance="Cosine",
    )

    # 6. Lưu embeddings vào Qdrant
    qdrant.add_embeddings(azure_vectors)

    # 7. Thử tìm top 2 kết quả tương tự với vector đầu tiên
    query_vec = azure_vectors[0].embedding
    results = qdrant.search(query_vector=query_vec, top_k=2)

    print("Kết quả tìm kiếm top 2:")
    for hit in results:
        print(f"  - id={hit.id}, score={hit.score}")
