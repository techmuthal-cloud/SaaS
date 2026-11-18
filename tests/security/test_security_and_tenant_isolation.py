import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.core.security import (
    sanitize_for_spreadsheet,
    validate_and_sanitize_upload,
    validate_jwt_secret,
    create_access_token
)
from app.models.entities import Workspace, User, WorkspaceMember
from app.core.database import SessionLocal

client = TestClient(app)

# ----------------- Secret & Placeholder Handling Tests -----------------

def test_missing_jwt_secret_fails():
    with pytest.raises(RuntimeError) as exc_info:
        validate_jwt_secret(None)
    assert "FATAL: JWT_SECRET_KEY is missing" in str(exc_info.value)

    with pytest.raises(RuntimeError) as exc_info:
        validate_jwt_secret("   ")
    assert "FATAL: JWT_SECRET_KEY is missing" in str(exc_info.value)

def test_known_placeholder_secrets_fail():
    placeholders = [
        "sellerflow-dev-secret-key-change-in-production-2026",
        "change-me-in-production-sellerflow-key-2026",
        "generate-a-strong-random-secret-key-for-production",
        "secret",
        "changeme",
        "password",
        "admin",
        "default",
        "test",
    ]
    for ph in placeholders:
        with pytest.raises(RuntimeError) as exc_info:
            validate_jwt_secret(ph)
        assert "FATAL: JWT_SECRET_KEY is set to an insecure known placeholder" in str(exc_info.value)

def test_short_jwt_secret_fails():
    with pytest.raises(RuntimeError) as exc_info:
        validate_jwt_secret("short-key")
    assert "too short" in str(exc_info.value)

def test_valid_deployment_secret_succeeds():
    valid = "my-secure-production-ready-secret-key-2026-xyz"
    assert validate_jwt_secret(valid) == valid

# ----------------- API-Level Authentication & Authorization Tests -----------------

def test_unauthenticated_requests_rejected_with_401():
    """All protected routes must return 401 when called without Authorization header."""
    assert client.get("/api/v1/workspaces").status_code == 401
    assert client.post("/api/v1/workspaces", data={"name": "NoAuth Corp"}).status_code == 401
    assert client.get("/api/v1/workspaces/random-id/stores").status_code == 401
    assert client.get("/api/v1/workspaces/random-id/discrepancies").status_code == 401
    assert client.get("/api/v1/workspaces/random-id/waterfall").status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401

def test_forged_x_user_id_header_is_rejected_with_401():
    """
    CRITICAL SECURITY CHECK:
    Client-supplied identity headers like X-User-ID MUST NOT be accepted as authentication.
    Requests without a validated Bearer token must return 401.
    """
    db = SessionLocal()
    try:
        user = User(email=f"victim_{uuid.uuid4().hex[:6]}@example.com", hashed_password="xyz")
        db.add(user)
        db.commit()
        db.refresh(user)
        victim_id = user.id
    finally:
        db.close()

    # Attempt forged identity via header
    res1 = client.get("/api/v1/workspaces", headers={"X-User-ID": victim_id})
    assert res1.status_code == 401
    assert "Authentication required" in res1.json()["detail"]

    res2 = client.post("/api/v1/workspaces", data={"name": "Hacked WS"}, headers={"X-User-ID": victim_id})
    assert res2.status_code == 401

    res3 = client.get(f"/api/v1/workspaces/random-id/stores", headers={"X-User-ID": victim_id})
    assert res3.status_code == 401

def test_forged_bearer_token_rejected_with_401():
    """Invalid or forged JWT tokens must be rejected with 401."""
    res = client.get(
        "/api/v1/workspaces",
        headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.fake_signature"}
    )
    assert res.status_code == 401
    assert "Invalid or expired" in res.json()["detail"]

