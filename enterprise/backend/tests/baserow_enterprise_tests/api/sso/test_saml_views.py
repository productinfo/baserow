import urllib

from django.shortcuts import reverse
from django.test.utils import override_settings

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_saml_provider_get_login_url(api_client, data_fixture, enterprise_data_fixture):
    admin, token = data_fixture.create_user_and_token(is_staff=True)

    # create a valid SAML provider
    auth_provider_1 = enterprise_data_fixture.create_saml_auth_provider(
        domain="test1.com"
    )
    auth_provider_login_url = reverse("api:enterprise:sso:saml:login_url")

    # cannot create a SAML provider with an invalid domain or metadata
    response = api_client.get(
        auth_provider_login_url, format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert "redirect_url" in response_json
    assert response_json["redirect_url"] == "http://testserver/api/sso/saml/login/"

    # if more than one SAML provider is enabled, this endpoint need a email address
    auth_provider_2 = enterprise_data_fixture.create_saml_auth_provider(
        domain="test2.com"
    )

    # cannot create a SAML provider with an invalid domain or metadata
    response = api_client.get(
        reverse("api:enterprise:sso:saml:login_url"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_SAML_INVALID_LOGIN_REQUEST"

    query_params = urllib.parse.urlencode(
        {
            "email": f"user@{auth_provider_1.domain}",
            "original": "/database/1/table/1",
        }
    )
    response = api_client.get(
        f"{auth_provider_login_url}?{query_params}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert "redirect_url" in response_json
    assert (
        response_json["redirect_url"]
        == f"http://testserver/api/sso/saml/login/?{query_params}"
    )

    query_params = urllib.parse.urlencode(
        {
            "email": f"user@{auth_provider_2.domain}",
            "original": "http://test.com",
        }
    )
    response = api_client.get(
        f"{auth_provider_login_url}?{query_params}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert "redirect_url" in response_json
    # the original url is not relative so it should be ignored
    response_query_params = urllib.parse.urlencode(
        {
            "email": f"user@{auth_provider_2.domain}",
        }
    )
    assert (
        response_json["redirect_url"]
        == f"http://testserver/api/sso/saml/login/?{response_query_params}"
    )

    query_params = urllib.parse.urlencode(
        {
            "email": "user@unregistered-domain.com",
            "original": "http://test.com",
        }
    )
    response = api_client.get(
        f"{auth_provider_login_url}?{query_params}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_SAML_INVALID_LOGIN_REQUEST"

    response = api_client.get(
        f"{auth_provider_login_url}?email=invalid_email",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
