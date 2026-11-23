import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.core.config import settings
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

# ----------------- Part 2: Upload Hardening & Content Validation Tests -----------------

def test_mismatched_xlsx_content_rejected():
    """An XLSX file without PK zip magic bytes must be rejected with 400."""
    with pytest.raises(HTTPException) as exc_info:
        validate_and_sanitize_upload(b"Plain text data instead of zip archive", "fake.xlsx")
    assert exc_info.value.status_code == 400
    assert "Missing valid Zip archive signature" in exc_info.value.detail

def test_binary_content_in_csv_rejected():
    """A CSV file with binary null bytes must be rejected with 400."""
    with pytest.raises(HTTPException) as exc_info:
        validate_and_sanitize_upload(b"order_id,amount\x00\x01\x02binarypayload", "fake.csv")
    assert exc_info.value.status_code == 400
    assert "Binary null bytes detected" in exc_info.value.detail

def test_malformed_xlsx_corrupted_zip_rejected():
    """A corrupted zip archive with .xlsx extension must be rejected with 400."""
    corrupt_zip = b"PK\x03\x04" + b"invalid_corrupted_payload" * 10
    with pytest.raises(HTTPException) as exc_info:
        validate_and_sanitize_upload(corrupt_zip, "corrupt.xlsx")
    assert exc_info.value.status_code == 400
    assert "Corrupted or unreadable Zip archive structure" in exc_info.value.detail

def test_oversized_file_upload_rejected():
    """Enforce size limits while reading before full buffering."""
    # Register user
    email = f"uploader_{uuid.uuid4().hex[:6]}@example.com"
    reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
    token = reg.json()["access_token"]
    ws_id = reg.json()["workspace"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate content larger than 25MB (26MB)
    oversized_bytes = b"0" * (26 * 1024 * 1024)
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/imports",
        headers=headers,
        files={"file": ("huge_file.csv", oversized_bytes, "text/csv")}
    )
    assert res.status_code == 413
    assert "exceeds maximum allowed size limit" in res.json()["detail"]

