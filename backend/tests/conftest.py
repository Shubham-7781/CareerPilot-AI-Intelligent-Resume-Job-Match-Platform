import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Must be set before app.core.config.Settings() is instantiated at import
# time — points file uploads at a temp dir instead of the container path
# /app/uploads, which won't exist (or be writable) outside Docker/CI.
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="careerpilot_test_uploads_"))
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_pytest_only")
# The whole test session hits the API from the same client IP in rapid
# succession — without a high ceiling here, unrelated tests start failing
# with 429s purely because of test volume, not because anything's wrong.
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "100000")

from app.db.session import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
