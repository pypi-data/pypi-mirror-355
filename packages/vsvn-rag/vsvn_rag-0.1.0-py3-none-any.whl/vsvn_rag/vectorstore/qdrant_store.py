# project_root/vector_store/qdrant_vector_store.py

from typing import List, Optional, Dict, Any
from uuid import uuid4  # Thêm import này để tạo UUID nếu cần
from .base_vector_store import BaseVectorStore

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        VectorParams,
        Distance,
        PointStruct,
        Filter,
        ScoredPoint,
    )
except ImportError:
    QdrantClient = None


class QdrantVectorStore(BaseVectorStore):
    """
    Vector Store cài đặt với Qdrant. Dùng qdrant-client để kết nối, upsert và search.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        prefer_grpc: bool = False,
        index_name: str = "default_collection",
        dimension: int = 1536,
        distance: str = "Cosine",
    ):
        if QdrantClient is None:
            raise ImportError(
                "Cần cài đặt qdrant-client (pip install qdrant-client) để dùng QdrantVectorStore."
            )

        self.index_name = index_name
        self.dimension = dimension

        try:
            distance_enum = Distance[distance.upper()]
        except KeyError:
            raise ValueError(
                f"Unsupported distance metric: {distance}. "
                f"Hãy dùng một trong {[d.name for d in Distance]}."
            )

        self.distance = distance_enum

        self.client = QdrantClient(
            url=f"http://{host}:{port}",
            prefer_grpc=prefer_grpc,
            api_key=api_key,
        )

        try:
            self.client.delete_collection(collection_name=self.index_name)
        except Exception:
            pass

        self.client.create_collection(
            collection_name=self.index_name,
            vectors_config=VectorParams(
                size=self.dimension,
                distance=self.distance,
            ),
        )

    def add_embeddings(
        self,
        vectors: List,
        payloads: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Nhận vào một danh sách các object `vec` (có thuộc tính vec.chunk_id và vec.embedding),
        và optional payloads tương ứng, rồi upsert vào Qdrant.
        """
        points: List[PointStruct] = []
        for idx, vec in enumerate(vectors):
            # Chuyển đổi chunk_id thành số nguyên nếu cần
            try:
                point_id = int(vec.chunk_id)  # Thử chuyển thành int
            except (ValueError, TypeError):
                # Nếu không chuyển được thành int, tạo UUID từ chunk_id
                point_id = str(uuid4())  # Hoặc có thể dùng cách khác để tạo ID hợp lệ

            payload = payloads[idx] if (payloads is not None and idx < len(payloads)) else {}
            p = PointStruct(
                id=point_id,  # Sử dụng point_id đã được chuyển đổi
                vector=vec.embedding,
                payload=payload,
            )
            points.append(p)

        self.client.upsert(collection_name=self.index_name, points=points)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[ScoredPoint]:
        """
        Tìm kiếm top_k điểm tương tự trong Qdrant dựa trên query_vector và optional filter.
        """
        if filter is not None:
            qdrant_filter = Filter(**filter)
        else:
            qdrant_filter = None

        results = self.client.search(
            collection_name=self.index_name,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            query_filter=qdrant_filter,
        )
        return results