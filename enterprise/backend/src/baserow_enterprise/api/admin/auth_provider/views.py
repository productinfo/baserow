from typing import Any, Dict
from urllib.request import Request

from baserow.api.auth_provider.serializers import AuthProviderSerializer
from baserow.api.decorators import map_exceptions, validate_body_custom_fields
from baserow.api.schemas import get_error_schema
from baserow.api.utils import (
    DiscriminatorCustomFieldsMappingSerializer,
    validate_data_custom_fields,
)
from baserow.core.auth_provider.exceptions import AuthProviderModelNotFound
from baserow.core.registries import auth_provider_type_registry
from baserow_enterprise.auth_provider.handler import AuthProviderHandler
from baserow_enterprise.license.handler import check_active_enterprise_license
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .errors import ERROR_AUTH_PROVIDER_DOES_NOT_EXIST
from .serializers import CreateAuthProviderSerializer, UpdateAuthProviderSerializer


class AdminAuthProvidersView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Auth"],
        request=None,
        operation_id="create_auth_provider",
        description=(
            "Creates a new authentication Provider. This can be used to enable "
            "authentication with a third party service like Google or Facebook."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                auth_provider_type_registry, AuthProviderSerializer
            ),
            400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION"]),
        },
    )
    @transaction.atomic
    @validate_body_custom_fields(
        auth_provider_type_registry,
        base_serializer_class=CreateAuthProviderSerializer,
    )
    def post(self, request: Request, data: Dict[str, Any]) -> Response:
        """Create a new Authentication Provider."""

        check_active_enterprise_license(request.user)

        provider_type = data.pop("type")
        auth_provider_type = auth_provider_type_registry.get(provider_type)
        with auth_provider_type.map_api_exceptions():
            provider = AuthProviderHandler().create_auth_provider(
                request.user, auth_provider_type, **data
            )

        return Response(
            auth_provider_type.get_serializer(provider, AuthProviderSerializer).data
        )

    @extend_schema(
        tags=["Auth"],
        request=None,
        operation_id="list_auth_providers",
        description=(
            "Verify if there is a authentication provider for the given email address and "
            "return information about the authentication completion."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                auth_provider_type_registry, AuthProviderSerializer, many=True
            )
        },
    )
    @transaction.atomic
    def get(self, request: Request) -> Response:
        """List all Authentication Providers."""

        check_active_enterprise_license(request.user)

        # TODO: move to handler
        auth_providers = []
        for auth_provider_type in auth_provider_type_registry.get_all():
            serialized_auth_provider_type = auth_provider_type.export_serialized()
            serialized_auth_provider_type["auth_providers"] = [
                auth_provider_type.get_serializer(provider, AuthProviderSerializer).data
                for provider in auth_provider_type.list_providers()
            ]
            auth_providers.append(serialized_auth_provider_type)
        return Response({"auth_provider_types": auth_providers})


class AdminAuthProviderView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Auth"],
        request=None,
        operation_id="update_auth_provider",
        description=(
            "Updates a new authentication Provider. This can be used to enable "
            "authentication with a third party service like Google or Facebook."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                auth_provider_type_registry, AuthProviderSerializer
            ),
            400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION"]),
            404: get_error_schema(["ERROR_AUTH_PROVIDER_DOES_NOT_EXIST"]),
        },
        auth=[],
    )
    @transaction.atomic
    @map_exceptions(
        {
            AuthProviderModelNotFound: ERROR_AUTH_PROVIDER_DOES_NOT_EXIST,
        }
    )
    def patch(self, request, auth_provider_id: int):
        """Update a new Authentication Provider."""

        check_active_enterprise_license(request.user)

        handler = AuthProviderHandler()
        provider = handler.get_auth_provider(auth_provider_id)
        provider_type = auth_provider_type_registry.get_by_model(provider)
        data = validate_data_custom_fields(
            provider_type.type,
            auth_provider_type_registry,
            request.data,
            base_serializer_class=UpdateAuthProviderSerializer,
        )
        with provider_type.map_api_exceptions():
            provider = handler.update_auth_provider(request.user, provider, **data)

        return Response(
            provider_type.get_serializer(provider, AuthProviderSerializer).data
        )

    @extend_schema(
        tags=["Auth"],
        request=None,
        operation_id="get_auth_providers",
        description=("Get an authentication provider."),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                auth_provider_type_registry, AuthProviderSerializer
            ),
            404: get_error_schema(["ERROR_AUTH_PROVIDER_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            AuthProviderModelNotFound: ERROR_AUTH_PROVIDER_DOES_NOT_EXIST,
        }
    )
    def get(self, request: Request, auth_provider_id: int) -> Response:
        """Get the requested Authentication Providers."""

        check_active_enterprise_license(request.user)

        provider = AuthProviderHandler().get_auth_provider(auth_provider_id)
        provider_type = auth_provider_type_registry.get_by_model(provider)
        return Response(
            provider_type.get_serializer(
                provider, base_class=AuthProviderSerializer
            ).data
        )

    @extend_schema(
        tags=["Auth"],
        request=None,
        operation_id="delete_auth_provider",
        description=("Delete an authentication provider."),
        responses={
            204: None,
            404: get_error_schema(["ERROR_AUTH_PROVIDER_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            AuthProviderModelNotFound: ERROR_AUTH_PROVIDER_DOES_NOT_EXIST,
        }
    )
    def delete(self, request: Request, auth_provider_id: int) -> Response:
        """Delete the requested authentication provider."""

        check_active_enterprise_license(request.user)

        handler = AuthProviderHandler()
        provider = handler.get_auth_provider(auth_provider_id)
        handler.delete_auth_provider(request.user, provider)
        return Response(status=204)
