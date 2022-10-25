import base64
import binascii
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from baserow_enterprise.api.sso.saml.errors import ERROR_SAML_INVALID_LOGIN_REQUEST
from baserow_enterprise.license.handler import has_active_enterprise_license
from baserow_enterprise.sso.saml.models import SamlAuthProviderModel
from defusedxml import ElementTree
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT, entity
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config
from saml2.response import AuthnResponse

from baserow.api.decorators import map_exceptions, validate_query_parameters
from baserow.api.schemas import get_error_schema
from baserow.core.user.exceptions import UserNotFound
from baserow.core.user.handler import UserHandler

from .exceptions import (
    InvalidSamlConfiguration,
    InvalidSamlRequest,
    InvalidSamlResponse,
)
from .serializers import SamlLoginRequestSerializer


ENTITY_ID_SAML_RESPONSE_TAG = "{urn:oasis:names:tc:SAML:2.0:assertion}Issuer"
REDIRECT_URL_ON_ERROR = settings.PUBLIC_WEB_FRONTEND_URL + "/login/error"


logger = logging.getLogger(__name__)


def redirect_to_frontend_error_page(message: Optional[str] = None) -> HttpResponse:
    """
    Redirects the user to the error page in the frontend providing a message
    as query parameter if provided.
    """

    frontend_error_page_url = REDIRECT_URL_ON_ERROR
    if message:
        frontend_error_page_url += "?" + urlencode({"message": message})
    return redirect(frontend_error_page_url)


def get_saml_client_for(
    saml_auth_provider: SamlAuthProviderModel, acs_url: str
) -> Saml2Client:
    """
    Returns a SAML client with the correct configuration for the given authentication
    provider.

    :param saml_auth_provider: The authentication provider that needs to be used to
        authenticate the user.
    :param acs_url: The url that should be used as the assertion consumer service url.
    :return: The SAML client that can be used to authenticate the user.
    """

    saml_settings: Dict[str, Any] = {
        "entityid": acs_url,
        "metadata": {"inline": [saml_auth_provider.metadata]},
        "allow_unknown_attributes": True,
        "debug": settings.DEBUG,
        "service": {
            "sp": {
                "endpoints": {
                    "assertion_consumer_service": [
                        (acs_url, BINDING_HTTP_REDIRECT),
                        (acs_url, BINDING_HTTP_POST),
                    ],
                },
                "allow_unsolicited": True,
                "authn_requests_signed": False,
                "logout_requests_signed": True,
                "want_assertions_signed": False,
                "want_response_signed": False,
            },
        },
    }
    sp_config = Saml2Config()
    sp_config.load(saml_settings)
    return Saml2Client(config=sp_config)


def check_authn_response_is_valid_or_raise(authn_response: AuthnResponse):
    """
    Checks if the authn response is valid and raises an exception if not.

    :param authn_response: The authn response that should be checked.
    :raises InvalidSamlResponse: When the authn response is not valid.
    :return: True if the authn response is valid.
    """

    if not authn_response:
        raise InvalidSamlResponse("There was no response from SAML identity provider.")

    if not authn_response.name_id:
        raise InvalidSamlResponse("No name_id in SAML response.")

    if not authn_response.issuer():
        raise InvalidSamlResponse("No issuer/entity_id in SAML response.")

    if not authn_response.get_identity():
        raise InvalidSamlResponse("No user identity in SAML response.")


def get_saml_auth_provider_from_saml_response(
    saml_raw_response: str,
) -> SamlAuthProviderModel:
    """
    Parses the saml response and returns the authentication provider that needs to
    be used to authenticate the user.

    :param saml_raw_response: The raw saml response that was received from the
        identity provider.
    :raises InvalidSamlConfiguration: When the correct authentication provider is
        not found in the system based on the information of saml response received.
    :return: The authentication provider that needs to be used to authenticate the
        user.
    """

    try:
        decoded_saml_response = ElementTree.fromstring(
            base64.b64decode(saml_raw_response).decode("utf-8")
        )
        issuer = decoded_saml_response.find(ENTITY_ID_SAML_RESPONSE_TAG).text
    except (binascii.Error, ElementTree.ParseError, AttributeError):
        raise InvalidSamlConfiguration("Impossible decode SAML response.")

    saml_auth_provider = SamlAuthProviderModel.objects.filter(
        enabled=True, metadata__contains=issuer
    ).first()
    if not saml_auth_provider:
        raise InvalidSamlConfiguration("Unknown SAML issuer.")
    return saml_auth_provider


