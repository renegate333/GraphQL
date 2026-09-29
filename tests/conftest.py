"""Общие фикстуры pytest."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Файловая тестовая БД, единая для всех модулей.
TEST_DB_PATH = ROOT / "test_vault.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_not_for_prod")
os.environ.setdefault("PASSWORD_PEPPER", "test_pepper_not_for_prod")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_TTL_MIN", "60")
os.environ.setdefault("PASSWORD_MIN_LENGTH", "12")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("APP_NAME", "Vault")

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine, SessionLocal, get_db
from app.main import app as fastapi_app


@pytest.fixture(autouse=True)
def _reset_db():
    """Перед каждым тестом — чистая схема."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """TestClient. И REST (get_db), и GraphQL (context.SessionLocal) используют
    одну и ту же фабрику SessionLocal из app.db.session — поэтому override
    нужен только для синхронного потока REST, GraphQL и так пойдёт в тестовую БД."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()