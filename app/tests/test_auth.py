import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.main import app

engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine_test)


@pytest.fixture(autouse=True)
def setup_db() -> None:
    Base.metadata.create_all(engine_test)
    yield
    Base.metadata.drop_all(engine_test)


@pytest.fixture
def client(setup_db: None) -> TestClient:
    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def get_token(client: TestClient) -> str:
    response = client.post("/token", data={"username": "demo", "password": "orientops2026"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_token_valid_credentials(client: TestClient) -> None:
    response = client.post("/token", data={"username": "demo", "password": "orientops2026"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_token_invalid_credentials(client: TestClient) -> None:
    response = client.post("/token", data={"username": "demo", "password": "wrong"})
    assert response.status_code == 401


def test_protected_endpoint_without_token(client: TestClient) -> None:
    assert client.get("/filieres").status_code == 401
    assert client.get("/formations").status_code == 401
    assert client.post("/recommend", json={}).status_code == 401


def test_protected_endpoint_with_valid_token(client: TestClient) -> None:
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/filieres", headers=headers).status_code == 200
    assert client.get("/formations", headers=headers).status_code == 200


def test_protected_endpoint_with_invalid_token(client: TestClient) -> None:
    headers = {"Authorization": "Bearer invalidtoken"}
    assert client.get("/filieres", headers=headers).status_code == 401


def test_health_is_public(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