def get_user_identity_from_authn_response(
    authn_response: AuthnResponse,
) -> Dict[str, Any]:
    """
    Extracts the user identity from the authn response and return a dict that
    can be sent to the UserHandler to create or update the user.

    :param authn_response: The authn response that contains the user identity.
    :return: A dictionary containing the user info that can be sent to the
        UserHandler.create_user() method.
    """

    user_identity = authn_response.get_identity()
    email = user_identity["user.email"][0]
    first_name = user_identity["user.first_name"][0]
    return {
        "email": email,
        "name": first_name,
    }


def get_valid_frontend_url(requested_original_url: str) -> str:
    """
    Returns a valid frontend url based on the original url requested before the
    redirection to the login. If the original url is relative, it will be
    prefixed with the frontend hostname to make the IdP redirection work. If the
    original url is external to Baserow, the default public frontend url will be
    returned instead.

    :param requested_original_url: The url to which the user should be
        redirected after a successful login.
    :return: The url with the token as a query parameter.
    """

    parsed_url = urlparse(requested_original_url)
    frontend_url = urlparse(settings.PUBLIC_WEB_FRONTEND_URL)

    if parsed_url.hostname is None:
        parsed_url = frontend_url._replace(path=parsed_url.path)
    if parsed_url.hostname != frontend_url.hostname:
        parsed_url = frontend_url

    return parsed_url.geturl()


def urlencode_token_as_query_params_for_user_session(url: str, token: str) -> str:
    """
    Adds the token as a query parameter to the url.

    :param url: The url to which the user should be redirected
        after a successful login.
    :param token: The token that should be added to the url.
    :return: The url with the token as a query parameter.
    """

    parsed_url = urlparse(url)
    return parsed_url._replace(query=f"token={token}").geturl()


def get_or_create_user_and_sign_in_via_saml_identity(
    user_info: Dict[str, Any], saml_auth_provider: SamlAuthProviderModel
) -> AbstractUser:
    """
    Gets from the database if present or creates a user if not, based on the
    user info that was received from the identity provider.

    :param user_info: A dictionary containing the user info that can be sent to
        the UserHandler.create_user() method.
    :param saml_auth_provider: The authentication provider that was used to
        authenticate the user.
    :return: The user that was created or updated.
    """

    user_handler = UserHandler()
    try:
        user = user_handler.get_active_user(email=user_info["email"])
        user_handler.user_signed_in_via_provider(user, saml_auth_provider)
    except UserNotFound:
        with transaction.atomic():
            # TODO: what about language, group invitation token and template?
            user = user_handler.create_user(
                **user_info,
                password=None,
                authentication_provider=saml_auth_provider,
            )
    return user


@method_decorator(csrf_exempt, name="dispatch")
class AssertionConsumerServiceView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        """
        This is the endpoint the SAML identity provider will call after the user
        has been authenticated there. If valid, the SAML response will contain
        the user's information needed to retrieve or create the user in the
        database. Once we have a valid user, a frontend url will be returned
        with the user's token as a query parameter so that the frontend can
        authenticate and start a new session for the user.
        """

        if not has_active_enterprise_license():
            return redirect_to_frontend_error_page(
                "SAML login is not available without a valid enterprise license."
            )

        saml_response = request.POST.get("SAMLResponse")
        if saml_response is None:
            return redirect_to_frontend_error_page(
                "SAML response is missing. Verify the SAML provider configuration."
            )

        try:
            saml_auth_provider = get_saml_auth_provider_from_saml_response(
                saml_response
            )
            acs_url = request.build_absolute_uri(reverse("api:enterprise:sso:saml:acs"))
            saml_client = get_saml_client_for(saml_auth_provider, acs_url)
            authn_response = saml_client.parse_authn_request_response(
                saml_response, entity.BINDING_HTTP_POST
            )
            check_authn_response_is_valid_or_raise(authn_response)
            user_info = get_user_identity_from_authn_response(authn_response)
        except Exception as exc:
            logger.exception(exc)
            return redirect_to_frontend_error_page(
                "An error occurred parsing the Identity Provider SAML response."
            )

        user = get_or_create_user_and_sign_in_via_saml_identity(
            user_info, saml_auth_provider
        )
        user_session_tokens = UserHandler().get_session_tokens_for_user(user)

        # since we correctly sign in a user, we can set this IdP as verified
        # This means it can be used as unique authentication provider form now on
        if not saml_auth_provider.is_verified:
            saml_auth_provider.is_verified = True
            saml_auth_provider.save()

        valid_frontend_url = get_valid_frontend_url(request.POST["RelayState"])
        redirect_url = urlencode_token_as_query_params_for_user_session(
            valid_frontend_url, user_session_tokens["refresh"]
        )
        return redirect(redirect_url)


