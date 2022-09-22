from typing import Dict, Optional, Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

from rest_framework.request import Request
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, Token, TokenError

from baserow.api.user.registries import user_data_registry


def get_user_from_jwt_token(
    token: str,
    token_class: Optional[Type[Token]] = None,
) -> AbstractUser:
    """
    Returns the user that is associated with the given JWT token.

    :param token: The JWT token string
    :param token_class: The token class that must be used to decode the token.
    :param request: The request that is used to get the user data.
    :return: The user that is associated with the token
    :raises TokenError: If the token is invalid or if the user does not exist.
    """

    TokenClass = token_class or AccessToken
    payload = TokenClass(token).token_backend.decode(token)
    user_id = payload.get(api_settings.USER_ID_CLAIM)
    User = get_user_model()
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        # It could happen if the user was deleted after the token was issued.
        raise TokenError("User does not exist.")


def get_all_user_data_serialized(
    user: AbstractUser, request: Optional[Request] = None
) -> Dict:
    # Update the payload with the additional user data that must be added. The
    # `user_data_registry` contains instances that want to add additional information
    # to this payload.
    from baserow.api.user.serializers import UserSerializer

    return {
        "user": UserSerializer(user, context={"request": request}).data,
        **user_data_registry.get_all_user_data(user, request),
    }


def get_all_user_data_serialized_from_jwt_token(
    token: str,
    token_class: Optional[Type[Token]] = None,
    request: Optional[Request] = None,
) -> Dict:
    """
    Returns a dictionary with all the user data that is associated with the given JWT
    token.

    :param token: The JWT token string
    :param token_class: The token class that must be used to decode the token.
    :param request: The request that is used to get the user data.
    :return: The user data that is associated with the token
    """

    user = get_user_from_jwt_token(token, token_class)
    return get_all_user_data_serialized(user, request)
