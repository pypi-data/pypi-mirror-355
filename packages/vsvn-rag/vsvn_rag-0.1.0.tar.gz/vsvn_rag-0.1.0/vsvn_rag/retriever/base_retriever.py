# vsvn_rag/retriever/base_retriever.py

from abc import ABC, abstractmethod
from typing import List
from vsvn_rag.shared.schema import RetrievalResult

class BaseRetriever(ABC):
    """
    Interface chung cho mọi Retriever:
    - index(chunks, embeddings?): lưu trữ dữ liệu cần thiết để sau này retrieve.
    - retrieve(query, top_k): trả về danh sách RetrievalResult.
    """

    @abstractmethod
    def index(self, chunks: List[str], embeddings: List[list] = None):
        """
        Lưu trữ hoặc xây dựng chỉ mục cho các chunk (văn bản).
        Nếu retriever cần embedding (như Hybrid), embeddings sẽ được truyền vào.
        - chunks: List[str] - danh sách văn bản (chunks) đã được chunking.
        - embeddings: List[list] (tùy chọn) - danh sách embedding tương ứng nếu cần.
        """
        pass

    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> List[RetrievalResult]:
        """
        Thực hiện tìm kiếm dựa trên query (chuỗi), trả về top_k RetrievalResult.
        """
        pass
