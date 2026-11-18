import os
import pytest

# Configure a valid, non-placeholder test deployment secret for the automated test suite
TEST_SECRET = "sellerflow-automated-test-suite-secure-key-2026-xyz"
os.environ["JWT_SECRET_KEY"] = TEST_SECRET

from app.core.config import settings
settings.JWT_SECRET_KEY = TEST_SECRET

from app.core.database import Base, engine

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
