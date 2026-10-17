import pytest
from unittest.mock import MagicMock, patch
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import  create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database import Base
from main import app, get_db



SQLALCHEMY_TEST_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args = {"check_same_thread": False}, poolclass = StaticPool)

TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind = engine)
    yield
    Base.metadata.drop_all(bind=engine)

#_______test logic___________#

def test_register_sucess():
    response = client.post("/register", json={"username": "testuser", "password": "123456789"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "password" not in data

def test_register_duplicate_username():
    client.post("/register", json={"username": "surya", "password": "bhuvi1234"})
    response = client.post("/register", json={"username": "surya", "password": "bhuvi1234"})
    assert response.status_code == 400

def test_login_sucess():
    client.post("/register", json={"username": "loginuser", "password": "123456789"})
    response = client.post("/login", data={"username": "loginuser", "password": "123456789"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_protected_route_without_token():
    response = client.get("/documents")
    assert response.status_code == 401

def test_login_wrong_password():
    client.post("/register", json={"username": "wronguser", "password": "correct123"})
    response = client.post("/login", data={     # ← data= not json=
        "username": "wronguser",
        "password": "wrongpass"
    })
    assert response.status_code == 401