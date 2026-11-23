import os
import json
import urllib.request
import urllib.error
import io
import uuid
import re
import zipfile
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from fastapi import Header, HTTPException, status, Depends, UploadFile
import jwt
from jwt import PyJWKClient, PyJWTError, ExpiredSignatureError, InvalidIssuerError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import User, Workspace, WorkspaceMember
from app.core.logging import logger

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
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now, "nbf": now})
    return jwt.encode(to_encode, secret, algorithm=settings.JWT_ALGORITHM)

_CLERK_JWK_CLIENT = None

def get_clerk_jwk_client() -> Optional[PyJWKClient]:
    global _CLERK_JWK_CLIENT
    if _CLERK_JWK_CLIENT is None and settings.CLERK_JWKS_URL:
        try:
            _CLERK_JWK_CLIENT = PyJWKClient(
                settings.CLERK_JWKS_URL,
                cache_keys=True,
                max_cached_keys=16,
                cache_jwk_set=True,
                lifespan=3600
            )
        except Exception as e:
            logger.warning(f"Could not initialize Clerk JWK client: {e}")
    return _CLERK_JWK_CLIENT

def verify_clerk_token_jwks(token: str) -> Optional[dict]:
    """
    Verifies Clerk RS256 token against Clerk JWKS validating issuer, subject, expiry and authorized party.
    Uses bounded caching and refreshes key set on unknown key ID.
    Does NOT fall back to backend symmetric secrets.
    """
    jwk_client = get_clerk_jwk_client()
    if not jwk_client:
        return None

    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        decode_options = {
            "require": ["exp", "sub"],
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
            "verify_aud": False,
        }
        issuer = settings.CLERK_ISSUER if settings.CLERK_ISSUER else None
        if settings.ENVIRONMENT == "production" and not issuer:
            raise RuntimeError("FATAL: CLERK_ISSUER is required in production environment.")

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options=decode_options
        )

        # Validate authorized party (azp) if configured
        if settings.CLERK_AUTHORIZED_PARTIES:
            azp = payload.get("azp")
            if azp and azp not in settings.CLERK_AUTHORIZED_PARTIES:
                logger.warning(f"Clerk token rejected: unauthorized azp {azp}")
                return None

        return payload
    except (ExpiredSignatureError, InvalidIssuerError, PyJWTError) as e:
        logger.debug(f"Clerk token verification rejected: {e}")
        return None
    except Exception as e:
        logger.warning(f"Clerk token verification error: {e}")
        return None

def fetch_clerk_user_email(clerk_user_id: str) -> Tuple[Optional[str], bool]:
    """
    Fetches real email address and verification status for user from Clerk Backend API.
    Returns (email_address, is_verified).
    """
    if not settings.CLERK_SECRET_KEY:
        return None, False
    try:
        url = f"https://api.clerk.com/v1/users/{clerk_user_id}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            emails = data.get("email_addresses", [])
            primary_id = data.get("primary_email_address_id")

            # Check primary email first
            for e in emails:
                if e.get("id") == primary_id:
                    addr = e.get("email_address")
                    is_verified = (e.get("verification", {}).get("status") == "verified")
                    return addr, is_verified

            # Check any verified email
            for e in emails:
                if e.get("verification", {}).get("status") == "verified":
                    return e.get("email_address"), True

            if emails:
                return emails[0].get("email_address"), False
    except Exception as e:
        logger.debug(f"Failed to fetch Clerk user email: {e}")
    return None, False

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Enforces validated Bearer JWT authentication.
    Verifies Clerk RS256 JWKS tokens in production; supports local JWT secret in test/dev.
    Client-supplied identity headers (such as X-User-ID) are strictly rejected.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    user_id: Optional[str] = None
    is_clerk_verified = False

    # 1. First attempt verification with Clerk JWKS
    clerk_payload = verify_clerk_token_jwks(token)
    if clerk_payload:
        user_id = clerk_payload.get("sub")
        is_clerk_verified = True

    # 2. Local JWT secret verification allowed only in non-production environments
    if not user_id:
        if settings.ENVIRONMENT == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Clerk authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            secret = get_jwt_secret()
            payload = jwt.decode(
                token,
                secret,
                algorithms=[settings.JWT_ALGORITHM],
                options={"require": ["sub", "exp"], "verify_exp": True}
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload: missing subject identifier",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user = db.query(User).filter((User.id == user_id) | (User.clerk_id == user_id)).first()

    # Provision user record from real Clerk profile
    if not user and is_clerk_verified:
        email_addr, is_verified = fetch_clerk_user_email(user_id)
        user_email = email_addr or f"{user_id}@unverified.clerk"
        try:
            user = User(
                id=user_id,
                clerk_id=user_id,
                email=user_email,
                full_name="Clerk Verified User" if is_verified else "Clerk User",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            user = db.query(User).filter((User.id == user_id) | (User.clerk_id == user_id)).first()

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

def require_workspace_role(allowed_roles: List[str]):
    """
    Role-Based Access Control (RBAC) dependency factory.
    Verifies that the caller possesses one of the allowed roles (e.g. 'owner', 'admin', 'accountant').
    """
    def role_dependency(
        workspace_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> WorkspaceMember:
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        ).first()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User {current_user.id} is not a member of workspace {workspace_id}"
            )

        if member.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: Role '{member.role}' cannot perform this action (requires: {', '.join(allowed_roles)})"
            )

        return member

    return role_dependency

