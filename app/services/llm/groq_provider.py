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

        self.top_p = (
            getattr(config, "LLM_TOP_P", None)
            or getattr(config.Config, "LLM_TOP_P", 0.9)
        )

        self.max_tokens = (
            getattr(config, "LLM_MAX_TOKENS", None)
            or getattr(config.Config, "LLM_MAX_TOKENS", 2048)
        )

        self.client = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            model_kwargs={
                "top_p": self.top_p,
            },
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
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "api_key_configured": bool(self.api_key),
        }