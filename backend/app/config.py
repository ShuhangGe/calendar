import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./calendar_assistant.db"
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Services
    openai_api_key: str = ""
    push_notification_key: Optional[str] = None
    
    # Long-term Memory Configuration
    fact_encryption_key: str = "your-fact-encryption-key-change-this"
    chroma_persist_directory: str = "./chroma_db"
    embedding_model: str = "text-embedding-ada-002"
    vector_similarity_threshold: float = 0.6
    max_relevant_facts: int = 10
    
    # Environment
    environment: str = "development"
    
    # App settings
    app_name: str = "Calendar Assistant"
    version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings() 