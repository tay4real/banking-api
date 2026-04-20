import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Account  # noqa: F401

# Use a dedicated test database on your running PostgreSQL container
TEST_DATABASE_URL = "postgresql://postgres:password@localhost:5432/banking_test"


def create_test_database():
    """Create the test database if it doesn't exist."""
    root_engine = create_engine(
        "postgresql://postgres:password@localhost:5432/postgres",
        isolation_level="AUTOCOMMIT"
    )
    with root_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname='banking_test'")
        ).fetchone()
        if not exists:
            conn.execute(text("CREATE DATABASE banking_test"))
    root_engine.dispose()


create_test_database()

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture(scope="function")
def db():
    """Fresh schema for every test — all tables dropped and recreated."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_redis():
    """Auto-applied to every test — replaces Redis with an in-memory mock."""
    with patch("app.core.redis_client.redis_client") as mock:
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock(return_value=True)
        mock.ping = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def registered_user(client):
    payload = {
        "email": "ada@example.com",
        "full_name": "Ada Okafor",
        "phone_number": "08012345678",
        "password": "SecurePass1!"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return payload


@pytest.fixture
def auth_headers(client, registered_user):
    response = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"]
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_tokens(client, registered_user):
    response = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"]
    })
    return response.json()