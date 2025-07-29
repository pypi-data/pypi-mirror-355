from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

# Kết nối đến Qdrant đang chạy trên localhost
client = QdrantClient(url="http://localhost:6333")

# Tạo một collection mới (nếu chưa có)
client.create_collection(
    collection_name="my_collection",
    vectors_config=VectorParams(
        size=300,  # Kích thước vector (thí dụ là 300 chiều)
        distance=Distance.COSINE  # Chọn khoảng cách cosine
    )
)