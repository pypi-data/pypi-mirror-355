# vsvn_rag/retriever/hybrid_retriever.py

from typing import List, Dict
import numpy as np
from vsvn_rag.retriever.base_retriever import BaseRetriever
from vsvn_rag.shared.schema import RetrievalResult
from vsvn_rag.embedder.base_embedder import BaseEmbedder

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Tính cosine similarity giữa hai vector.
    """
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

class HybridRetriever(BaseRetriever):
    """
    Triển khai thuật toán Hybrid Search:
    - Kết hợp điểm BM25 và điểm embedding similarity theo tỉ lệ alpha, 1-alpha.
    """

    def __init__(self, bm25_retriever: BaseRetriever, embedder: BaseEmbedder, alpha: float = 0.5):
        """
        bm25_retriever: instance BM25Retriever đã được index sẵn.
        embedder: instance BaseEmbedder (Offline hoặc AzureOpenAI).
        alpha: hệ số weight cho điểm BM25 (0 <= alpha <= 1).
               (1-alpha) sẽ được dùng cho điểm embedding similarity.
        """
        self.bm25_retriever = bm25_retriever
        self.embedder = embedder
        self.alpha = alpha

        # Lưu embedding cho chunks (dùng để tính cosine similarity)
        self.chunk_embeddings: Dict[str, np.ndarray] = {}
        # Lưu content và metadata cho mỗi chunk_id
        self.chunks_dict: Dict[str, Dict] = {}

        self.top_k = None

    def index(self, chunks: List[str], embeddings: List[List[float]] = None, metadata: List[Dict[str, str]] = None, chunk_ids: List[str] = None):
        """
        - Gọi index cho BM25Retriever trước.
        - Lưu embedding cho các chunk.
        """
        # 1) Index cho BM25
        self.bm25_retriever.index(chunks, embeddings, metadata, chunk_ids)

        # 2) Lưu embedding cho các chunk
        if embeddings is None:
            # Tính embedding on-the-fly
            chunk_embeddings = self.embedder.embed(chunks)
            for emb, cid, cont, meta in zip(chunk_embeddings, chunk_ids, chunks, metadata or [{}]*len(chunks)):
                self.chunk_embeddings[cid] = np.array(emb.embedding)
                self.chunks_dict[cid] = {"content": cont, "metadata": meta}
        else:
            for emb_vec, cid, cont, meta in zip(embeddings, chunk_ids, chunks, metadata or [{}]*len(chunks)):
                self.chunk_embeddings[cid] = np.array(emb_vec)
                self.chunks_dict[cid] = {"content": cont, "metadata": meta}

    def retrieve(self, query: str, top_k: int) -> List[RetrievalResult]:
        """
        Thực hiện Hybrid Search:
        1) Lấy toàn bộ kết quả BM25 (có thể lấy nhiều hơn top_k để tính sau).
        2) Tính điểm embedding similarity giữa query và các chunk.
        3) Chuẩn hóa score BM25 và cosine similarity về cùng thang (0–1).
        4) Tính điểm hỗn hợp: alpha * bm25_norm + (1 - alpha) * emb_norm.
        5) Sắp xếp theo điểm hỗn hợp và trả về top_k.
        """
        self.top_k = top_k

        # 1) Lấy tất cả kết quả BM25 (để dễ chuẩn hóa). Giả sử ta lấy top_n với n = top_k * 5 (hoặc toàn bộ nếu ít chunk).
        # Tùy vào kích thước của chỉ mục, bạn có thể lấy toàn bộ hoặc một số lượng lớn hơn top_k.
        initial_results = self.bm25_retriever.retrieve(query, top_k * 5)

        # 2) Tính embedding của query
        query_emb_list = self.embedder.embed([query])
        query_emb = np.array(query_emb_list[0].embedding)

        # 3) Lấy scores BM25 và tính cosine similarity cho từng chunk
        bm25_scores = []
        emb_scores = []
        for res in initial_results:
            cid = res.chunk_id
            bm25_scores.append(res.score)

            chunk_emb = self.chunk_embeddings.get(cid, None)
            if chunk_emb is None:
                # Nếu chưa có embedding (hiếm xảy ra), gán 0
                emb_scores.append(0.0)
            else:
                emb_scores.append(cosine_similarity(query_emb, chunk_emb))

        bm25_scores = np.array(bm25_scores, dtype=float)
        emb_scores = np.array(emb_scores, dtype=float)

        # 4) Chuẩn hóa sang thang 0–1
        def normalize(arr: np.ndarray) -> np.ndarray:
            if arr.max() == arr.min():
                return np.zeros_like(arr)
            return (arr - arr.min()) / (arr.max() - arr.min())

        bm25_norm = normalize(bm25_scores)
        emb_norm = normalize(emb_scores)

        # 5) Tính điểm hỗn hợp
        hybrid_scores = self.alpha * bm25_norm + (1 - self.alpha) * emb_norm

        # 6) Tạo danh sách RetrievalResult mới với score = hybrid_score, content/metadata giữ nguyên
        hybrid_results = []
        for idx, res in enumerate(initial_results):
            cid = res.chunk_id
            hybrid_results.append(RetrievalResult(
                chunk_id=cid,
                score=float(hybrid_scores[idx]),
                content=self.chunks_dict[cid]["content"],
                metadata=self.chunks_dict[cid]["metadata"]
            ))

        # 7) Sắp xếp theo score giảm dần và trả về top_k
        hybrid_results.sort(key=lambda x: x.score, reverse=True)
        return hybrid_results[:top_k]
