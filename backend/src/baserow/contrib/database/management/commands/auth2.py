from django.core.management.base import BaseCommand

import requests
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix


class Command(BaseCommand):
    help = "Run oauth2"

    def handle(self, *args, **options):
        from django.urls import reverse

        # Github 1

        web_url = "https://github.com"
        api_url = "https://api.github.com"
        # profile_url = "{0}/user".format(api_url)
        # emails_url = "{0}/user/emails".format(api_url)
        # access_token_url = "{0}/login/oauth/access_token".format(web_url)
        authorize_url = "{0}/login/oauth/authorize".format(web_url)
        scope = "read:user,user:email"

        client_id = "3d8e919cb739d5203076"
        # client_secret = "be31a2fd16d5f239f0d6c0635942a50b183710ac"
        base_url = "https://7258-2a02-8308-a-5900-00-dd5.eu.ngrok.io"
        callback_url = "/api/sso/oauth2/login/1/"
        redirect_uri = base_url + callback_url

        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
        authorization_url, state = oauth.authorization_url(authorize_url)

        # print("Please go to %s and authorize access." % authorization_url)

        # *********************************

        # Google 0

        authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
        access_token_url = "https://www.googleapis.com/oauth2/v4/token"
        scope = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]

        client_id = (
            "301549728349-a6rg277tvpt8r0u3vqutn38ri25rfbo1.apps.googleusercontent.com"
        )
        # client_secret = "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"
        base_url = "https://6f18-2a02-8308-a-5900-00-dd5.eu.ngrok.io"
        callback_url = "/api/sso/oauth2/login/0/"
        redirect_uri = base_url + callback_url

        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
        authorization_url, state = oauth.authorization_url(authorize_url)

        # print("Please go to %s and authorize access." % authorization_url)

        # *************************************

        # Gitlab 3

        authorize_url = "https://gitlab.com/oauth/authorize"
        # access_token_url = "https://www.googleapis.com/oauth2/v4/token"
        scope = ["read_user"]
        client_id = "923a758e46143335b68cbc02333cb950fcfcfa755c568dc2d0efbb7ff3b160c1"
        # client_secret = (
        #     "c1010f7e2d722ee9013bb6386c5f6178e57a567b9b364da4a9183bd09defa140"
        # )
        base_url = "https://6f18-2a02-8308-a-5900-00-dd5.eu.ngrok.io"
        callback_url = "/api/sso/oauth2/login/3/"
        redirect_uri = base_url + callback_url

        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
        authorization_url, state = oauth.authorization_url(authorize_url)

        # print("Please go to %s and authorize access." % authorization_url)

        # *************************************

        # Facebook 4

        authorize_url = "https://www.facebook.com/dialog/oauth"
        # access_token_url = "https://graph.facebook.com/oauth/access_token"

        client_id = "1278353936264511"

        scope = ["email"]

        base_url = "https://6f18-2a02-8308-a-5900-00-dd5.eu.ngrok.io"
        callback_url = "/api/sso/oauth2/login/4/"
        redirect_uri = base_url + callback_url

        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
        oauth = facebook_compliance_fix(oauth)

        authorization_url, state = oauth.authorization_url(authorize_url)

        # print("Please go to %s and authorize access." % authorization_url)

        # OpenId Connect

        # /.well-known/openid-configuration
        # https://developer.okta.com/docs/reference/api/oidc/#well-known-openid-configuration
        # -> token_endpoint
        # -> authorization_endpoint
        # -> userinfo_endpoint

        domain_url = "https://dev-18976703-admin.okta.com/oauth2/default"
        wellknown_url = domain_url + "/.well-known/openid-configuration"

        response = requests.get(wellknown_url)
        print(response.json())

        scope = ["openid", "email", "profile"]

        client_id = "0oa6tgvy1wLwemj0v5d7"
        client_secret = "SV5EJFRQG9Cz4vendkrl3M8YME5PmdVCQkFPYF2E"

        authorize_url = response.json()["authorization_endpoint"]
        access_token_url = response.json()["token_endpoint"]
        user_info_url = response.json()["userinfo_endpoint"]

        print(authorize_url)
        print(access_token_url)
        print(user_info_url)

        base_url = "https://302c-2a02-8308-a-5900-00-dd5.eu.ngrok.io"
        callback_url = "/api/sso/oauth2/login/10/"
        redirect_uri = base_url + callback_url

        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
        # oauth = facebook_compliance_fix(oauth)

        authorization_url, state = oauth.authorization_url(authorize_url)

        print("Please go to %s and authorize access." % authorization_url)
