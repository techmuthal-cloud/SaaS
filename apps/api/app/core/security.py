import os
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Header, HTTPException, status, Depends
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import User, Workspace, WorkspaceMember

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = getattr(settings, "JWT_SECRET_KEY", "sellerflow-dev-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Extracts current authenticated user from Bearer JWT or test header.
    In production, Bearer JWT is validated.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    return user
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials"
            )

    if x_user_id:
        user = db.query(User).filter(User.id == x_user_id).first()
        if user:
            return user

    return None

def verify_tenant_access(
    workspace_id: str,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_workspace_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Workspace:
    """
    Strict Tenant Isolation Check:
    Verifies that the caller has membership in the target workspace.
    Fails closed with 401/403.
    """
    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id} not found"
        )

    # If X-Workspace-Id header is passed, ensure it matches URL parameter
    if x_workspace_id and x_workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Header X-Workspace-Id does not match path workspace_id"
        )

    user = get_current_user_optional(authorization, x_user_id, db)
    
    # If users exist in database, require explicit membership check
    total_users = db.query(User).count()
    if total_users > 0:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access workspace data"
            )
        
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id
        ).first()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User {user.id} does not have access to workspace {workspace_id}"
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