# ----------------- Security & Sanitization Helpers -----------------

ALLOWED_EXTENSIONS = {".csv", ".tsv", ".txt", ".xlsx"}
MAGIC_BYTES_ZIP = b"PK\x03\x04"
MAGIC_BYTES_EXE = b"MZ"
MAGIC_BYTES_ELF = b"\x7fELF"

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

async def read_upload_stream_safely(
    file: UploadFile,
    max_bytes: int = settings.MAX_FILE_SIZE_MB * 1024 * 1024,
    chunk_size: int = 64 * 1024
) -> bytes:
    """
    Streams upload chunks into memory with strict size limit enforcement during reading,
    preventing denial-of-service through memory exhaustion.
    """
    total_bytes = 0
    buffer = bytearray()

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size limit of {settings.MAX_FILE_SIZE_MB}MB"
            )
        buffer.extend(chunk)

    return bytes(buffer)

def validate_and_sanitize_upload(file_bytes: bytes, filename: str) -> str:
    """
    Validates file extension, magic bytes, text/zip integrity, and returns a secure random UUID storage name.
    Neutralizes path traversal attempts.
    """
    if not filename or not filename.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File name cannot be empty")

    _, ext = os.path.splitext(filename.lower().strip())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {ext}. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Empty file check
    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty (0 bytes)")

    # Content & Magic-Byte Validation
    if ext == ".xlsx":
        if not file_bytes.startswith(MAGIC_BYTES_ZIP):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid XLSX file: Missing valid Zip archive signature (mismatched extension)"
            )
        # Validate Zip structure and check against decompression bombs
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
                info_list = zf.infolist()
                sheet_count = sum(1 for item in info_list if "xl/worksheets/sheet" in item.filename)
                if sheet_count > settings.MAX_XLSX_SHEETS:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"XLSX file exceeds maximum allowed sheet count ({settings.MAX_XLSX_SHEETS})"
                    )

                total_uncompressed = 0
                max_uncompressed = settings.MAX_XLSX_UNCOMPRESSED_MB * 1024 * 1024
                for item in info_list:
                    total_uncompressed += item.file_size
                    if total_uncompressed > max_uncompressed:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="XLSX expansion size exceeds maximum allowed decompression limit"
                        )
                    # Check suspicious compression ratio
                    if item.compress_size > 0 and (item.file_size / item.compress_size) > 100:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Suspicious archive compression ratio detected"
                        )
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid XLSX file: Corrupted or unreadable Zip archive structure"
            )
    else:
        # CSV / TSV / TXT
        # Reject binary executables disguised as text
        if file_bytes.startswith(MAGIC_BYTES_ZIP) or file_bytes.startswith(MAGIC_BYTES_EXE) or file_bytes.startswith(MAGIC_BYTES_ELF):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid text report: Binary file signature detected"
            )
        # Check first 4KB for null bytes indicating binary content
        sample = file_bytes[:4096]
        if b"\x00" in sample:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report content: Binary null bytes detected in text file"
            )

    # Safe random filename on disk (avoids path traversal entirely)
    safe_storage_name = f"{uuid.uuid4().hex}{ext}"
    return safe_storage_name

def safe_cleanup_file(file_path: Optional[str]):
    """
    Safely cleans up temporary or aborted upload files on disk.
    """
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Cleaned up temporary upload file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove upload file {file_path}: {e}")
