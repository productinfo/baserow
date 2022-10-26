import urllib
from typing import Any, Dict, Optional
from django.urls import reverse
from baserow.core.auth_provider.auth_provider_types import (
    AuthProviderType,
)
from baserow.core.auth_provider.models import AuthProviderModel
from django.conf import settings
from .models import (
    GoogleAuthProviderModel,
    FacebookAuthProviderModel,
    GitHubAuthProviderModel,
    GitLabAuthProviderModel,
    OpenIdConnectAuthProviderModel,
)
import requests
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
from dataclasses import dataclass, asdict
from rest_framework import serializers
from baserow_enterprise.api.sso.oauth2.exceptions import InvalidProviderUrl
from baserow_enterprise.api.sso.oauth2.errors import ERROR_INVALID_PROVIDER_URL
from baserow.api.utils import ExceptionMappingType


OAUTH_BACKEND_URL = settings.PUBLIC_BACKEND_URL


@dataclass
class UserInfo:
    name: str
    email: str


@dataclass
class WellKnownUrls:
    authorization_url: str
    access_token_url: str
    user_info_url: str


class OAuth2AuthProviderMixin:
    def can_create_new_providers(self):
        return True

    def get_login_options(self, **kwargs) -> Optional[Dict[str, Any]]:
        instances = self.model_class.objects.all()
        items = []
        for instance in instances:
            items.append(
                {
                    "redirect_url": urllib.parse.urljoin(
                        OAUTH_BACKEND_URL,
                        reverse("api:enterprise:sso:oauth2:login", args=(instance.id,)),
                    ),
                    "name": instance.name,
                    "type": self.type,
                }
            )
        return {
            "type": self.type,
            "items": items,
        }

    def get_authorization_url(
        self, instance: AuthProviderModel, base_url: Optional[str]
    ) -> str:
        """
        Expects self.SCOPE and self.AUTHORIZATION_URL to be set. Alternatively,
        base_url can be provided instead of AUTHORIZATION_URL.
        """

        if not base_url:
            base_url = self.AUTHORIZATION_URL
        oauth = self.get_oauth_session(instance)
        authorization_url, state = oauth.authorization_url(base_url)
        return authorization_url

    def get_oauth_session(self, instance: AuthProviderModel) -> OAuth2Session:
        redirect_uri = urllib.parse.urljoin(
            OAUTH_BACKEND_URL,
            reverse("api:enterprise:sso:oauth2:callback", args=(instance.id,)),
        )
        return OAuth2Session(
            instance.client_id, redirect_uri=redirect_uri, scope=self.SCOPE
        )


class GoogleAuthProviderType(OAuth2AuthProviderMixin, AuthProviderType):
    """
    The Google authentication provider type allows users to
    login using OAuth2 through Google.
    """

    type = "google"
    model_class = GoogleAuthProviderModel
    allowed_fields = ["id", "enabled", "name", "client_id", "secret"]
    serializer_field_names = ["enabled", "name", "client_id", "secret"]

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    SCOPE = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    ACCESS_TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

    def get_user_info(self, instance: GoogleAuthProviderModel, code: str) -> UserInfo:
        oauth = self.get_oauth_session(instance)
        token = oauth.fetch_token(
            self.ACCESS_TOKEN_URL,
            code=code,
            client_secret=instance.secret,
        )
        response = oauth.get(self.USER_INFO_URL)
        name = response.json().get("name", None)
        email = response.json().get("email", None)
        return UserInfo(name=name, email=email)


class GitHubAuthProviderType(OAuth2AuthProviderMixin, AuthProviderType):
    """
    The Github authentication provider type allows users to
    login using OAuth2 through Github.
    """

    type = "github"
    model_class = GitHubAuthProviderModel
    allowed_fields = ["id", "enabled", "name", "client_id", "secret"]
    serializer_field_names = ["enabled", "name", "client_id", "secret"]

    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    SCOPE = "read:user,user:email"

    ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_INFO_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    def get_user_info(self, instance: GitHubAuthProviderModel, code: str) -> UserInfo:
        oauth = self.get_oauth_session(instance)
        token = oauth.fetch_token(
            self.ACCESS_TOKEN_URL,
            code=code,
            client_secret=instance.secret,
        )
        response = oauth.get(self.USER_INFO_URL)
        name = response.json().get("name", None)
        email = self.get_email(
            self.EMAILS_URL,
            {"Authorization": "token {}".format(token.get("access_token"))},
        )
        return UserInfo(name=name, email=email)

    def get_email(url, headers):
        email = None
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        emails = resp.json()
        if resp.status_code == 200 and emails:
            email = emails[0]
            primary_emails = [
                e for e in emails if not isinstance(e, dict) or e.get("primary")
            ]
            if primary_emails:
                email = primary_emails[0]
            if isinstance(email, dict):
                email = email.get("email", "")
        return email


