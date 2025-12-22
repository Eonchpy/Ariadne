import pytest
from httpx import AsyncClient

from app.core.security import get_password_hash
from app.repositories.user_repo import UserRepository
from app.models.user import User as UserModel
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_auth_login_refresh_and_me(client: AsyncClient, db_session: AsyncSession):
    # Arrange: create a user
    repo = UserRepository(db_session)
    password = "pass123!"
    user = UserModel(
        email="user@example.com",
        name="Test User",
        hashed_password=get_password_hash(password),
        roles=["admin"],
    )
    await repo.add(user)
    await db_session.commit()

    # Act: login
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": password}
    )
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == user.email

    # Act: call /users/me with access token
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    me_resp = await client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == user.email

    # Act: refresh token
    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]}
    )
    assert refresh_resp.status_code == 200
    refreshed = refresh_resp.json()
    assert refreshed["access_token"]
    assert refreshed["refresh_token"]

    # Act: logout (revokes refresh)
    logout_resp = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": refreshed["refresh_token"]}
    )
    assert logout_resp.status_code == 204
