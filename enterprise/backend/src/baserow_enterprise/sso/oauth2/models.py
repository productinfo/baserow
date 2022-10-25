from django.db import models

from baserow.core.auth_provider.models import AuthProviderModel

from django.db import models


class GoogleAuthProviderModel(AuthProviderModel):
    name = models.CharField(
        blank=True,
        max_length=191,
    )
    client_id = models.CharField(
        max_length=191,
        help_text="App ID, or consumer key",
    )
    secret = models.CharField(
        max_length=191,
        help_text="API secret, client secret, or consumer secret",
    )


class FacebookAuthProviderModel(AuthProviderModel):
    name = models.CharField(
        blank=True,
        max_length=191,
    )
    client_id = models.CharField(
        max_length=191,
        help_text="App ID, or consumer key",
    )
    secret = models.CharField(
        max_length=191,
        help_text="API secret, client secret, or consumer secret",
    )


class GitHubAuthProviderModel(AuthProviderModel):
    name = models.CharField(
        blank=True,
        max_length=191,
    )
    client_id = models.CharField(
        max_length=191,
        help_text="App ID, or consumer key",
    )
    secret = models.CharField(
        max_length=191,
        help_text="API secret, client secret, or consumer secret",
    )


class GitLabAuthProviderModel(AuthProviderModel):
    name = models.CharField(
        blank=True,
        max_length=191,
    )
    url = models.URLField(help_text="Base URL of the authorization server")
    client_id = models.CharField(
        max_length=191,
        help_text="App ID, or consumer key",
    )
    secret = models.CharField(
        max_length=191,
        help_text="API secret, client secret, or consumer secret",
    )


class OpenIdConnectAuthProviderModel(AuthProviderModel):
    name = models.CharField(
        blank=True,
        max_length=191,
    )
    url = models.URLField(help_text="Base URL of the authorization server")
    client_id = models.CharField(
        max_length=191,
        help_text="App ID, or consumer key",
    )
    secret = models.CharField(
        max_length=191,
        help_text="API secret, client secret, or consumer secret",
    )
