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
    MAX_UPLOAD_ROWS: int = 50000
    MAX_XLSX_UNCOMPRESSED_MB: int = 100
    MAX_XLSX_SHEETS: int = 20
    FREE_TIER_MONTHLY_ORDER_LIMIT: int = 10000

    # Secret configuration: deployment must provide via environment variable
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Internal Monitoring Token for /metrics endpoint
    MONITORING_SECRET_TOKEN: Optional[str] = None

    # Rate limiting thresholds (requests per minute)
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_REGISTER_PER_MINUTE: int = 5
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 15

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
