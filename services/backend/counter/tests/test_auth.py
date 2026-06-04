"""Basic integration tests for dj-rest-auth endpoints."""

import pytest

pytestmark = pytest.mark.django_db


def test_register(api_client):
    resp = api_client.post("/api/auth/registration/", {
        "username": "newuser",
        "email": "newuser@example.com",
        "password1": "Str0ng!Pass",
        "password2": "Str0ng!Pass",
    })
    assert resp.status_code == 201
    assert "key" in resp.data


def test_login(api_client, user):
    resp = api_client.post("/api/auth/login/", {
        "username": "testuser",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    assert "key" in resp.data


def test_user_details(auth_client):
    resp = auth_client.get("/api/auth/user/")
    assert resp.status_code == 200
    assert resp.data["username"] == "testuser"
    assert resp.data["email"] == "testuser@example.com"


def test_logout(auth_client):
    resp = auth_client.post("/api/auth/logout/")
    assert resp.status_code == 200


def test_password_change(auth_client):
    resp = auth_client.post("/api/auth/password/change/", {
        "new_password1": "NewPass123!",
        "new_password2": "NewPass123!",
    })
    assert resp.status_code == 200
