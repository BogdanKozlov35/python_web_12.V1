import json
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi import BackgroundTasks
from httpx import ASGITransport, AsyncClient

from main import app
from src.admin.emails import send_email
from tests.confi_test import override_get_db, test_user, auth_headers, db_session, test_user_contact, user_password, user_role





async def test_user_register(override_get_db, user_role, faker, monkeypatch):

    with patch.object(BackgroundTasks, "add_task") as mock_add_task:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:

            payload = {
                "email": faker.email(),
                "username": faker.user_name(),
                "password": faker.password(),
            }
            response = await ac.post(
                "/auth/register",
                json=payload,
            )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["email"] == payload["email"]

        mock_add_task.assert_called_once_with(send_email, data["email"])



async def test_user_login(override_get_db, test_user, user_password, faker):
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as ac:

        response = await ac.post(
            "/auth/token",
            data={"username": test_user.username, "password": user_password},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
