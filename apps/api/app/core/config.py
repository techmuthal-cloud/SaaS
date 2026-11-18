from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "SellerFlow AI"
    ENVIRONMENT: str = "development" # development, test, staging, production
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

    # Clerk Authentication Configuration (Loaded from environment variables)
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_PUBLISHABLE_KEY: Optional[str] = None
    CLERK_JWKS_URL: Optional[str] = None
    CLERK_ISSUER: Optional[str] = None

    # Supabase Platform (Database & Storage - Loaded from environment variables)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "sellerflow-vault"
    STORAGE_PROVIDER: str = "supabase" # supabase, local

    # Internal Monitoring Token for /metrics endpoint
    MONITORING_SECRET_TOKEN: Optional[str] = None

    # Redis for Distributed Rate Limiting & Background Jobs
    REDIS_URL: Optional[str] = None
    TRUSTED_PROXIES: List[str] = ["127.0.0.1", "::1", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

    # Rate limiting thresholds (requests per minute)
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_REGISTER_PER_MINUTE: int = 5
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 15

    # Resend Email Configuration
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM_EMAIL: str = "notifications@sellerflow.ai"

    # PostHog Privacy-Conscious Product Telemetry
    POSTHOG_API_KEY: Optional[str] = None
    POSTHOG_HOST: str = "https://app.posthog.com"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
