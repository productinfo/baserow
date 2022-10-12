import urllib
from typing import Any, Dict, Optional
from django.urls import reverse
from baserow.core.auth_provider.auth_provider_types import (
    AuthenticationProviderType,
)
from baserow.core.auth_provider.models import AuthenticationProviderModel
from django.conf import settings
from .models import (
    GoogleAuthenticationProviderModel,
    FacebookAuthenticationProviderModel,
    GitHubAuthenticationProviderModel,
    GitLabAuthenticationProviderModel,
    OpenIdConnectAuthenticationProviderModel,
)
import requests
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
import json
from dataclasses import dataclass

OAUTH_BACKEND_URL = settings.PUBLIC_BACKEND_URL


@dataclass
class UserInfo:
    name: str
    email: str


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
        self, instance: AuthenticationProviderModel, base_url: Optional[str]
    ) -> str:
        """
        Expects self.SCOPE and self.AUTHORIZATION_URL to be set. Alternatively,
        base_url can be provided instead of AUTHORIZATION_URL.
        """

        if not base_url:
            base_url = self.AUTHORIZATION_URL
        provider_id = instance.id
        redirect_uri = urllib.parse.urljoin(
            OAUTH_BACKEND_URL,
            reverse("api:enterprise:sso:oauth2:callback", args=(provider_id,)),
        )
        oauth = OAuth2Session(
            instance.client_id, redirect_uri=redirect_uri, scope=self.SCOPE
        )
        authorization_url, state = oauth.authorization_url(base_url)
        return authorization_url


class GoogleAuthenticationProviderType(
    OAuth2AuthProviderMixin, AuthenticationProviderType
):
    """
    The Google authentication provider type allows users to
    login using OAuth2 through Google.
    """

    type = "google"
    model_class = GoogleAuthenticationProviderModel
    allowed_fields = ["name", "client_id", "secret"]
    serializer_field_names = ["name", "client_id", "secret"]

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    SCOPE = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]
    ACCESS_TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"


class GitHubAuthenticationProviderType(
    OAuth2AuthProviderMixin, AuthenticationProviderType
):
    """
    The Github authentication provider type allows users to
    login using OAuth2 through Github.
    """

    type = "github"
    model_class = GitHubAuthenticationProviderModel
    allowed_fields = ["name", "client_id", "secret"]
    serializer_field_names = ["name", "client_id", "secret"]

    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    SCOPE = "read:user,user:email"
    GITHUB_API_URL = "https://api.github.com"

    def get_user_info(
        self, instance: GitHubAuthenticationProviderModel, code: str
    ) -> UserInfo:
        profile_url = "{0}/user".format(self.GITHUB_API_URL)
        emails_url = "{0}/user/emails".format(self.GITHUB_API_URL)
        access_token_url = "https://github.com/login/oauth/access_token"
        redirect_uri = urllib.parse.urljoin(
            OAUTH_BACKEND_URL,
            reverse("api:enterprise:sso:oauth2:callback", args=(instance.id,)),
        )
        oauth = OAuth2Session(
            instance.client_id, redirect_uri=redirect_uri, scope=self.SCOPE
        )
        token = oauth.fetch_token(
            access_token_url,
            code=code,
            client_secret=instance.secret,
        )
        r = oauth.get(profile_url)
        name = r.json().get("name", None)
        email = self.get_email(
            emails_url,
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


class GitLabAuthenticationProviderType(
    OAuth2AuthProviderMixin, AuthenticationProviderType
):
    """
    The GitLab authentication provider type allows users to
    login using OAuth2 through GitLab.
    """

    type = "gitlab"
    model_class = GitLabAuthenticationProviderModel
    allowed_fields = ["name", "url", "client_id", "secret"]
    serializer_field_names = ["name", "url", "client_id", "secret"]

    AUTHORIZATION_URL = "https://gitlab.com/oauth/authorize"
    SCOPE = ["read_user"]

    def get_authorization_url(
        self, instance: AuthenticationProviderModel, base_url: Optional[str]
    ) -> str:
        super().get_authorization_url(instance, instance.url)

    def get_user_info(
        self, instance: GitHubAuthenticationProviderModel, code: str
    ) -> UserInfo:
        access_token_url = "https://gitlab.com/oauth/token"
        redirect_uri = urllib.parse.urljoin(
            OAUTH_BACKEND_URL,
            reverse("api:enterprise:sso:oauth2:callback", args=(instance.id,)),
        )
        oauth = OAuth2Session(
            instance.client_id, redirect_uri=redirect_uri, scope=self.SCOPE
        )
        token = oauth.fetch_token(
            access_token_url,
            code=code,
            client_secret=instance.secret,
        )
        r = oauth.get("https://gitlab.com/api/v4/user")
        name = r.json().get("name", None)
        email = r.json().get("email", None)
        return UserInfo(name=name, email=email)


class FacebookAuthenticationProviderType(
    OAuth2AuthProviderMixin, AuthenticationProviderType
):
    """
    The Facebook authentication provider type allows users to
    login using OAuth2 through Facebook.
    """

    type = "facebook"
    model_class = FacebookAuthenticationProviderModel
    allowed_fields = ["name", "url", "client_id", "secret"]
    serializer_field_names = ["name", "url", "client_id", "secret"]

    AUTHORIZATION_URL = "https://www.facebook.com/dialog/oauth"
    SCOPE = ["email"]

    def get_authorization_url(
        self, instance: AuthenticationProviderModel, base_url: Optional[str]
    ) -> str:
        provider_id = instance.id
        redirect_uri = urllib.parse.urljoin(
            OAUTH_BACKEND_URL,
            reverse("api:enterprise:sso:oauth2:callback", args=(provider_id,)),
        )
        oauth = OAuth2Session(
            instance.client_id, redirect_uri=redirect_uri, scope=self.SCOPE
        )
        oauth = facebook_compliance_fix(oauth)
        authorization_url, state = oauth.authorization_url(self.AUTHORIZATION_URL)
        return authorization_url


class OpenIdConnectAuthenticationProviderType(
    OAuth2AuthProviderMixin, AuthenticationProviderType
):
    """
    The OpenId authentication provider type allows users to
    login using OAuth2 through OpenId Connect compatible provider.
    """

    type = "openid_connect"
    model_class = OpenIdConnectAuthenticationProviderModel
    allowed_fields = ["name", "url", "client_id", "secret"]
    serializer_field_names = ["name", "url", "client_id", "secret"]

    SCOPE = ["openid", "email", "profile"]

    def get_authorization_url(
        self, instance: AuthenticationProviderModel, base_url: Optional[str]
    ) -> str:
        super().get_authorization_url(instance, instance.url)
