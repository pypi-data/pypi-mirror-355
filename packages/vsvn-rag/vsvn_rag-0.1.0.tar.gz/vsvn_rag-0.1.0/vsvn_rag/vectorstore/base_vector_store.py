# project_root/vector_store/base_vector_store.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class BaseVectorStore(ABC):
    """
    Interface chung cho mọi Vector Store (Qdrant, FAISS, Pinecone, ...).
    """

    @abstractmethod
    def add_embeddings(
        self,
        vectors: List,                   # Thực ra vectors là List[EmbeddingVector], nhưng ta để chung List
        payloads: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Lưu (upsert) danh sách EmbeddingVector vào Vector Store.
        payloads (nếu có) sẽ là metadata tương ứng với từng vector.
        """
        ...

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm tương tự (similarity search) với query_vector, trả về top_k kết quả.
        Nếu filter != None, áp filter metadata.
        Kết quả có thể là List[Dict] chứa { id, score, payload, ... } tuỳ store.
        """
        ...
