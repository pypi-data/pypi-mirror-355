# vsvn_rag/retriever/bm25_retriever.py

from typing import List, Dict
import numpy as np
from rank_bm25 import BM25Okapi
from vsvn_rag.retriever.base_retriever import BaseRetriever
from vsvn_rag.shared.schema import RetrievalResult

class BM25Retriever(BaseRetriever):
    """
    Triển khai thuật toán BM25 dùng rank_bm25.
    """

    def __init__(self, top_k: int = 5):
        """
        top_k: số lượng kết quả mặc định sẽ trả về nếu không truyền top_k ở retrieve().
        """
        self.top_k = top_k
        self.bm25 = None
        self.chunks = []          # List[str]: danh sách nội dung đã chunk
        self.chunk_metadata = [] # List[Dict[str,str]]: metadata tương ứng cho mỗi chunk
        self.chunk_ids = []       # List[str]: chunk_id cho từng chunk

    def index(self, chunks: List[str], embeddings: List[list] = None, metadata: List[Dict[str, str]] = None, chunk_ids: List[str] = None):
        """
        Tạo chỉ mục BM25 từ danh sách chunks.
        - chunks: List[str] các văn bản nhỏ (ô nhỏ từ quá trình chunking).
        - embeddings: không được sử dụng ở BM25, nên bỏ qua.
        - metadata: danh sách metadata cho từng chunk (nếu có).
        - chunk_ids: danh sách chunk_id tương ứng (nếu có).
        """
        # Tokenize từng chunk (mặc định split khoảng trắng)
        tokenized_corpus = [chunk.split() for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

        self.chunks = chunks
        self.chunk_metadata = metadata if metadata is not None else [{} for _ in chunks]
        self.chunk_ids = chunk_ids if chunk_ids is not None else [str(i) for i in range(len(chunks))]

    def retrieve(self, query: str, top_k: int = None) -> List[RetrievalResult]:
        """
        Thực hiện truy vấn BM25, trả về top_k RetrievalResult.
        """
        if self.bm25 is None:
            raise ValueError("BM25 Retriever chưa được index. Hãy gọi index(...) trước.")

        if top_k is None:
            top_k = self.top_k

        tokenized_query = query.split()
        # Lấy scores GM25 cho mỗi chunk
        scores = self.bm25.get_scores(tokenized_query)
        # Chọn top_k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: List[RetrievalResult] = []
        for idx in top_indices:
            result = RetrievalResult(
                chunk_id=self.chunk_ids[idx],
                score=float(scores[idx]),
                content=self.chunks[idx],
                metadata=self.chunk_metadata[idx]
            )
            results.append(result)

        return results
