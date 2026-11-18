from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "SellerFlow AI"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./sellerflow.db"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001"
    ]
    STORAGE_DIR: str = "./storage/uploads"
    MAX_FILE_SIZE_MB: int = 25
    FREE_TIER_MONTHLY_ORDER_LIMIT: int = 10000

    # Secret configuration: deployment must provide via environment variable
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