class GitLabAuthProviderType(OAuth2AuthProviderMixin, AuthProviderType):
    """
    The GitLab authentication provider type allows users to
    login using OAuth2 through GitLab.
    """

    type = "gitlab"
    model_class = GitLabAuthProviderModel
    allowed_fields = ["id", "enabled", "name", "url", "client_id", "secret"]
    serializer_field_names = ["enabled", "name", "url", "client_id", "secret"]

    AUTHORIZATION_URL = "https://gitlab.com/oauth/authorize"
    SCOPE = ["read_user"]

    ACCESS_TOKEN_URL = "https://gitlab.com/oauth/token"
    USER_INFO_URL = "https://gitlab.com/api/v4/user"

    def get_authorization_url(
        self, instance: AuthProviderModel, base_url: Optional[str]
    ) -> str:
        # TODO: access and user info url based on instance.url or not
        super().get_authorization_url(instance, instance.url)

    def get_user_info(self, instance: GitLabAuthProviderModel, code: str) -> UserInfo:
        oauth = self.get_oauth_session(instance)
        token = oauth.fetch_token(
            self.ACCESS_TOKEN_URL,
            code=code,
            client_secret=instance.secret,
        )
        response = oauth.get(self.USER_INFO_URL)
        name = response.json().get("name", None)
        email = response.json().get("email", None)
        return UserInfo(name=name, email=email)


class FacebookAuthProviderType(OAuth2AuthProviderMixin, AuthProviderType):
    """
    The Facebook authentication provider type allows users to
    login using OAuth2 through Facebook.
    """

    type = "facebook"
    model_class = FacebookAuthProviderModel
    allowed_fields = ["id", "enabled", "name", "url", "client_id", "secret"]
    serializer_field_names = ["enabled", "name", "url", "client_id", "secret"]

    AUTHORIZATION_URL = "https://www.facebook.com/dialog/oauth"
    SCOPE = ["email"]

    ACCESS_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
    USER_INFO_URL = "https://graph.facebook.com/me?fields=id,email,name"

    def get_authorization_url(
        self, instance: FacebookAuthProviderModel, base_url: Optional[str]
    ) -> str:
        oauth = self.get_oauth_session(instance)
        oauth = facebook_compliance_fix(oauth)
        authorization_url, state = oauth.authorization_url(self.AUTHORIZATION_URL)
        return authorization_url

    def get_user_info(self, instance: FacebookAuthProviderModel, code: str) -> UserInfo:
        oauth = self.get_oauth_session(instance)
        oauth = facebook_compliance_fix(oauth)
        token = oauth.fetch_token(
            self.ACCESS_TOKEN_URL,
            code=code,
            client_secret=instance.secret,
        )
        response = oauth.get(self.USER_INFO_URL)
        name = response.json().get("name", None)
        email = response.json().get("email", None)
        return UserInfo(name=name, email=email)


class OpenIdConnectAuthProviderType(OAuth2AuthProviderMixin, AuthProviderType):
    """
    The OpenId authentication provider type allows users to
    login using OAuth2 through OpenId Connect compatible provider.
    """

    type = "openid_connect"
    model_class = OpenIdConnectAuthProviderModel
    allowed_fields = [
        "id",
        "enabled",
        "name",
        "url",
        "client_id",
        "secret",
        "authorization_url",
        "access_token_url",
        "user_info_url",
    ]
    serializer_field_names = ["enabled", "name", "url", "client_id", "secret"]
    api_exceptions_map: ExceptionMappingType = {
        InvalidProviderUrl: ERROR_INVALID_PROVIDER_URL
    }

    SCOPE = ["openid", "email", "profile"]

    def create(self, **values):
        urls = self.get_wellknown_urls(values["url"])
        return super().create(**values, **asdict(urls))

    def update(self, provider, **values):
        urls = {}
        if values.get("url"):
            urls = self.get_wellknown_urls(values["url"])
        return super().update(provider, **values, **asdict(urls))

    def get_authorization_url(
        self, instance: AuthProviderModel, base_url: Optional[str]
    ) -> str:
        super().get_authorization_url(instance, instance.authorization_url)

    def get_user_info(
        self, instance: OpenIdConnectAuthProviderModel, code: str
    ) -> UserInfo:
        oauth = self.get_oauth_session(instance)
        token = oauth.fetch_token(
            instance.access_token_url,
            code=code,
            client_secret=instance.secret,
        )
        response = oauth.get(instance.user_info_url)
        name = response.json().get("name", None)
        email = response.json().get("email", None)
        return UserInfo(name=name, email=email)

    def get_wellknown_urls(self, base_url: str) -> WellKnownUrls:
        try:
            wellknown_url = f"{base_url}/.well-known/openid-configuration"
            response = requests.get(wellknown_url)
            return WellKnownUrls(
                authorization_url=response.json()["authorization_endpoint"],
                access_token_url=response.json()["token_endpoint"],
                user_info_url=response.json()["userinfo_endpoint"],
            )
        except Exception:
            raise InvalidProviderUrl()
