import config
from app.services.llm.groq_provider import GroqProvider


class LLMService:
    def __init__(self):
        provider_name = getattr(config.Config, "LLM_PROVIDER", "groq").lower()

        if provider_name == "groq":
            self.provider = GroqProvider()

    #   elif provider_name == "...":
    
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

    def generate(self, system_prompt: str, human_prompt: str) -> str:
        return self.provider.generate(system_prompt, human_prompt)

    def get_config_summary(self) -> dict:
        return self.provider.get_config_summary()