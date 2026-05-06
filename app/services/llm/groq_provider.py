from app.services.llm.base_provider import BaseLLMProvider
from langchain_openai import ChatOpenAI
import config


class GroqProvider(BaseLLMProvider):
    def __init__(self):
        self.base_url = (
            getattr(config, "LLM_BASE_URL", None)
            or getattr(config.Config, "LLM_BASE_URL")
        )

        self.api_key = (
            getattr(config, "LLM_API_KEY", None)
            or getattr(config.Config, "LLM_API_KEY")
        )

        self.model = (
            getattr(config, "LLM_MODEL", None)
            or getattr(config.Config, "LLM_MODEL")
        )

        self.temperature = (
            getattr(config, "LLM_TEMPERATURE", None)
            or getattr(config.Config, "LLM_TEMPERATURE", 0.2)
        )

        self.client = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
        )

    def generate(self, system_prompt: str, human_prompt: str) -> str:
        response = self.client.invoke([
            ("system", system_prompt),
            ("human", human_prompt),
        ])

        return response.content
    
    
    def get_config_summary(self) -> dict:
        return {
            "provider": "groq",
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "api_key_configured": bool(self.api_key),
        }