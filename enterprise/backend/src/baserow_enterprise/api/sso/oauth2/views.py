from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction

from django.shortcuts import redirect

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from baserow.core.user.exceptions import UserNotFound
from baserow.core.user.handler import UserHandler

from rest_framework.permissions import AllowAny

from baserow.core.registries import auth_provider_type_registry

from baserow.core.auth_provider.models import AuthProviderModel
from django.http import HttpResponseRedirect

from django.conf import settings


def get_or_create_user(email, first_name) -> AbstractBaseUser:
    try:
        # TODO: active user?
        user = UserHandler().get_active_user(email=email)
    except UserNotFound:
        with transaction.atomic():
            user = UserHandler().create_user(
                name=first_name, email=email, password=None
            )
    return user


def encode_token_for_user(user: AbstractBaseUser) -> str:
    return str(RefreshToken.for_user(user))


class OAuth2LoginView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, provider_id):
        instance = AuthProviderModel.objects.get(id=provider_id)
        provider_type = auth_provider_type_registry.get_by_model(
            instance.specific_class
        )
        redirect_url = provider_type.get_authorization_url(
            instance.specific_class.objects.get(id=provider_id)
        )
        return HttpResponseRedirect(redirect_to=redirect_url)


class OAuth2CallbackView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, provider_id):
        instance = AuthProviderModel.objects.get(id=provider_id)
        provider_type = auth_provider_type_registry.get_by_model(
            instance.specific_class
        )
        code = request.query_params.get("code")
        userinfo = provider_type.get_user_info(instance, code)
        user = get_or_create_user(userinfo.email, userinfo.name)
        jwt_token = encode_token_for_user(user)
        return redirect(settings.PUBLIC_WEB_FRONTEND_URL + f"?token={jwt_token}")