def test_two_users_cross_tenant_access_denied_with_403():
    """
    CRITICAL SECURITY INVARIANT:
    User A cannot access User B's workspace data. Must return 403 Forbidden.
    """
    # 1. Register User A
    email_a = f"alice_{uuid.uuid4().hex[:6]}@example.com"
    res_a = client.post("/api/v1/auth/register", json={
        "email": email_a,
        "password": "Password123!",
        "full_name": "Alice Seller",
        "workspace_name": "Alice Retail"
    })
    assert res_a.status_code == 200
    token_a = res_a.json()["access_token"]
    ws_a_id = res_a.json()["workspace"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    email_b = f"bob_{uuid.uuid4().hex[:6]}@example.com"
    res_b = client.post("/api/v1/auth/register", json={
        "email": email_b,
        "password": "Password123!",
        "full_name": "Bob Seller",
        "workspace_name": "Bob Logistics"
    })
    assert res_b.status_code == 200
    token_b = res_b.json()["access_token"]
    ws_b_id = res_b.json()["workspace"]["id"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A accessing their own workspace -> SUCCEEDS (200)
    assert client.get(f"/api/v1/workspaces/{ws_a_id}/stores", headers=headers_a).status_code == 200
    assert client.get(f"/api/v1/workspaces/{ws_a_id}/discrepancies", headers=headers_a).status_code == 200

    # 4. User B accessing their own workspace -> SUCCEEDS (200)
    assert client.get(f"/api/v1/workspaces/{ws_b_id}/stores", headers=headers_b).status_code == 200
    assert client.get(f"/api/v1/workspaces/{ws_b_id}/discrepancies", headers=headers_b).status_code == 200

    # 5. User A attempting to access User B's workspace -> MUST BE 403 FORBIDDEN
    cross_res_1 = client.get(f"/api/v1/workspaces/{ws_b_id}/stores", headers=headers_a)
    assert cross_res_1.status_code == 403
    assert "Access denied" in cross_res_1.json()["detail"]

    cross_res_2 = client.get(f"/api/v1/workspaces/{ws_b_id}/discrepancies", headers=headers_a)
    assert cross_res_2.status_code == 403
    assert "Access denied" in cross_res_2.json()["detail"]

    cross_res_3 = client.get(f"/api/v1/workspaces/{ws_b_id}/waterfall", headers=headers_a)
    assert cross_res_3.status_code == 403

    # 6. User B attempting to access User A's workspace -> MUST BE 403 FORBIDDEN
    cross_res_4 = client.get(f"/api/v1/workspaces/{ws_a_id}/stores", headers=headers_b)
    assert cross_res_4.status_code == 403
    assert "Access denied" in cross_res_4.json()["detail"]

def test_workspace_listing_scoped_strictly_to_membership():
    """Users must only see workspaces where they are members."""
    # Register User C
    email_c = f"carol_{uuid.uuid4().hex[:6]}@example.com"
    res_c = client.post("/api/v1/auth/register", json={
        "email": email_c,
        "password": "Password123!",
        "workspace_name": "Carol Boutique"
    })
    token_c = res_c.json()["access_token"]
    ws_c_id = res_c.json()["workspace"]["id"]
    headers_c = {"Authorization": f"Bearer {token_c}"}

    # Register User D
    email_d = f"dave_{uuid.uuid4().hex[:6]}@example.com"
    res_d = client.post("/api/v1/auth/register", json={
        "email": email_d,
        "password": "Password123!",
        "workspace_name": "Dave Electronics"
    })
    token_d = res_d.json()["access_token"]
    ws_d_id = res_d.json()["workspace"]["id"]
    headers_d = {"Authorization": f"Bearer {token_d}"}

    # User C listing workspaces: must only see Carol Boutique
    list_c = client.get("/api/v1/workspaces", headers=headers_c).json()
    c_ids = [w["id"] for w in list_c]
    assert ws_c_id in c_ids
    assert ws_d_id not in c_ids

    # User D listing workspaces: must only see Dave Electronics
    list_d = client.get("/api/v1/workspaces", headers=headers_d).json()
    d_ids = [w["id"] for w in list_d]
    assert ws_d_id in d_ids
    assert ws_c_id not in d_ids

def test_workspace_creation_assigns_owner_atomically():
    """Creating a workspace requires auth and atomically assigns caller as owner."""
    email_e = f"eve_{uuid.uuid4().hex[:6]}@example.com"
    res_e = client.post("/api/v1/auth/register", json={
        "email": email_e,
        "password": "Password123!",
        "workspace_name": "Eve Primary"
    })
    token_e = res_e.json()["access_token"]
    headers_e = {"Authorization": f"Bearer {token_e}"}

    # Eve creates a second workspace
    create_res = client.post("/api/v1/workspaces", data={"name": "Eve Second Venture"}, headers=headers_e)
    assert create_res.status_code == 200
    new_ws = create_res.json()
    assert new_ws["name"] == "Eve Second Venture"
    assert new_ws["role"] == "owner"

    # Verify Eve can list both workspaces
    eve_workspaces = client.get("/api/v1/workspaces", headers=headers_e).json()
    assert len(eve_workspaces) == 2
    for w in eve_workspaces:
        assert w["role"] == "owner"

# ----------------- Sanitization & File Upload Tests -----------------

def test_csv_formula_injection_sanitization():
    """Ensure dangerous formula injection characters (=, +, -, @, tab, cr) are prepended with single quote."""
    assert sanitize_for_spreadsheet("=1+1") == "'=1+1"
    assert sanitize_for_spreadsheet("+cmd|'/c calc'!A1") == "'+cmd|'/c calc'!A1"
    assert sanitize_for_spreadsheet("-5+2") == "'-5+2"
    assert sanitize_for_spreadsheet("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_for_spreadsheet("\tTAB_INJECT") == "'\tTAB_INJECT"
    assert sanitize_for_spreadsheet("OD402-1234567") == "OD402-1234567"
    assert sanitize_for_spreadsheet("SKU-CHAIR-01") == "SKU-CHAIR-01"
    assert sanitize_for_spreadsheet("1500.00") == "1500.00"

def test_path_traversal_upload_defense():
    """Ensure malicious user filenames with directory traversal are neutralized to safe UUIDs."""
    malicious_filename = "../../../../../etc/passwd.csv"
    safe_name = validate_and_sanitize_upload(b"order_id,amount\nOD1,100", malicious_filename)
    assert ".." not in safe_name
    assert "/" not in safe_name
    assert "\\" not in safe_name
    assert safe_name.endswith(".csv")

def test_unsupported_file_extension_rejected():
    with pytest.raises(HTTPException) as exc_info:
        validate_and_sanitize_upload(b"malicious executable", "payload.exe")
    assert exc_info.value.status_code == 400
    assert "Unsupported file format" in exc_info.value.detail
