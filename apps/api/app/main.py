from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import RequestIDMiddleware, logger
from app.core.security import validate_jwt_secret
from app.routes.api_v1 import router as api_v1_router

# Ensure tables are created in development/SQLite
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Accountant-Grade Financial Intelligence & Multi-Marketplace Reconciliation for Indian E-Commerce",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request ID tracing middleware
app.add_middleware(RequestIDMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

@app.on_event("startup")
async def startup_event():
    # Require deployment-provided secret and fail startup if missing or a known placeholder
    validate_jwt_secret(settings.JWT_SECRET_KEY)
    logger.info("SellerFlow AI backend service initialized with tenant isolation and deterministic reconciliation.")

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": "2.0.0",
        "documentation": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }
