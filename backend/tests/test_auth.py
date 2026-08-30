"""Authentication tests."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_register_login_me(app_client):
    r = await app_client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "company": "TestCo",
        "password": "Password123!",
        "confirm_password": "Password123!",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body

    token = body["access_token"]
    r = await app_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "test@example.com"

    # Login
    r = await app_client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "Password123!",
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_password_mismatch(app_client):
    r = await app_client.post("/api/auth/register", json={
        "name": "X", "email": "x@example.com",
        "password": "Password123!", "confirm_password": "DIFFERENT",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_invalid_login(app_client):
    r = await app_client.post("/api/auth/login", json={
        "email": "nobody@example.com", "password": "wrong",
    })
    assert r.status_code == 401
