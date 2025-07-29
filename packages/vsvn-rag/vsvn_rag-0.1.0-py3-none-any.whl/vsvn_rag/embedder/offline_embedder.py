# embedding/offline_embedder.py

from typing import List
from vsvn_rag.shared.schema import EmbeddingVector  # Import từ shared.schema
from .base_embedder import BaseEmbedder
from sentence_transformers import SentenceTransformer
from loguru import logger


class OfflineEmbedder(BaseEmbedder):
    """
    Embedder sử dụng mô hình offline (SentenceTransformer) để tạo embeddings.
    """

    def __init__(self, model_name_or_path: str):
        """
        Khởi tạo OfflineEmbedder với mô hình đã chọn từ cấu hình.
        """
        self.model = SentenceTransformer(model_name_or_path)

    def embed(self, texts: List[str]) -> List[EmbeddingVector]:
        """
        Sử dụng mô hình SentenceTransformer để tạo embeddings.
        """
        embeddings_list = self.model.encode(texts, show_progress_bar=False).tolist()
        results: List[EmbeddingVector] = []
        for idx, vec in enumerate(embeddings_list):
            chunk_id = f"id_{idx}"
            results.append(EmbeddingVector(chunk_id=chunk_id, embedding=vec))
        print("result:",results)
        return results
