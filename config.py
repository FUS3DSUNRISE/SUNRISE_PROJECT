import os
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    DEBUG = True

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-key-123")

    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

    LLM_BASE_URL = "https://api.groq.com/openai/v1"
    LLM_API_KEY = "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"
    LLM_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False

    POWERBI_EXPORT_TOKEN = "dev-powerbi-token-123"

    LLM_SYSTEM_PROMPT_PATH = os.getenv(
        "LLM_SYSTEM_PROMPT_PATH",
        os.path.join(BASE_DIR, "app", "prompts", "system_prompt.txt")
    )

    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")