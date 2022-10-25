from django.urls import include, path

from .saml import urls as saml_urls
from .oauth2 import urls as oauth2_urls

app_name = "baserow_enterprise.api.sso"

urlpatterns = [
    path("saml/", include(saml_urls, namespace="saml")),
    path("oauth2/", include(oauth2_urls, namespace="oauth2")),
]