def test_failed_upload_cleans_up_storage_file():
    """Verify that when an upload fails validation or parsing, no orphan file remains on disk."""
    import os
    from app.core.config import settings

    email = f"clean_{uuid.uuid4().hex[:6]}@example.com"
    reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
    token = reg.json()["access_token"]
    ws_id = reg.json()["workspace"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload mismatched file
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/imports",
        headers=headers,
        files={"file": ("corrupt.xlsx", b"not-a-valid-zip-file", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert res.status_code == 400

    # Verify no orphan files left in workspace upload directory
    ws_dir = os.path.join(settings.STORAGE_DIR, ws_id)
    if os.path.exists(ws_dir):
        files_in_dir = os.listdir(ws_dir)
        assert len(files_in_dir) == 0, f"Expected 0 files after cleanup, found {files_in_dir}"

# ----------------- Part 2: Readiness & Restricted Metrics Tests -----------------

def test_readiness_probe_database_success():
    """Readiness probe returns 200 when database connectivity is operational."""
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

def test_readiness_probe_reports_database_failure():
    """Readiness probe returns 503 Service Unavailable when database fails."""
    from app.main import app
    from app.core.database import get_db

    # Mock broken database session
    def broken_db():
        class BrokenSession:
            def execute(self, *args, **kwargs):
                raise RuntimeError("Database connection pool exhausted")
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    try:
        res = client.get("/api/v1/health/ready")
        assert res.status_code == 503
        data = res.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
    finally:
        app.dependency_overrides.pop(get_db, None)

def test_metrics_endpoint_access_control():
    """Metrics endpoint must be restricted to authorized operators."""
    # 1. Unauthenticated request without monitoring token must be rejected with 403
    unauth_res = client.get("/api/v1/metrics")
    assert unauth_res.status_code == 403
    assert "restricted to authorized operators" in unauth_res.json()["detail"]

    # 2. Invalid monitoring token rejected with 403
    fake_res = client.get("/api/v1/metrics", headers={"X-Monitoring-Token": "invalid-token"})
    assert fake_res.status_code == 403

    # 3. Valid operator monitoring token accepted with 200
    valid_res = client.get("/api/v1/metrics", headers={"X-Monitoring-Token": "sellerflow-test-monitoring-token-2026-xyz"})
    assert valid_res.status_code == 200
    data = valid_res.json()
    assert "workspaces_count" in data
    assert "total_imports" in data

# ----------------- Part 2: Tenant-Scoped Uploads & Exports -----------------

def test_tenant_scoped_upload_access_denied():
    """User A cannot upload files into User B's workspace."""
    # Register User A
    reg_a = client.post("/api/v1/auth/register", json={"email": f"a_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    reg_b = client.post("/api/v1/auth/register", json={"email": f"b_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    ws_b_id = reg_b.json()["workspace"]["id"]

    # User A tries to upload to User B's workspace -> MUST BE 403
    res = client.post(
        f"/api/v1/workspaces/{ws_b_id}/imports",
        headers=headers_a,
        files={"file": ("test.csv", b"order_id,amount\nOD1,100", "text/csv")}
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_tenant_scoped_export_access_denied():
    """User A cannot export User B's dispute manifest or Tally XML."""
    reg_a = client.post("/api/v1/auth/register", json={"email": f"ea_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = client.post("/api/v1/auth/register", json={"email": f"eb_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    ws_b_id = reg_b.json()["workspace"]["id"]

    # User A attempts to export User B's batch dispute manifest
    res1 = client.get(f"/api/v1/workspaces/{ws_b_id}/discrepancies/batch-manifest", headers=headers_a)
    assert res1.status_code == 403
    assert "Access denied" in res1.json()["detail"]

    # User A attempts to export User B's Tally DayBook XML
    res2 = client.get(f"/api/v1/workspaces/{ws_b_id}/export-tally", headers=headers_a)
    assert res2.status_code == 403
    assert "Access denied" in res2.json()["detail"]

# ----------------- Part 2: Rate Limiting Tests -----------------

def test_rate_limiter_throttles_burst_requests():
    """Verify in-memory sliding-window rate limiter blocks brute-force abuse with 429."""
    from app.core.rate_limiter import limiter
    limiter.reset()

    # Perform rapid login attempts
    responses = []
    for _ in range(15):
        r = client.post("/api/v1/auth/login", json={"email": "nonexistent@example.com", "password": "wrong"})
        responses.append(r.status_code)

    # First 10 attempts allowed (401 invalid creds), subsequent attempts throttled with 429
    assert 429 in responses
    throttled = [code for code in responses if code == 429]
    assert len(throttled) > 0

# ----------------- Production Hardening & Anti-Fabrication Tests -----------------

def test_invalid_store_id_rejected_on_upload():
    """Verify that passing a store_id not belonging to the workspace returns 400 Bad Request."""
    reg = client.post("/api/v1/auth/register", json={"email": f"store_test_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token = reg.json()["access_token"]
    ws_id = reg.json()["workspace"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload with a bogus store_id
    res = client.post(
        f"/api/v1/workspaces/{ws_id}/imports",
        headers=headers,
        data={"store_id": "bogus-store-id-999", "marketplace": "amazon_in", "report_type": "settlement"},
        files={"file": ("test.csv", b"order_id,amount\nOD1,100", "text/csv")}
    )
    assert res.status_code == 400
    assert "does not belong to authorized workspace" in res.json()["detail"]

def test_viewer_role_rejected_from_uploading():
    """Verify that a workspace member with 'viewer' role is rejected from uploading reports with 403."""
    db = SessionLocal()
    try:
        # Create user with viewer role in workspace
        viewer_user = User(email=f"viewer_{uuid.uuid4().hex[:6]}@example.com", is_active=True)
        db.add(viewer_user)
        ws = Workspace(name="Viewer Test Workspace")
        db.add(ws)
        db.commit()

        member = WorkspaceMember(workspace_id=ws.id, user_id=viewer_user.id, role="viewer")
        db.add(member)
        db.commit()

        token = create_access_token({"sub": viewer_user.id})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.post(
            f"/api/v1/workspaces/{ws.id}/imports",
            headers=headers,
            files={"file": ("test.csv", b"order_id,amount\nOD1,100", "text/csv")}
        )
        assert res.status_code == 403
        assert "Viewer role is not authorized" in res.json()["detail"]
    finally:
        db.close()

def test_tax_reconciliation_zero_sales_does_not_fabricate_amounts():
    """Verify tax reconciliation returns 0.00 and no_transactions status, NEVER fabricating 150000.00."""
    reg = client.post("/api/v1/auth/register", json={"email": f"tax_zero_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token = reg.json()["access_token"]
    ws_id = reg.json()["workspace"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/v1/workspaces/{ws_id}/tax-reconciliation?period_month=2026-11", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["gross_sales"] == "0.00"
    assert data["tds_section_194_o"] == "0.00"
    assert data["tcs_section_52"] == "0.00"
    assert data["status"] == "no_transactions"

def test_dispute_generation_missing_discrepancy_returns_404():
    """Verify dispute generation fails with 404 when no discrepancy exists, NEVER fabricating 450.00 claim."""
    reg = client.post("/api/v1/auth/register", json={"email": f"disp_test_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token = reg.json()["access_token"]
    ws_id = reg.json()["workspace"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        f"/api/v1/workspaces/{ws_id}/disputes/generate",
        headers=headers,
        json={"order_id": "NON_EXISTENT_ORDER_999", "marketplace": "amazon_in"}
    )
    assert res.status_code == 404
    assert "No discrepancy found" in res.json()["detail"]

def test_metrics_endpoint_rejects_regular_user_bearer_token():
    """Verify regular authenticated user cannot access /metrics."""
    reg = client.post("/api/v1/auth/register", json={"email": f"normal_user_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/metrics", headers=headers)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_metrics_endpoint_allows_superuser_bearer_token():
    """Verify superuser operator CAN access /metrics."""
    db = SessionLocal()
    try:
        super_user = User(email=f"superuser_{uuid.uuid4().hex[:6]}@example.com", is_active=True, is_superuser=True)
        db.add(super_user)
        db.commit()

        token = create_access_token({"sub": super_user.id})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/v1/metrics", headers=headers)
        assert res.status_code == 200
        assert "workspaces_count" in res.json()
    finally:
        db.close()

def test_trusted_proxy_ip_handling():
    """Verify get_client_ip ignores X-Forwarded-For if direct caller is untrusted."""
    from app.core.rate_limiter import get_client_ip
    from unittest.mock import MagicMock

    # Request from untrusted external IP
    mock_req = MagicMock()
    mock_req.client.host = "203.0.113.195" # Public internet IP
    mock_req.headers = {"X-Forwarded-For": "198.51.100.5"}

    ip = get_client_ip(mock_req)
    assert ip == "203.0.113.195" # Did NOT trust forged header

    # Request from trusted proxy (127.0.0.1)
    mock_req.client.host = "127.0.0.1"
    ip_trusted = get_client_ip(mock_req)
    assert ip_trusted == "198.51.100.5" # Successfully extracted client IP via trusted proxy

def test_viewer_role_rejected_from_reconcile_and_tally_export():
    """Verify viewer role cannot trigger reconciliation or export Tally daybook."""
    db = SessionLocal()
    try:
        viewer_user = User(email=f"viewer_audit_{uuid.uuid4().hex[:6]}@example.com", is_active=True)
        db.add(viewer_user)
        ws = Workspace(name="Viewer RBAC Test Workspace")
        db.add(ws)
        db.commit()

        member = WorkspaceMember(workspace_id=ws.id, user_id=viewer_user.id, role="viewer")
        db.add(member)
        db.commit()

        token = create_access_token({"sub": viewer_user.id})
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt to run reconciliation
        recon_res = client.post(f"/api/v1/workspaces/{ws.id}/reconcile", headers=headers)
        assert recon_res.status_code == 403
        assert "Reconciliation execution requires" in recon_res.json()["detail"]

        # Attempt to export Tally DayBook
        tally_res = client.get(f"/api/v1/workspaces/{ws.id}/export-tally", headers=headers)
        assert tally_res.status_code == 403
        assert "Tally export requires" in tally_res.json()["detail"]
    finally:
        db.close()

def test_storage_provider_quarantine_workflow():
    """Verify storage provider saves in quarantine and promotes to verified."""
    from app.core.storage import storage
    test_ws = f"ws_test_{uuid.uuid4().hex[:6]}"
    test_file = "test_doc.csv"
    data = b"order_id,amount\n101,500.00"

    path = storage.save(test_ws, test_file, data, is_quarantined=True)
    assert "quarantine" in path

    verified_path = storage.promote_from_quarantine(path)
    assert "verified" in verified_path

    # Clean up
    deleted = storage.delete(verified_path)
    assert deleted is True

def test_production_mode_rejects_local_auth_routes(monkeypatch):
    """Verify S02: Local password login & register routes are disabled in production."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    reg_res = client.post("/api/v1/auth/register", json={"email": "prod_user@example.com", "password": "Password123!"})
    assert reg_res.status_code == 403
    assert "disabled in production" in reg_res.json()["detail"]

    login_res = client.post("/api/v1/auth/login", json={"email": "prod_user@example.com", "password": "Password123!"})
    assert login_res.status_code == 403
    assert "disabled in production" in login_res.json()["detail"]

def test_get_stores_is_idempotent_read_only():
    """Verify S03: GET stores does not mutate DB or create stores on read."""
    reg = client.post("/api/v1/auth/register", json={"email": f"stores_user_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token = reg.json()["access_token"]
    ws_id = reg.json()["workspace"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    res1 = client.get(f"/api/v1/workspaces/{ws_id}/stores", headers=headers)
    assert res1.status_code == 200
    count1 = len(res1.json())

    res2 = client.get(f"/api/v1/workspaces/{ws_id}/stores", headers=headers)
    assert res2.status_code == 200
    assert len(res2.json()) == count1

def test_workspace_creation_error_sanitization_no_raw_sqlexception(monkeypatch):
    """Verify S09: Database errors return generic message and request ID without raw str(e)."""
    reg = client.post("/api/v1/auth/register", json={"email": f"ws_err_user_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from sqlalchemy.orm import Session
    def mock_commit(self):
        raise RuntimeError("CRITICAL: SQL Connection Terminated: SELECT * FROM credentials")

    monkeypatch.setattr(Session, "commit", mock_commit)

    res = client.post("/api/v1/workspaces", headers=headers, data={"name": "Broken Workspace"})
    assert res.status_code == 500
    assert "Failed to create workspace" in res.json()["detail"]
    assert "Reference Request ID:" in res.json()["detail"]
    # Ensure raw exception / SQL string is NOT leaked to client
    assert "CRITICAL: SQL Connection Terminated" not in res.json()["detail"]

def test_import_with_decimal_payload_serialization_success():
    """Verify F03: Settlement upload with Decimal values serializes into JSON column without TypeError."""
    reg = client.post("/api/v1/auth/register", json={"email": f"decimal_user_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token = reg.json()["access_token"]
    ws_id = reg.json()["workspace"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = (
        "order_id,transaction_type,amount_type,amount,currency\n"
        "ORD-DEC-001,Order,ItemPrice,1499.50,INR\n"
        "ORD-DEC-001,Order,Commission,-150.00,INR\n"
    ).encode("utf-8")

    res = client.post(
        f"/api/v1/workspaces/{ws_id}/imports",
        headers=headers,
        files={"file": ("amazon_settlement_test.csv", csv_data, "text/csv")},
        data={"marketplace": "amazon_in"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "completed"
    assert res.json()["rows_processed"] == 2

def test_new_api_contracts_imports_reconciliation_products_evidence():
    """Verify F02: Complete frontend-facing contracts exist and return valid data."""
    reg = client.post("/api/v1/auth/register", json={"email": f"contract_user_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token = reg.json()["access_token"]
    ws_id = reg.json()["workspace"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List imports
    imp_res = client.get(f"/api/v1/workspaces/{ws_id}/imports", headers=headers)
    assert imp_res.status_code == 200
    assert isinstance(imp_res.json(), list)

    # 2. Get latest reconciliation
    recon_res = client.get(f"/api/v1/workspaces/{ws_id}/reconciliation/latest", headers=headers)
    assert recon_res.status_code == 200
    assert "summary" in recon_res.json()

    # 3. Product create & list
    p_create = client.post(
        f"/api/v1/workspaces/{ws_id}/products",
        headers=headers,
        data={"sku": "SKU-TEST-100", "cogs_amount": "250.00", "weight_grams": "600"}
    )
    assert p_create.status_code == 200
    assert p_create.json()["status"] == "saved"

    p_list = client.get(f"/api/v1/workspaces/{ws_id}/products", headers=headers)
    assert p_list.status_code == 200
    assert any(p["sku"] == "SKU-TEST-100" for p in p_list.json())

    # 4. Evidence drawer endpoint
    ev_res = client.get(f"/api/v1/workspaces/{ws_id}/evidence/ORD-DEC-001", headers=headers)
    assert ev_res.status_code == 200
    assert "transactions" in ev_res.json()

def test_invalid_bank_statement_date_returns_400():
    """Verify F06: Invalid date format in bank statement returns 400 error rather than defaulting to today."""
    reg = client.post("/api/v1/auth/register", json={"email": f"bank_date_user_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token = reg.json()["access_token"]
    ws_id = reg.json()["workspace"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    malformed_csv = (
        "value_date,narration,credit_amount,debit_amount\n"
        "NOT-A-REAL-DATE,Deposit from Amazon,1000.00,0.00\n"
    ).encode("utf-8")

    res = client.post(
        f"/api/v1/workspaces/{ws_id}/bank-statements/upload",
        headers=headers,
        files={"file": ("bad_bank.csv", malformed_csv, "text/csv")}
    )
    assert res.status_code == 400
    assert "Invalid date format" in res.json()["detail"]

def test_owner_tally_export_success():
    """Verify owner or authorized role can successfully export Tally DayBook XML without crashing."""
    reg = client.post("/api/v1/auth/register", json={"email": f"tally_user_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"})
    token = reg.json()["access_token"]
    ws_id = reg.json()["workspace"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/v1/workspaces/{ws_id}/export-tally", headers=headers)
    assert res.status_code == 200
    assert "application/xml" in res.headers["content-type"]
    assert "<ENVELOPE>" in res.text
    assert "<TALLYREQUEST>Import Data</TALLYREQUEST>" in res.text



