import os
from collections.abc import Generator
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy.engine import make_url
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

local_settings = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
os.environ.setdefault(
    "DATABASE_URL",
    local_settings.get("DATABASE_URL")
    or "postgresql+psycopg://ems_test:ems_test@localhost:5432/employee_management",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-never-used-for-production-123456789")

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Attendance, Department, Employee, LeaveRequest, User  # noqa: F401

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or local_settings.get("TEST_DATABASE_URL")
APPLICATION_DATABASE_URL = os.environ.get("DATABASE_URL") or local_settings.get("DATABASE_URL")
if TEST_DATABASE_URL:
    test_url = make_url(TEST_DATABASE_URL)
    if not test_url.database or not test_url.database.endswith("_test"):
        raise RuntimeError("TEST_DATABASE_URL must name a dedicated database ending in _test.")
    if APPLICATION_DATABASE_URL:
        app_url = make_url(APPLICATION_DATABASE_URL)
        if test_url.database == app_url.database:
            raise RuntimeError("TEST_DATABASE_URL must not point to the application database.")
testing_session_local = None


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    global testing_session_local
    if not TEST_DATABASE_URL:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated PostgreSQL database ending in _test.")
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    email = "admin@example.test"
    password = "Admin-testing-password-123"
    assert testing_session_local is not None
    with testing_session_local() as db:
        db.add(User(email=email, password_hash=hash_password_for_fixture(password), role="admin"))
        db.commit()
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.cookies['access_token']}"}


@pytest.fixture
def db_session_factory(client: TestClient):
    return testing_session_local


def hash_password_for_fixture(password: str) -> str:
    from app.core.security import hash_password

    return hash_password(password)
