import os
import pytest

# Configure a valid, non-placeholder test deployment secret for the automated test suite
TEST_SECRET = "sellerflow-automated-test-suite-secure-key-2026-xyz"
TEST_MONITORING_SECRET = "sellerflow-test-monitoring-token-2026-xyz"
os.environ["JWT_SECRET_KEY"] = TEST_SECRET
os.environ["MONITORING_SECRET_TOKEN"] = TEST_MONITORING_SECRET

from app.core.config import settings
settings.JWT_SECRET_KEY = TEST_SECRET
settings.MONITORING_SECRET_TOKEN = TEST_MONITORING_SECRET

from app.core.database import Base, engine
from app.core.rate_limiter import limiter

@pytest.fixture(autouse=True)
def setup_database_and_limiter():
    limiter.reset()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    limiter.reset()
