import base64
import binascii
import json
from typing import Any, Dict

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction

# from django.http import HttpRequest, HttpResponse
from rest_framework.request import Request
from rest_framework.response import Response
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.contenttypes.models import ContentType

from baserow.core.user.exceptions import UserNotFound
from baserow.core.user.handler import UserHandler

from rest_framework.permissions import AllowAny

import requests
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
from baserow.core.registries import authentication_provider_type_registry

from baserow.core.auth_provider.models import AuthenticationProviderModel
from django.http import HttpResponseRedirect

# Github specific
def get_email(url, headers):
    email = None
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    emails = resp.json()
    if resp.status_code == 200 and emails:
        email = emails[0]
        primary_emails = [
            e for e in emails if not isinstance(e, dict) or e.get("primary")
        ]
        if primary_emails:
            email = primary_emails[0]
        if isinstance(email, dict):
            email = email.get("email", "")
    return email


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
        instance = AuthenticationProviderModel.objects.get(id=provider_id)
        provider_type = authentication_provider_type_registry.get_by_model(
            instance.specific_class
        )
        redirect_url = provider_type.get_authorization_url(
            instance.specific_class.objects.get(id=provider_id)
        )
        return HttpResponseRedirect(redirect_to=redirect_url)


class OAuth2CallbackView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, provider_id):
        instance = AuthenticationProviderModel.objects.get(id=provider_id)
        provider_type = authentication_provider_type_registry.get_by_model(
            instance.specific_class
        )
        code = request.query_params.get("code")
        # TODO: sign in user after provider authorize him
        userinfo = provider_type.get_user_info(instance, code)
        user = get_or_create_user(userinfo.email, userinfo.name)
        jwt_token = encode_token_for_user(user)
        redirect_url = "http://localhost:3000"  # TODO:
        return redirect(redirect_url + f"?token={jwt_token}")


#         if provider_id == "0":
#             authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
#             access_token_url = "https://www.googleapis.com/oauth2/v4/token"
#             scope = [
#                 "openid",
#                 "https://www.googleapis.com/auth/userinfo.email",
#                 "https://www.googleapis.com/auth/userinfo.profile",
#             ]

#             client_id = "301549728349-a6rg277tvpt8r0u3vqutn38ri25rfbo1.apps.googleusercontent.com"
#             client_secret = "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"
#             base_url = "https://6f18-2a02-8308-a-5900-00-dd5.eu.ngrok.io"
#             callback_url = "/api/sso/oauth2/login/0/"
#             redirect_uri = base_url + callback_url

#             oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
#             authorization_url, state = oauth.authorization_url(
#                 authorize_url, access_type="offline", prompt="select_account"
#             )

#             token = oauth.fetch_token(
#                 access_token_url,
#                 code=code,
#                 client_secret=client_secret,
#             )

#             r = oauth.get("https://www.googleapis.com/oauth2/v1/userinfo")

#             name = r.json().get("name", None)
#             email = r.json().get("email", None)

#             user = get_or_create_user(email, name)

#             jwt_token = encode_token_for_user(user)

#             redirect_url = "http://localhost:3000"

#             # TODO: drf redirect instead
#             return redirect(redirect_url + f"?token={jwt_token}")

#         if provider_id == "1":

#             web_url = "https://github.com"
#             api_url = "https://api.github.com"
#             profile_url = "{0}/user".format(api_url)
#             emails_url = "{0}/user/emails".format(api_url)
#             access_token_url = "{0}/login/oauth/access_token".format(web_url)
#             authorize_url = "{0}/login/oauth/authorize".format(web_url)
#             scope = "read:user,user:email"

#             client_id = "3d8e919cb739d5203076"
#             client_secret = "be31a2fd16d5f239f0d6c0635942a50b183710ac"
#             base_url = "https://7258-2a02-8308-a-5900-00-dd5.eu.ngrok.io"
#             callback_url = "/api/sso/oauth2/login/1/"
#             redirect_uri = base_url + callback_url

#             oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)

#             token = oauth.fetch_token(
#                 access_token_url,
#                 code=code,
#                 client_secret=client_secret,
#             )