def get_auth_provider(email: Optional[str] = None) -> SamlAuthProviderModel:
    """
    It returns the Saml Identity Provider for the the given email address.
    If the email address and only one IdP is configured, it returns that IdP.

    :param email: The email address of the user.
    :raises InvalidSamlRequest: If there is no Saml Identity Provider for the domain
        or the email is invalid.
    :return: The Saml Identity Provider for the domain of the email address.
    """

    base_queryset = SamlAuthProviderModel.objects.filter(enabled=True)

    if email is not None:
        try:
            domain = email.rsplit("@", 1)[1]
        except IndexError:
            raise InvalidSamlRequest("Invalid mail address provided.")
        base_queryset = base_queryset.filter(domain=domain)

    try:
        return base_queryset.get()
    except (
        SamlAuthProviderModel.DoesNotExist,
        SamlAuthProviderModel.MultipleObjectsReturned,
    ):
        raise InvalidSamlRequest("No valid SAML identity provider found.")


@method_decorator(csrf_exempt, name="dispatch")
class BaserowInitiatedSingleSignOn(View):
    def _get_redirect_url_to_saml_identity_provider(
        self,
        saml_auth_provider: SamlAuthProviderModel,
        acs_url: str,
        original_url: str,
    ) -> str:
        """
        Returns the redirect url to the identity provider. This url is used to
        initiate the SAML authentication flow from the service provider.

        :param saml_auth_provider: The identity provider to which the user
            should be redirected.
        :param acs_url: The assertion consumer service endpoint where the
            identity provider will send the SAML response.
        :param original_url: The url to which the user should be redirected
            after a successful login.
        :raises InvalidSamlConfiguration: If the SAML configuration is invalid.
        :return: The redirect url to the identity provider.
        """

        saml_client = get_saml_client_for(saml_auth_provider, acs_url)
        _, info = saml_client.prepare_for_authenticate(relay_state=original_url)

        for key, value in info["headers"]:
            if key == "Location":
                return value
        else:
            raise InvalidSamlConfiguration("No Location header found in SAML response.")

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        This is the endpoint that is called when the user wants to initiate the
        SSO SAML login from Baserow (the service provider). The user will be
        redirected to the SAML identity provider (IdP) where the user can
        authenticate. After the authentication the user will be redirected back
        to the assertion consumer service endpoint (ACS) where the SAML response
        will be validated and the user will be signed in.
        """

        if not has_active_enterprise_license():
            return redirect_to_frontend_error_page(
                "SAML login is not available without an enterprise license."
            )

        email = request.GET.get("email")
        original_request_url = request.GET.get("original", "")
        acs_url = request.build_absolute_uri(reverse("api:enterprise:sso:saml:acs"))

        try:
            saml_auth_provider = get_auth_provider(email)
            redirect_url = self._get_redirect_url_to_saml_identity_provider(
                saml_auth_provider, acs_url, original_request_url
            )
        except (InvalidSamlRequest, InvalidSamlConfiguration) as exc:
            logger.exception(exc)
            return redirect_to_frontend_error_page(
                "An error occurred before the redirection to the SAML identity provider."
            )

        return redirect(redirect_url)


class AdminAuthProvidersLoginUrlView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="email",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="The email address of the user that want to sign in using SAML.",
            ),
            OpenApiParameter(
                name="original",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description=(
                    "The url to which the user should be redirected after a successful login."
                ),
            ),
        ],
        tags=["Auth"],
        request=SamlLoginRequestSerializer,
        operation_id="auth_provider_login_url",
        description=(
            "Return the correct redirect_url to initiate the SSO SAML login. "
            "It needs an email address if multiple SAML providers are configured, "
            "Otherwise it will return the redirect_url for the only configured "
            "SAML provider."
        ),
        responses={
            200: Dict[str, str],
            400: get_error_schema(["ERROR_SAML_INVALID_LOGIN_REQUEST"]),
        },
        auth=[],
    )
    @transaction.atomic
    @validate_query_parameters(SamlLoginRequestSerializer, return_validated=True)
    @map_exceptions(
        {
            InvalidSamlRequest: ERROR_SAML_INVALID_LOGIN_REQUEST,
        }
    )
    def get(self, request, query_params):
        """Return the correct link for the SP initiated SAML login."""

        # check_active_enterprise_license(?)

        # check there is a valid SAML provider configured for the email provided
        get_auth_provider(query_params.get("email"))

        relative_url = reverse("api:enterprise:sso:saml:login")
        if query_params:
            # ensure the original requested url is relative
            original = urlparse(query_params.pop("original", ""))
            if original.hostname is None:
                query_params["original"] = original.geturl()

            relative_url = f"{relative_url}?{urlencode(query_params)}"

        return Response({"redirect_url": request.build_absolute_uri(relative_url)})
