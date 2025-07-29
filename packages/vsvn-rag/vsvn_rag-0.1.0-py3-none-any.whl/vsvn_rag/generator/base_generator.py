from abc import ABC, abstractmethod

class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, query: str, contexts: list[str]) -> str:
        pass
