from abc import ABC, abstractmethod
from vsvn_rag.shared.schema import EmbeddingVector

class BaseEmbedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[EmbeddingVector]:
        # embedding = model.encode(text)
        # return [EmbeddingVector(chunk_id=f"id{i}", embedding=vec) for i, vec in enumerate(embeddings)]
        pass
