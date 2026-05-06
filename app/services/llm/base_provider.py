class BaseLLMProvider:
    def generate(self, system_prompt: str, human_prompt: str) -> str:
        raise NotImplementedError("LLM providers must implement generate()")