from generator.base_generator import BaseGenerator

class OpenAIGenerator(BaseGenerator):
    def __init__(self, model="gpt-4"):
        self.model = model

    def generate(self, query: str, contexts: list[str]) -> str:
        return f"Simulated answer to: '{query}' using {len(contexts)} context chunk(s)"
