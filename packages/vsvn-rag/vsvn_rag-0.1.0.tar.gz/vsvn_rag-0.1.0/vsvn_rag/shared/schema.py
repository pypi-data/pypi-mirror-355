from dataclasses import dataclass
from typing import List, Dict

@dataclass
class DocumentChunk:
    id: str
    document_id: str
    content: str
    metadata: Dict[str, str]

@dataclass
class EmbeddingVector:
    chunk_id: str
    embedding: List[float]

@dataclass
class RetrievalResult:
    chunk_id: str
    score: float
    content: str
    metadata: Dict[str, str]
