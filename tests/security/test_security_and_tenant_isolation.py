import pytest
from decimal import Decimal
from fastapi import HTTPException
from app.core.security import (
    sanitize_for_spreadsheet,
    validate_and_sanitize_upload,
    verify_tenant_access
)
from app.models.entities import Workspace, User, WorkspaceMember
from app.core.database import SessionLocal, Base, engine

def test_csv_formula_injection_sanitization():
    """Ensure dangerous formula injection characters (=, +, -, @, tab, cr) are prepended with single quote."""
    assert sanitize_for_spreadsheet("=1+1") == "'=1+1"
    assert sanitize_for_spreadsheet("+cmd|'/c calc'!A1") == "'+cmd|'/c calc'!A1"
    assert sanitize_for_spreadsheet("-5+2") == "'-5+2"
    assert sanitize_for_spreadsheet("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_for_spreadsheet("\tTAB_INJECT") == "'\tTAB_INJECT"
    # Safe text remains unchanged
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

def test_tenant_isolation_cross_tenant_denied():
    """
    CRITICAL SECURITY INVARIANT:
    User A cannot access Workspace B's data. Must raise HTTP 403 Forbidden.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Create Workspace A and User A
        ws_a = Workspace(name="Tenant A Workspace")
        db.add(ws_a)
        db.commit()
        db.refresh(ws_a)

        user_a = User(email="usera@example.com")
        db.add(user_a)
        db.commit()
        db.refresh(user_a)

        db.add(WorkspaceMember(workspace_id=ws_a.id, user_id=user_a.id, role="owner"))

        # Create Workspace B and User B
        ws_b = Workspace(name="Tenant B Workspace")
        db.add(ws_b)
        db.commit()
        db.refresh(ws_b)

        user_b = User(email="userb@example.com")
        db.add(user_b)
        db.commit()
        db.refresh(user_b)

        db.add(WorkspaceMember(workspace_id=ws_b.id, user_id=user_b.id, role="owner"))
        db.commit()

        # User A tries to access Workspace B: MUST FAIL WITH 403
        with pytest.raises(HTTPException) as exc_info:
            verify_tenant_access(
                workspace_id=ws_b.id,
                authorization=None,
                x_user_id=user_a.id,
                x_workspace_id=None,
                db=db
            )
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

        # User A accessing Workspace A: MUST SUCCEED
        verified_ws = verify_tenant_access(
            workspace_id=ws_a.id,
            authorization=None,
            x_user_id=user_a.id,
            x_workspace_id=None,
            db=db
        )
        assert verified_ws.id == ws_a.id

    finally:
        db.close()
