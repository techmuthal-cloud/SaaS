import os
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Header, HTTPException, status, Depends
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import User, Workspace, WorkspaceMember

KNOWN_INSECURE_PLACEHOLDERS = {
    "sellerflow-dev-secret-key-change-in-production-2026",
    "change-me-in-production-sellerflow-key-2026",
    "generate-a-strong-random-secret-key-for-production",
    "secret",
    "changeme",
    "password",
    "admin",
    "default",
    "test",
    "jwt_secret",
}

def validate_jwt_secret(secret: Optional[str]) -> str:
    """
    Validates that a deployment-provided secret exists and is not a known placeholder.
    Fails startup with RuntimeError if invalid.
    """
    if not secret or not str(secret).strip():
        raise RuntimeError(
            "FATAL: JWT_SECRET_KEY is missing. A deployment-provided secret must be supplied "
            "via the JWT_SECRET_KEY environment variable. Startup aborted."
        )
    clean_secret = str(secret).strip().lower()
    if clean_secret in KNOWN_INSECURE_PLACEHOLDERS or len(str(secret).strip()) < 16:
        raise RuntimeError(
            "FATAL: JWT_SECRET_KEY is set to an insecure known placeholder or is too short (min 16 chars). "
            "Please configure a strong, unique secret in your deployment environment."
        )
    return str(secret).strip()

def get_jwt_secret() -> str:
    return validate_jwt_secret(settings.JWT_SECRET_KEY)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    secret = get_jwt_secret()
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret, algorithm=settings.JWT_ALGORITHM)

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Enforces validated Bearer JWT authentication.
    Client-supplied identity headers (such as X-User-ID) are strictly removed and ignored.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        secret = get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing subject identifier",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account does not exist or has been deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def verify_tenant_access(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Workspace:
    """
    Strict Tenant Isolation & Workspace Authorization Check:
    1. Authenticates the caller via validated Bearer token.
    2. Verifies the target workspace exists (404 if missing).
    3. Validates X-Workspace-Id header matches URL if provided (403 if mismatched).
    4. Enforces that current_user has an active membership in the target workspace (403 if not).
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id} not found"
        )

    if x_workspace_id and x_workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Header X-Workspace-Id does not match path workspace_id"
        )

    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User {current_user.id} does not have access to workspace {workspace_id}"
        )

    return workspace

# ----------------- Security & Sanitization Helpers -----------------

ALLOWED_EXTENSIONS = {".csv", ".tsv", ".txt", ".xlsx"}
MAGIC_BYTES_PREFIXES = {
    b"PK\x03\x04": ".xlsx", # Zip/Excel
}

def sanitize_for_spreadsheet(value: Optional[str]) -> str:
    """
    Guards against CSV / Spreadsheet Formula Injection.
    Prepends single quote (') if the text starts with dangerous formula trigger characters.
    Triggers: =, +, -, @, \t, \r
    """
    if value is None:
        return ""
    str_val = str(value)
    if str_val and str_val[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{str_val}"
    return str_val

def validate_and_sanitize_upload(file_bytes: bytes, filename: str) -> str:
    """
    Validates file extension, size, and returns a secure random UUID-based storage filename.
    Never trusts client-provided file paths.
    """
    if len(file_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Check extension
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {ext}. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Safe random filename on disk (avoids path traversal entirely)
    safe_storage_name = f"{uuid.uuid4().hex}{ext}"
    return safe_storage_name
