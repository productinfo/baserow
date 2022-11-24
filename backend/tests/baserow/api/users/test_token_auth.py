from datetime import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.shortcuts import reverse

import pytest
from freezegun import freeze_time
from pytz import timezone
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework_simplejwt.tokens import RefreshToken

from baserow.core.models import UserLogEntry
from baserow.core.registries import Plugin, plugin_registry

User = get_user_model()


@pytest.mark.django_db
def test_token_auth(api_client, data_fixture):
    class TmpPlugin(Plugin):
        type = "tmp_plugin"
        called = False

        def user_signed_in(self, user):
            self.called = True

    plugin_mock = TmpPlugin()

    user = data_fixture.create_user(
        email="test@test.nl", password="password", first_name="Test1", is_active=True
    )

    assert not user.last_login

    response = api_client.post(
        reverse("api:user:token_auth"), {"password": "password"}, format="json"
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["email"] == ["This field is required."]

    # accept username for backward compatibility
    response = api_client.post(
        reverse("api:user:token_auth"),
        {"username": "invalid_mail", "password": "password"},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["username"] == ["Enter a valid email address."]

    response = api_client.post(
        reverse("api:user:token_auth"),
        {"email": "invalid_mail", "password": "password"},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["email"] == ["Enter a valid email address."]

    response = api_client.post(
        reverse("api:user:token_auth"),
        {"email": "no_existing@test.nl", "password": "password"},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert (
        response_json["detail"] == "No active account found with the given credentials."
    )

    response = api_client.post(
        reverse("api:user:token_auth"),
        {"email": "test@test.nl", "password": "wrong_password"},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert (
        response_json["detail"] == "No active account found with the given credentials."
    )

    with patch.dict(plugin_registry.registry, {"tmp": plugin_mock}):
        with freeze_time("2020-01-01 12:00"):
            response = api_client.post(
                reverse("api:user:token_auth"),
                {"email": "test@test.nl", "password": "password"},
                format="json",
            )
            response_json = response.json()
            assert response.status_code == HTTP_200_OK
            assert "access_token" in response_json
            assert "refresh_token" in response_json
            assert "user" in response_json
            assert response_json["user"]["username"] == "test@test.nl"
            assert response_json["user"]["first_name"] == "Test1"
            assert response_json["user"]["id"] == user.id
            assert response_json["user"]["is_staff"] is False
            assert plugin_mock.called

    user.refresh_from_db()
    assert user.last_login == datetime(2020, 1, 1, 12, 00, tzinfo=timezone("UTC"))

    logs = UserLogEntry.objects.all()
    assert len(logs) == 1
    assert logs[0].actor_id == user.id
    assert logs[0].action == "SIGNED_IN"
    assert logs[0].timestamp == datetime(2020, 1, 1, 12, 00, tzinfo=timezone("UTC"))

    with freeze_time("2020-01-02 12:00"):
        response = api_client.post(
            reverse("api:user:token_auth"),
            {"email": " teSt@teSt.nL ", "password": "password"},
            format="json",
        )
        response_json = response.json()
        assert response.status_code == HTTP_200_OK
        assert "access_token" in response_json
        assert "refresh_token" in response_json
        assert "user" in response_json
        assert response_json["user"]["username"] == "test@test.nl"
        assert response_json["user"]["first_name"] == "Test1"
        assert response_json["user"]["id"] == user.id
        assert response_json["user"]["is_staff"] is False

    user.refresh_from_db()
    assert user.last_login == datetime(2020, 1, 2, 12, 0, tzinfo=timezone("UTC"))

    data_fixture.create_user(
        email="test2@test.nl", password="password", first_name="Test1", is_active=False
    )
    response = api_client.post(
        reverse("api:user:token_auth"),
        {"email": "test2@test.nl", "password": "wrong_password"},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert (
        response_json["detail"] == "No active account found with the given credentials."
    )

    response = api_client.post(
        reverse("api:user:token_auth"),
        {"email": "test2@test.nl", "password": "password"},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response_json["error"] == "ERROR_DEACTIVATED_USER"
    assert response_json["detail"] == "User account has been disabled."

    # Check that a login cancel user deletion
    user_to_be_deleted = data_fixture.create_user(
        email="test3@test.nl", password="password", to_be_deleted=True
    )

    # check that the user cannot refresh the token if set to be deleted
    refresh_token = str(RefreshToken.for_user(user_to_be_deleted))
    response = api_client.post(
        reverse("api:user:token_refresh"),
        {"refresh_token": refresh_token},
        format="json",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    response_json = response.json()
    assert response_json["error"] == "ERROR_INVALID_REFRESH_TOKEN"
    assert response_json["detail"] == "Refresh token is expired or invalid."

    response = api_client.post(
        reverse("api:user:token_auth"),
        {"email": "test3@test.nl", "password": "password"},
        format="json",
    )

    user_to_be_deleted.refresh_from_db()
    assert user_to_be_deleted.profile.to_be_deleted is False

    # check that now the user can refresh the token
    response = api_client.post(
        reverse("api:user:token_refresh"),
        {"refresh_token": refresh_token},
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert "access_token" in response_json
    assert "user" in response_json


@pytest.mark.django_db
def test_token_refresh(api_client, data_fixture):
    class TmpPlugin(Plugin):
        type = "tmp_plugin"
        called = False

        def user_signed_in(self, user):
            self.called = True

    plugin_mock = TmpPlugin()

    user = data_fixture.create_user(
        email="test@test.nl", password="password", first_name="Test1"
    )
    refresh_token = str(RefreshToken.for_user(user))

    response = api_client.post(
        reverse("api:user:token_refresh"), {"token": "WRONG_TOKEN"}, format="json"
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    response_json = response.json()
    assert response_json["error"] == "ERROR_INVALID_REFRESH_TOKEN"
    assert response_json["detail"] == "Refresh token is expired or invalid."

    # DEPRECATED: "token" as body param is deprecated, use "refresh_token" instead
    with patch.dict(plugin_registry.registry, {"tmp": plugin_mock}):
        response = api_client.post(
            reverse("api:user:token_refresh"),
            {"token": refresh_token},
            format="json",
        )
        assert response.status_code == HTTP_200_OK
        response_json = response.json()
        assert "access_token" in response_json
        assert "user" in response_json
        assert response_json["user"]["username"] == "test@test.nl"
        assert response_json["user"]["first_name"] == "Test1"
        assert response_json["user"]["id"] == user.id
        assert response_json["user"]["is_staff"] is False
        assert not plugin_mock.called

    with patch.dict(plugin_registry.registry, {"tmp": plugin_mock}):
        response = api_client.post(
            reverse("api:user:token_refresh"),
            {"refresh_token": refresh_token},
            format="json",
        )
        assert response.status_code == HTTP_200_OK
        response_json = response.json()
        assert "access_token" in response_json
        assert "user" in response_json
        assert response_json["user"]["username"] == "test@test.nl"
        assert response_json["user"]["first_name"] == "Test1"
        assert response_json["user"]["id"] == user.id
        assert response_json["user"]["is_staff"] is False
        assert not plugin_mock.called

    with freeze_time("2019-01-01 12:00"):
        response = api_client.post(
            reverse("api:user:token_refresh"),
            json={"refresh_token": str(RefreshToken.for_user(user))},
        )
        assert response.status_code == HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "ERROR_INVALID_REFRESH_TOKEN"
        assert response_json["detail"] == "Refresh token is expired or invalid."


@pytest.mark.django_db
def test_token_verify(api_client, data_fixture):
    class TmpPlugin(Plugin):
        type = "tmp_plugin"
        called = False

        def user_signed_in(self, user):
            self.called = True

    plugin_mock = TmpPlugin()

    user = data_fixture.create_user(
        email="test@test.nl", password="password", first_name="Test1"
    )
    refresh_token = str(RefreshToken.for_user(user))

    response = api_client.post(
        reverse("api:user:token_verify"), {"token": "WRONG_TOKEN"}, format="json"
    )
    assert response.status_code == HTTP_400_BAD_REQUEST

    with patch.dict(plugin_registry.registry, {"tmp": plugin_mock}):
        response = api_client.post(
            reverse("api:user:token_verify"),
            {"refresh_token": refresh_token},
            format="json",
        )
        response_json = response.json()
        assert response.status_code == HTTP_200_OK
        assert "user" in response_json
        assert response_json["user"]["username"] == "test@test.nl"
        assert response_json["user"]["first_name"] == "Test1"
        assert response_json["user"]["id"] == user.id
        assert response_json["user"]["is_staff"] is False
        assert not plugin_mock.called

    with freeze_time("2019-01-01 12:00"):
        response = api_client.post(
            reverse("api:user:token_verify"),
            json={"refresh_token": str(RefreshToken.for_user(user))},
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
