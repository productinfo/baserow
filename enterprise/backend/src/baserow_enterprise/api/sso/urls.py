from django.urls import include, path

from .saml import urls as saml_urls
from .views import SSOProviderView, SSOProvidersView
from .oauth2 import urls as oauth2_urls

app_name = "baserow_enterprise.api.sso"

urlpatterns = [
    path("saml/", include(saml_urls, namespace="saml")),
    path("oauth2/", include(oauth2_urls, namespace="oauth2")),
    re_path(r"^$", SSOProvidersView.as_view(), name="list"),
    re_path(r"(?P<provider_id>[0-9]+)/$", SSOProviderView.as_view(), name="item"),
]
