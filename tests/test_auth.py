# tests/test_auth.py
from ninja.testing import TestClient

from accounts.tokens import create_token
from taskflow.api import api

client = TestClient(api)


def test_obtain_token(alice):
    response = client.post("/auth/token", json={"username": "alice", "password": "wonderland-42"})
    assert response.status_code == 200
    token = response.json()["access"]

    response = client.get("/projects/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_wrong_password(alice):
    response = client.post("/auth/token", json={"username": "alice", "password": "nope"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


def test_missing_token():
    response = client.get("/projects/")
    assert response.status_code == 401


def test_expired_token(alice):
    token = create_token(alice.id, "access", lifetime=-1)
    response = client.get("/projects/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_refresh_token_is_not_an_access_token(alice):
    response = client.post("/auth/token", json={"username": "alice", "password": "wonderland-42"})
    refresh = response.json()["refresh"]
    response = client.get("/projects/", headers={"Authorization": f"Bearer {refresh}"})
    assert response.status_code == 401
