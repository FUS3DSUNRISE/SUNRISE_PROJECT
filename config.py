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
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_MODEL = "llama-3.3-70b-versatile"

    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False

    POWERBI_EXPORT_TOKEN = "dev-powerbi-token-123"

    LLM_SYSTEM_PROMPT_PATH = os.getenv(
        "LLM_SYSTEM_PROMPT_PATH",
        os.path.join(BASE_DIR, "app", "prompts", "system_prompt.txt")
    )

    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))