#             r = oauth.get(profile_url)
#             name = r.json().get("name", None)
#             email = get_email(
#                 emails_url,
#                 {"Authorization": "token {}".format(token.get("access_token"))},
#             )

#             user = get_or_create_user(email, name)

#             jwt_token = encode_token_for_user(user)

#             redirect_url = "http://localhost:3000"

#             # TODO: drf redirect instead
#             return redirect(redirect_url + f"?token={jwt_token}")

#         if provider_id == "3":
#             authorize_url = "https://gitlab.com/oauth/authorize"
#             access_token_url = "https://gitlab.com/oauth/token"
#             scope = ["read_user"]

#             client_id = (
#                 "923a758e46143335b68cbc02333cb950fcfcfa755c568dc2d0efbb7ff3b160c1"
#             )
#             client_secret = (
#                 "c1010f7e2d722ee9013bb6386c5f6178e57a567b9b364da4a9183bd09defa140"
#             )
#             base_url = "https://6f18-2a02-8308-a-5900-00-dd5.eu.ngrok.io"
#             callback_url = "/api/sso/oauth2/login/3/"
#             redirect_uri = base_url + callback_url

#             oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
#             authorization_url, state = oauth.authorization_url(authorize_url)

#             token = oauth.fetch_token(
#                 access_token_url,
#                 code=code,
#                 client_secret=client_secret,
#             )

#             r = oauth.get("https://gitlab.com/api/v4/user")

#             name = r.json().get("name", None)
#             email = r.json().get("email", None)

#             user = get_or_create_user(email, name)

#             jwt_token = encode_token_for_user(user)

#             redirect_url = "http://localhost:3000"

#             # TODO: drf redirect instead
#             return redirect(redirect_url + f"?token={jwt_token}")

#         if provider_id == "4":

#             authorize_url = "https://www.facebook.com/dialog/oauth"
#             access_token_url = "https://graph.facebook.com/oauth/access_token"

#             client_id = "1278353936264511"
#             client_secret = "da82cef4c2d98b87b828018e59b0d044"

#             base_url = "https://6f18-2a02-8308-a-5900-00-dd5.eu.ngrok.io"
#             callback_url = "/api/sso/oauth2/login/4/"
#             redirect_uri = base_url + callback_url

#             oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)
#             oauth = facebook_compliance_fix(oauth)

#             token = oauth.fetch_token(
#                 access_token_url,
#                 code=code,
#                 client_secret=client_secret,
#             )

#             r = oauth.get("https://graph.facebook.com/me?fields=id,email,name")

#             print(r.json())

#             name = r.json().get("name", None)
#             email = r.json().get("email", None)

#             user = get_or_create_user(email, name)

#             jwt_token = encode_token_for_user(user)

#             redirect_url = "http://localhost:3000"

#             # TODO: drf redirect instead
#             return redirect(redirect_url + f"?token={jwt_token}")

#         if provider_id == "10":

#             domain_url = "https://dev-18976703-admin.okta.com/oauth2/default"
#             wellknown_url = domain_url + "/.well-known/openid-configuration"
#             response = requests.get(wellknown_url)

#             scope = ["openid", "email", "profile"]

#             client_id = "0oa6tgvy1wLwemj0v5d7"
#             client_secret = "SV5EJFRQG9Cz4vendkrl3M8YME5PmdVCQkFPYF2E"

#             authorize_url = response.json()["authorization_endpoint"]
#             access_token_url = response.json()["token_endpoint"]
#             user_info_url = response.json()["userinfo_endpoint"]

#             base_url = "https://302c-2a02-8308-a-5900-00-dd5.eu.ngrok.io"
#             callback_url = "/api/sso/oauth2/login/10/"
#             redirect_uri = base_url + callback_url

#             oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
#             # authorization_url, state = oauth.authorization_url(authorize_url)

#             token = oauth.fetch_token(
#                 access_token_url,
#                 code=code,
#                 client_secret=client_secret,
#             )

#             r = oauth.get(user_info_url)

#             name = r.json().get("name", None)
#             email = r.json().get("email", None)

#             user = get_or_create_user(email, name)

#             jwt_token = encode_token_for_user(user)

#             redirect_url = "http://localhost:3000"

#             # TODO: drf redirect instead
#             return redirect(redirect_url + f"?token={jwt_token}")
