from typing import Optional, Type

from django.contrib.auth.models import AbstractUser

from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import AccessToken, Token, TokenError


def get_user_from_jwt_token(
    token: str,
    token_class: Optional[Type[Token]] = None,
) -> AbstractUser:
    """
    Returns the active user that is associated with the given JWT token.

    :param token: The JWT token string
    :param token_class: The token class that must be used to decode the token.
    :param request: The request that is used to get the user data.
    :return: The user that is associated with the token
    :raises KeyError: When the USER_ID_CLAIM is missing in the token payload.
    :raises TokenError: If the token is invalid or if the user does not exist.
    """

    from baserow.core.user.handler import UserHandler, UserNotFound

    TokenClass = token_class or AccessToken
    user_id = TokenClass(token)[jwt_settings.USER_ID_CLAIM]
    try:
        # Prevent users to renew their token during the grace time.
        # This force a user to login again to have a new token.
        return UserHandler().get_active_user(
            user_id, exclude_users_scheduled_to_be_deleted=True
        )
    except UserNotFound:
        # It could happen if the user was deleted after the token was issued.
        raise TokenError("User does not exist.")
