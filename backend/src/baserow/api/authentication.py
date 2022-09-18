from typing import Optional, Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import (
    JWTAuthentication as JWTJSONWebTokenAuthentication,
)
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, Token

from baserow.api.sessions import (
    set_client_undo_redo_action_group_id_from_request_or_raise_if_invalid,
    set_untrusted_client_session_id_from_request_or_raise_if_invalid,
)


class JSONWebTokenAuthentication(JWTJSONWebTokenAuthentication):
    def get_token_from_request(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        return raw_token

    def authenticate(self, request):
        """
        This method is basically a copy of
        rest_framework_simplejwt.authentication.JWTAuthentication.authenticate
        it adds a machine readable errors to the responses.

        Returns a two-tuple of `User` and token if a valid signature has been
        supplied using JWT-based authentication.  Otherwise returns `None`.
        """

        token = self.get_token_from_request(request)
        if token is None:
            return None

        try:
            payload = self.get_validated_token(token)
        except InvalidToken:
            msg = "Invalid token."
            raise exceptions.AuthenticationFailed(
                {"detail": msg, "error": "ERROR_INVALID_TOKEN"}
            )

        user = self.get_user(payload)

        # @TODO this should actually somehow be moved to the ws app.
        user.web_socket_id = request.headers.get("WebSocketId")
        set_untrusted_client_session_id_from_request_or_raise_if_invalid(user, request)
        set_client_undo_redo_action_group_id_from_request_or_raise_if_invalid(
            user, request
        )

        return user, token


class JSONWebTokenAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "baserow.api.authentication.JSONWebTokenAuthentication"
    name = "JWT"
    match_subclasses = True
    priority = -1

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT your_token",
        }


def get_user_from_jwt_token(
    token: str, token_class: Optional[Type[Token]] = None
) -> AbstractBaseUser:
    """
    Returns the user that is associated with the given JWT token.

    :param token: The JWT token
    :return: The user that is associated with the token
    :raises TokenError: If the token is invalid or if the user does not exist.
    :raises User.DoesNotExist: If the user does not exist.
    """

    if token_class is None:
        token_class = AccessToken

    payload = token_class(token).token_backend.decode(token)
    user_id = payload.get(api_settings.USER_ID_CLAIM)
    return get_user_model().objects.get(pk=user_id)
