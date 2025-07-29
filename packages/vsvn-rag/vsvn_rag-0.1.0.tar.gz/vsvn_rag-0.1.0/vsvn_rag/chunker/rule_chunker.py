from chunker.base_chunker import BaseChunker

class RuleBasedChunker(BaseChunker):
    def chunk(self, document: str) -> list[str]:
        # Chunk text based on double newline (paragraph split)
        return [chunk.strip() for chunk in document.split("\n\n") if chunk.strip()]
