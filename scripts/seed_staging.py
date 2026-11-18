import os
import sys
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.core.database import SessionLocal, engine, Base
from app.models.entities import Workspace, Store, User, WorkspaceMember, Product, BankAccount
from app.core.security import get_password_hash

def seed_staging():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Workspace).count() > 0:
            print("Staging database already has workspaces. Skipping.")
            return

        print("Seeding SellerFlow AI staging environment...")
        
        # Create Admin User (read password from environment, never hardcode)
        seed_password = os.environ.get("SEED_ADMIN_PASSWORD")
        if not seed_password:
            import secrets
            seed_password = secrets.token_urlsafe(16)
            print(f"[SECURITY NOTICE] No SEED_ADMIN_PASSWORD set in env. Generated random staging password: {seed_password}")

        user = User(
            email="demo@sellerflow.ai",
            full_name="Demo Seller & CA",
            hashed_password=get_password_hash(seed_password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Primary Workspace
        ws = Workspace(
            name="Apex Retail India",
            subscription_tier="pro"
        )
        db.add(ws)
        db.commit()
        db.refresh(ws)

        # Membership
        db.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="owner"))

        # Marketplaces
        db.add(Store(workspace_id=ws.id, display_name="Amazon India Store", marketplace_code="amazon_in"))
        db.add(Store(workspace_id=ws.id, display_name="Flipkart Electronics", marketplace_code="flipkart"))
        db.add(Store(workspace_id=ws.id, display_name="Meesho Supplier Direct", marketplace_code="meesho"))

        # Products
        db.add(Product(workspace_id=ws.id, sku="SKU-CHAIR-01", title="Ergonomic Desk Chair", category="Furniture", weight_grams=1200, cogs_amount=Decimal("650.00")))
        db.add(Product(workspace_id=ws.id, sku="SKU-TABLE-01", title="Oak Coffee Table", category="Furniture", weight_grams=3500, cogs_amount=Decimal("950.00")))

        # Bank Account
        db.add(BankAccount(workspace_id=ws.id, bank_name="HDFC Current Account", account_number_mask="XXXX-4819", ifsc_code="HDFC0000128"))

        db.commit()
        print("Staging database seeded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_staging()
