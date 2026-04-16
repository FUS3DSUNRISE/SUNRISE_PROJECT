class Config:
    DEBUG = True
    SECRET_KEY = "BIP-scailab"

    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

    LLM_BASE_URL = "https://api.groq.com/openai/v1"
    LLM_API_KEY = "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"
    LLM_MODEL = "llama-3.3-70b-versatile"

    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False