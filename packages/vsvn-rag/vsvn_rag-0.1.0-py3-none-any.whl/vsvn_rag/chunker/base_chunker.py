from abc import ABC, abstractmethod
from shared.schema import DocumentChunk

class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, document: str) -> list[DocumentChunk]:
        # return list of DocumentChunk
        pass
