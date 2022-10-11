from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from .sessions import set_user_session_data_from_request


class JSONWebTokenAuthentication(JWTAuthentication):
    def authenticate(self, request):
        """
        This method is basically a copy of
        rest_framework_simplejwt.authentication.JWTAuthentication.authenticate
        it adds a machine readable errors to the responses.

        Returns a two-tuple of `User` and token if a valid signature has been
        supplied using JWT-based authentication.  Otherwise returns `None`.
        """

        try:
            auth_response = super().authenticate(request)
            if auth_response is None:
                return None
            user, token = auth_response

        except InvalidToken:
            raise exceptions.AuthenticationFailed(
                {"detail": "Invalid token", "error": "ERROR_INVALID_TOKEN"}
            )

        set_user_session_data_from_request(user, request)

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
