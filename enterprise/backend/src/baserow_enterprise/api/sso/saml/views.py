import base64
import binascii
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from baserow_enterprise.api.sso.saml.errors import ERROR_SAML_INVALID_LOGIN_REQUEST
from baserow_enterprise.sso.saml.models import SamlAuthProviderModel
from baserow_premium.license.handler import check_active_premium_license
from defusedxml import ElementTree
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT, entity
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config
from saml2.config import ConfigurationError

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

check_active_enterprise_license = check_active_premium_license

ENTITY_ID_SAML_RESPONSE_TAG = "{urn:oasis:names:tc:SAML:2.0:assertion}Issuer"
REDIRECT_URL_ON_ERROR = settings.PUBLIC_WEB_FRONTEND_URL + "/login/error"


def redirect_to_error_page_with_message(message: str) -> HttpResponse:
    return redirect(f"{REDIRECT_URL_ON_ERROR}?message={message}")


def get_saml_client_for(
    identity_provider: SamlAuthProviderModel, acs_url: str
) -> Saml2Client:

    saml_settings: Dict[str, Any] = {
        "entityid": acs_url,
        "metadata": {"inline": [identity_provider.metadata]},
        "allow_unknown_attributes": True,
        # "debug": True,
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


def check_authn_response_is_valid_or_raise(authn_response) -> bool:
    if not authn_response:
        raise InvalidSamlResponse("There was no response from SAML identity provider.")

    if not authn_response.name_id:
        raise InvalidSamlResponse("No name_id in SAML response.")

    if not authn_response.issuer():
        raise InvalidSamlResponse("No issuer/entity_id in SAML response.")

    if not authn_response.get_identity():
        raise InvalidSamlResponse("No user identity in SAML response.")

    return True


def get_identity_provider_from_saml_response(
    saml_response: str,
) -> SamlAuthProviderModel:
    try:
        decoded_saml_response = ElementTree.fromstring(
            base64.b64decode(saml_response).decode("utf-8")
        )
        issuer = decoded_saml_response.find(ENTITY_ID_SAML_RESPONSE_TAG).text
    except (binascii.Error, ElementTree.ParseError, AttributeError):
        raise InvalidSamlConfiguration("Impossible decode SAML response.")

    identity_provider = SamlAuthProviderModel.objects.filter(
        enabled=True, metadata__contains=issuer
    ).first()
    if not identity_provider:
        raise InvalidSamlConfiguration("Unknown SAML issuer.")
    return identity_provider


def get_user_identity_from_authn_response(authn_response) -> Dict[str, Any]:
    user_identity = authn_response.get_identity()
    email = user_identity["user.email"][0]
    first_name = user_identity["user.first_name"][0]
    return {
        "email": email,
        "name": first_name,
    }


def urlencode_token(requested_redirect_url: str, token: str) -> str:
    """
    Checks if the requested redirect url is a valid url and if so, adds the token
    as a query parameter to the url.
    """

    parsed_url = urlparse(requested_redirect_url)
    frontend_url = urlparse(settings.PUBLIC_WEB_FRONTEND_URL)
    if parsed_url.hostname is None:
        # add the hostname for a relative url
        parsed_url = frontend_url._replace(path=parsed_url.path)
    if parsed_url.hostname != frontend_url.hostname:
        # redirect to the homepage if an invalid hostname is provided
        parsed_url = frontend_url
    return parsed_url._replace(query=f"token={token}").geturl()


@method_decorator(csrf_exempt, name="dispatch")
class AssertionConsumerServiceView(View):
    def post(self, request: HttpRequest) -> HttpResponse:

        # TODO: check user license here or disable all the providers if the
        # license expires? TODO: should I check that the email address of the
        # user belongs to the configured domain?

        saml_response = request.POST.get("SAMLResponse")
        if saml_response is None:
            return redirect_to_error_page_with_message(
                "No SAMLResponse found in POST data."
            )

        try:
            identity_provider = get_identity_provider_from_saml_response(saml_response)
        except KeyError as exc:
            return redirect_to_error_page_with_message(str(exc))

        acs_url = request.build_absolute_uri(reverse("api:enterprise:sso:saml:acs"))
        try:
            saml_client = get_saml_client_for(identity_provider, acs_url)
        except ConfigurationError as exc:
            return redirect_to_error_page_with_message(str(exc))

        authn_response = saml_client.parse_authn_request_response(
            saml_response, entity.BINDING_HTTP_POST
        )
        try:
            check_authn_response_is_valid_or_raise(authn_response)
        except InvalidSamlResponse as exc:
            return redirect_to_error_page_with_message(str(exc))

        user_info = get_user_identity_from_authn_response(authn_response)
        user_handler = UserHandler()
        try:
            user = user_handler.get_active_user(email=user_info["email"])
            user_handler.user_signed_in_via_provider(user, identity_provider)
        except UserNotFound:
            with transaction.atomic():
                # TODO: what about language, group invitation token and template?
                user = user_handler.create_user(
                    **user_info,
                    password=None,
                    authentication_provider=identity_provider,
                )
        tokens = user_handler.get_session_tokens_for_user(user)

        # since we correctly sign in a user, we can set this IdP as verified
        # This means it can be used as unique authentication provider
        if not identity_provider.is_verified:
            identity_provider.is_verified = True
            identity_provider.save()

        redirect_url = urlencode_token(request.POST["RelayState"], tokens["refresh"])
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
    def _get_redirect_url_to_identity_provider(
        self,
        identity_provider: SamlAuthProviderModel,
        acs_url: str,
        original_url: str,
    ) -> str:
        """
        Returns the redirect url to the identity provider. This url is used to
        initiate the SAML authentication flow from the service provider.
        """

        saml_client = get_saml_client_for(identity_provider, acs_url)
        _, info = saml_client.prepare_for_authenticate(relay_state=original_url)
        # Select the identity_provider URL to send the AuthN request to
        for key, value in info["headers"]:
            if key == "Location":
                return value
        else:
            raise InvalidSamlConfiguration("No Location header found in SAML response.")

    def get(self, request: HttpRequest) -> HttpResponse:

        # TODO: check enterprise license

        email = request.GET.get("email")

        try:
            identity_provider = get_auth_provider(email)
        except InvalidSamlRequest as exc:
            return redirect_to_error_page_with_message(str(exc))

        original_url = request.GET.get("original", "")
        acs_url = request.build_absolute_uri(reverse("api:enterprise:sso:saml:acs"))

        try:
            redirect_url = self._get_redirect_url_to_identity_provider(
                identity_provider, acs_url, original_url
            )
        except InvalidSamlConfiguration as exc:
            return redirect_to_error_page_with_message(str(exc))

        return redirect(redirect_url)


class AdminAuthProvidersLoginUrlView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Auth"],
        request=SamlLoginRequestSerializer,
        operation_id="login_auth_provider",
        description=("Return the correct redirect_url to initiate the SAML login."),
        responses={
            200: Dict[str, str],
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

        # check if the email address is valid, otherwise raise an error
        get_auth_provider(query_params.get("email"))

        relative_url = reverse("api:enterprise:sso:saml:login")
        if query_params:
            relative_url = f"{relative_url}?{urlencode(query_params)}"

        return Response({"redirect_url": request.build_absolute_uri(relative_url)})
