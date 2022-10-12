from django.apps import AppConfig


class BaserowEnterpriseConfig(AppConfig):
    name = "baserow_enterprise"

    def ready(self):
        from baserow.core.registries import plugin_registry

        from .plugins import EnterprisePlugin

        plugin_registry.register(EnterprisePlugin())


        from baserow_enterprise.sso.saml.auth_provider_types import SamlAuthProviderType
        from baserow_enterprise.sso.oauth2.auth_provider_types import (
            GoogleAuthenticationProviderType,
            FacebookAuthenticationProviderType,
            GitHubAuthenticationProviderType,
            GitLabAuthenticationProviderType,
            OpenIdConnectAuthenticationProviderType,
        )

        from baserow.core.registries import auth_provider_type_registry

        auth_provider_type_registry.register(SamlAuthProviderType())

        auth_provider_type_registry.register(
            GoogleAuthenticationProviderType()
        )
        auth_provider_type_registry.register(
            FacebookAuthenticationProviderType()
        )
        auth_provider_type_registry.register(
            GitHubAuthenticationProviderType()
        )
        auth_provider_type_registry.register(
            GitLabAuthenticationProviderType()
        )
        auth_provider_type_registry.register(
            OpenIdConnectAuthenticationProviderType()
        )
