from vsvn_rag.embedder.base_embedder import BaseEmbedder
from openai import AzureOpenAI
from typing import List, Dict
import uuid
from dataclasses import dataclass # Import dataclass

# Định nghĩa lại class EmbeddingVector như bạn mong muốn
@dataclass
class EmbeddingVector:
    chunk_id: str
    embedding: List[float]

class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, azure_api_key: str, azure_endpoint: str, embedding_model: str):
        self.client = AzureOpenAI(
            api_key=azure_api_key,
            azure_endpoint=azure_endpoint,  # Azure endpoint
            api_version="2024-12-01-preview"  # Phiên bản API phổ biến cho Azure OpenAI
        )
        self.embedding_model = embedding_model

    def embed(self, texts: List[str]) -> List[EmbeddingVector]: # Thay đổi kiểu trả về
        """
        Tạo embedding cho danh sách văn bản sử dụng Azure OpenAI.
        Args:
            texts: Danh sách các chuỗi văn bản.
        Returns:
            Danh sách các đối tượng EmbeddingVector chứa chunk_id và embedding.
        """
        try:
            embeddings: List[EmbeddingVector] = [] # Khởi tạo với kiểu List[EmbeddingVector]
            response = self.client.embeddings.create(
                input=texts,
                model=self.embedding_model  # Sử dụng deployment_name thay vì embedding_model
            )
            for i, data in enumerate(response.data):
                # Tạo một instance của EmbeddingVector và thêm vào danh sách
                embeddings.append(
                    EmbeddingVector(
                        chunk_id=str(uuid.uuid4()),  # Tạo ID duy nhất cho mỗi embedding
                        embedding=data.embedding
                    )
                )
            print(embeddings)
            return embeddings

        except Exception as e:
            print(f"Error while fetching embeddings: {e}")
            return [] # Trả về danh sách rỗng nếu có lỗi