from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str | None = None
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    groq_api_key: str = ""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    frontend_url: str = "http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
