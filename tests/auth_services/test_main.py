import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    resp = client.get("/auth/health")
    assert resp.status_code == 200
    assert resp.json() == {"health": "All Good"}

def test_signup_validation(monkeypatch):
    resp = client.post("/auth/signup", json={"email": "", "password": "abc", "name": "User"})
    assert resp.status_code == 400

def test_login_missing(monkeypatch):
    resp = client.post("/auth/login", json={"email": "user@example.com", "password": ""})
    assert resp.status_code == 400

def test_refresh_missing(monkeypatch):
    resp = client.post("/auth/refresh-token", json={"email": "", "refresh_token": ""})
    assert resp.status_code == 400

def test_logout_no_token(monkeypatch):
    resp = client.post("/auth/logout")
    assert resp.status_code == 401

# Demonstration for dependency override (example for logout)
def test_logout_token(monkeypatch):
    def fake_logout(token):
        assert token == "val"
        return {"message": "Account Logged Out"}
    app.dependency_overrides = {}
    from auth_services.authentication import logout
    monkeypatch.setattr("authentication.logout", fake_logout)
    headers = {"Authorization": "Bearer val"}
    resp = client.post("/auth/logout", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"message": "Account Logged Out"}

