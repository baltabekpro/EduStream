import pytest
import inspect
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db


# Compatibility shim: Starlette TestClient passes `app=` into httpx.Client.
# httpx>=0.28 removed this parameter, which breaks tests at runtime.
if "app" not in inspect.signature(httpx.Client.__init__).parameters:
    _original_httpx_client_init = httpx.Client.__init__

    def _patched_httpx_client_init(self, *args, app=None, **kwargs):
        return _original_httpx_client_init(self, *args, **kwargs)

    httpx.Client.__init__ = _patched_httpx_client_init

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
