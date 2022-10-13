from typing import Any, Dict, Type

from django.contrib.auth.models import AbstractUser

from baserow.core.auth_provider.auth_provider_types import AuthProviderType
from baserow.core.auth_provider.exceptions import AuthProviderModelNotFound
from baserow.core.auth_provider.models import AuthProviderModel
from baserow.core.registries import auth_provider_type_registry

SpecificAuthProviderModel = Type[AuthProviderModel]


class AuthProviderHandler:
    def get_auth_provider(self, auth_provider_id: int) -> SpecificAuthProviderModel:
        """
        Returns the authentication provider with the provided id.

        :param auth_provider_id: The id of the authentication provider.
        :raises AuthProviderModelNotFound: When the authentication provider does not
            exist.
        :return: The requested authentication provider.
        """

        try:
            return AuthProviderModel.objects.get(id=auth_provider_id).specific
        except AuthProviderModel.DoesNotExist:
            raise AuthProviderModelNotFound()

    def create_auth_provider(
        self,
        user: AbstractUser,
        auth_provider_type: Type[AuthProviderType],
        **values: Dict[str, Any]
    ) -> SpecificAuthProviderModel:
        """
        Creates a new authentication provider of the provided type.

        :param user: The user that is creating the authentication provider.
        :param auth_provider_type: The type of the authentication provider.
        :param values: The values that should be set on the authentication provider.
        :return: The created authentication provider.
        """

        auth_provider_type.before_create(user, **values)
        return auth_provider_type.create(**values)

    def update_auth_provider(
        self,
        user: AbstractUser,
        auth_provider: SpecificAuthProviderModel,
        **values: Dict[str, Any]
    ) -> SpecificAuthProviderModel:
        """
        Updates the authentication provider with the provided id.

        :param user: The user that is updating the authentication provider.
        :param auth_provider: The authentication provider that should be updated.
        :param values: The values that should be set on the authentication provider.
        :return: The updated authentication provider.
        """

        auth_provider_type = auth_provider_type_registry.get_by_model(auth_provider)
        auth_provider_type.before_update(user, auth_provider, **values)
        return auth_provider_type.update(auth_provider, **values)

    def delete_auth_provider(
        self, user: AbstractUser, auth_provider: AuthProviderModel
    ):
        """
        Deletes the authentication provider with the provided id. If the user is not
        allowed to delete the authentication provider then an error will be raised.

        :param user: The user that is deleting the authentication provider.
        :param auth_provider: The authentication provider that should be deleted.
        """

        auth_provider_type = auth_provider_type_registry.get_by_model(auth_provider)
        auth_provider_type.before_delete(user, auth_provider)
        auth_provider_type.delete(auth_provider)
