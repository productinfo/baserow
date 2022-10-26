from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction

from django.shortcuts import redirect

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from baserow.api.decorators import map_exceptions
from baserow.core.user.exceptions import UserNotFound
from baserow.core.user.handler import UserHandler
from baserow.api.schemas import get_error_schema
from rest_framework.permissions import AllowAny

from baserow.core.registries import auth_provider_type_registry

from baserow.core.auth_provider.models import AuthProviderModel
from django.http import HttpResponseRedirect
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from django.conf import settings
from baserow_enterprise.api.sso.errors import ERROR_AUTH_PROVIDER_DOES_NOT_EXIST
from baserow_enterprise.api.sso.exceptions import AuthProviderDoesNotExist

# TODO: Refactor into handler together with
#       get_or_create_user_and_sign_in_via_saml_identity
def get_or_create_user(
    email, first_name, auth_provider: AuthProviderModel
) -> AbstractBaseUser:
    user_handler = UserHandler()
    try:
        user = user_handler.get_active_user(email=email)
        user_handler.user_signed_in_via_provider(user, auth_provider)
    except UserNotFound:
        with transaction.atomic():
            user = user_handler.create_user(
                name=first_name,
                email=email,
                password=None,
                authentication_provider=auth_provider,
            )
    return user


# TODO: Refactor into handler
def encode_token_for_user(user: AbstractBaseUser) -> str:
    return str(RefreshToken.for_user(user))


class OAuth2LoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="provider_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the provider for which redirect.",
            ),
        ],
        tags=["Auth"],
        operation_id="oauth_provider_login_redirect",
        description=(
            "Redirects to the OAuth2 provider's authentication URL "
            "based on the provided auth provider's id."
        ),
        responses={
            301: None,
            404: get_error_schema(["ERROR_AUTH_PROVIDER_DOES_NOT_EXIST"]),
        },
        auth=[],
    )
    @map_exceptions(
        {
            AuthProviderDoesNotExist: ERROR_AUTH_PROVIDER_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def get(self, request, provider_id):
        """
        Redirects users to the authorization URL of the chosen provider
        to start OAuth2 login flow.
        """

        try:
            instance = AuthProviderModel.objects.get(id=provider_id)
        except AuthProviderModel.DoesNotExist:
            raise AuthProviderDoesNotExist
        # TODO: handle error
        provider_type = auth_provider_type_registry.get_by_model(
            instance.specific_class
        )
        redirect_url = provider_type.get_authorization_url(
            instance.specific_class.objects.get(id=provider_id)
        )
        return HttpResponseRedirect(redirect_to=redirect_url)


class OAuth2CallbackView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="provider_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The id of the provider for which to process the callback.",
            ),
            OpenApiParameter(
                name="code",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="The id of the provider for which to process the callback.",
            ),
        ],
        tags=["Auth"],
        operation_id="oauth_provider_login_callback",
        description=(
            "Processes callback from OAuth2 provider and "
            "logs the user in if successful."
        ),
        responses={
            301: None,
            404: get_error_schema(["ERROR_AUTH_PROVIDER_DOES_NOT_EXIST"]),
        },
        auth=[],
    )
    @map_exceptions(
        {
            AuthProviderDoesNotExist: ERROR_AUTH_PROVIDER_DOES_NOT_EXIST,
        }
    )
    @transaction.atomic
    def get(self, request, provider_id):
        """
        Processes callback from OAuth2 authentication provider by
        using the 'code' parameter to obtain tokens and query for user
        details. If successful, the user is given JWT token and is logged
        in.
        """

        try:
            instance = AuthProviderModel.objects.get(id=provider_id)
        except AuthProviderModel.DoesNotExist:
            raise AuthProviderDoesNotExist
        # TODO: handle error
        provider_type = auth_provider_type_registry.get_by_model(
            instance.specific_class
        )
        code = request.query_params.get("code")
        userinfo = provider_type.get_user_info(instance, code)
        user = get_or_create_user(userinfo.email, userinfo.name)
        jwt_token = encode_token_for_user(user)
        return redirect(settings.PUBLIC_WEB_FRONTEND_URL + f"?token={jwt_token}")
