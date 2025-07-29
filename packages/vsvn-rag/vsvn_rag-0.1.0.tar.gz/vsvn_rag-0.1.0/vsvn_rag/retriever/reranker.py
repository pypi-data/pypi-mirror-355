# vsvn_rag/retriever/rerank_retriever.py

from typing import List, Dict
import numpy as np
from vsvn_rag.retriever.base_retriever import BaseRetriever
from vsvn_rag.shared.schema import RetrievalResult
from vsvn_rag.embedder.base_embedder import BaseEmbedder  # Interface chung embedder

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Tính cosine similarity giữa hai vector.
    """
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

class RerankRetriever(BaseRetriever):
    """
    Triển khai thuật toán Rerank:
    - Dùng một BaseRetriever phụ trợ (ví dụ BM25) để lấy top_m kết quả ban đầu.
    - Tính embedding cho query và cho nội dung các chunk (nếu chưa có embedding).
    - Tính điểm cosine similarity và sắp xếp lại thứ tự dựa trên điểm này.
    """

    def __init__(self, base_retriever: BaseRetriever, embedder: BaseEmbedder, top_m: int = 20):
        """
        base_retriever: một instance của BaseRetriever (ví dụ BM25Retriever).
        embedder: một instance của BaseEmbedder (OfflineEmbedder hoặc OpenAIEmbedder).
        top_m: số lượng kết quả ban đầu do base_retriever trả về để rerank (>= top_k).
        """
        self.base_retriever = base_retriever
        self.embedder = embedder
        self.top_m = top_m

        # Lưu trữ embedding cho chunks (nếu có): {chunk_id: embedding_vector}
        self.chunk_embeddings: Dict[str, np.ndarray] = {}
        # Lưu trữ content và metadata cho chunk_id (để có thể build RetrievalResult sau)
        self.chunks_dict: Dict[str, Dict] = {}

        # top_k mặc định sẽ lấy từ cấu hình ở retrieve()
        self.top_k = None

    def index(self, chunks: List[str], embeddings: List[List[float]] = None, metadata: List[Dict[str, str]] = None, chunk_ids: List[str] = None):
        """
        - Gọi index của base_retriever (ví dụ BM25) trước.
        - Lưu embedding chunks trong self.chunk_embeddings để tính cosine similarity sau này.
        """
        # 1) Index vào base_retriever (chỉ index văn bản, BM25 không cần embeddings)
        self.base_retriever.index(chunks, embeddings, metadata, chunk_ids)

        # 2) Lưu embedding chunks vào dict
        if embeddings is None:
            # Nếu không có embeddings truyền vào, ta cần tính on-the-fly:
            # Tính embedding for all chunks
            chunk_embeddings = self.embedder.embed(chunks)
            for emb, cid, cont, meta in zip(chunk_embeddings, chunk_ids, chunks, metadata or [{}]*len(chunks)):
                self.chunk_embeddings[cid] = np.array(emb.embedding)
                self.chunks_dict[cid] = {"content": cont, "metadata": meta}
        else:
            for emb_vec, cid, cont, meta in zip(embeddings, chunk_ids, chunks, metadata or [{}]*len(chunks)):
                # emb_vec ở đây có thể là List[float]
                self.chunk_embeddings[cid] = np.array(emb_vec)
                self.chunks_dict[cid] = {"content": cont, "metadata": meta}

    def retrieve(self, query: str, top_k: int) -> List[RetrievalResult]:
        """
        Thực hiện retrieve theo 2 bước:
        1) Lấy top_m kết quả ban đầu từ base_retriever.
        2) Tính cosine similarity giữa embedding(query) và embedding(chunk).
        3) Sắp xếp lại theo cosine similarity và lấy top_k cuối cùng.
        """
        self.top_k = top_k

        # 1) Lấy top_m từ base_retriever
        initial_results = self.base_retriever.retrieve(query, self.top_m)

        # 2) Tính embedding của query
        query_emb_list = self.embedder.embed([query])
        query_emb = np.array(query_emb_list[0].embedding)

        # 3) Tính cosine similarity cho mỗi chunk trong initial_results
        rerank_results: List[RetrievalResult] = []
        for res in initial_results:
            cid = res.chunk_id
            if cid not in self.chunk_embeddings:
                # Nếu chưa có embedding cho cid (điều này hiếm xảy ra nếu index hợp lệ).
                continue
            chunk_emb = self.chunk_embeddings[cid]
            sim_score = cosine_similarity(query_emb, chunk_emb)
            # Tạo một RetrievalResult mới với score = sim_score
            new_res = RetrievalResult(
                chunk_id=cid,
                score=sim_score,
                content=self.chunks_dict[cid]["content"],
                metadata=self.chunks_dict[cid]["metadata"]
            )
            rerank_results.append(new_res)

        # 4) Sắp xếp theo score (cosine) giảm dần
        rerank_results.sort(key=lambda x: x.score, reverse=True)

        # 5) Trả về top_k
        return rerank_results[:top_k]
