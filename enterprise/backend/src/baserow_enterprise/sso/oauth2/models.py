from django.db import models

from baserow.core.auth_provider.models import AuthenticationProviderModel

from django.db import models


class OAuth2AuthenticationProviderMixin:
    ...
    # name = models.CharField(
    #     blank=True,
    #     max_length=191,
    # )
    # client_id = models.CharField(
    #     max_length=191,
    #     help_text="App ID, or consumer key",
    # )
    # secret = models.CharField(
    #     max_length=191,
    #     blank=True,
    #     help_text="API secret, client secret, or consumer secret",
    # )


class GoogleAuthenticationProviderModel(
    AuthenticationProviderModel, OAuth2AuthenticationProviderMixin
):
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


class FacebookAuthenticationProviderModel(
    AuthenticationProviderModel, OAuth2AuthenticationProviderMixin
):
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


class GitHubAuthenticationProviderModel(
    AuthenticationProviderModel, OAuth2AuthenticationProviderMixin
):
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


class GitLabAuthenticationProviderModel(
    AuthenticationProviderModel, OAuth2AuthenticationProviderMixin
):
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


class OpenIdConnectAuthenticationProviderModel(
    AuthenticationProviderModel, OAuth2AuthenticationProviderMixin
):
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
