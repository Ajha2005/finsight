import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.core.config import settings

# ── Test database setup ──
# We use a separate test DB so we never touch real data
TEST_DATABASE_URL = settings.DATABASE_URL + "_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)
HEADERS = {"x-api-key": settings.API_KEY}


# ── Helper ──
def make_csv(content: str):
    return io.BytesIO(content.encode())


# ── Tests ──

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_valid_csv():
    csv_content = "Date,Description,Amount\n2024-01-05,AMAZON,-45.99\n2024-01-06,SALARY,50000.00"
    response = client.post(
        "/api/v1/transactions/upload",
        headers=HEADERS,
        files={"file": ("test.csv", make_csv(csv_content), "text/csv")}
    )
    assert response.status_code == 200
    assert response.json()["summary"]["saved"] == 2


def test_upload_invalid_file_type():
    response = client.post(
        "/api/v1/transactions/upload",
        headers=HEADERS,
        files={"file": ("test.txt", make_csv("hello"), "text/plain")}
    )
    assert response.status_code == 400


def test_upload_missing_columns():
    csv_content = "Name,Value\nfoo,bar"
    response = client.post(
        "/api/v1/transactions/upload",
        headers=HEADERS,
        files={"file": ("test.csv", make_csv(csv_content), "text/csv")}
    )
    assert response.status_code == 422


def test_get_transactions_empty():
    response = client.get("/api/v1/transactions", headers=HEADERS)
    assert response.status_code == 200
    assert response.json() == []


def test_get_transactions_after_upload():
    csv_content = "Date,Description,Amount\n2024-01-05,AMAZON,-45.99\n2024-01-06,SALARY,50000.00"
    client.post(
        "/api/v1/transactions/upload",
        headers=HEADERS,
        files={"file": ("test.csv", make_csv(csv_content), "text/csv")}
    )
    response = client.get("/api/v1/transactions", headers=HEADERS)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_unauthorized_request():
    response = client.get("/api/v1/transactions", headers={"x-api-key": "wrongkey"})
    assert response.status_code == 401


def test_get_insights_empty():
    response = client.get("/api/v1/insights", headers=HEADERS)
    assert response.status_code == 200
    assert "message" in response.json()


def test_duplicate_upload_skipped():
    csv_content = "Date,Description,Amount\n2024-01-05,AMAZON,-45.99"
    for _ in range(2):
        client.post(
            "/api/v1/transactions/upload",
            headers=HEADERS,
            files={"file": ("test.csv", make_csv(csv_content), "text/csv")}
        )
    response = client.get("/api/v1/transactions", headers=HEADERS)
    assert len(response.json()) == 1