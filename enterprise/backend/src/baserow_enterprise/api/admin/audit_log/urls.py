from django.urls import re_path

from .views import AdminAuditLogView

app_name = "baserow_enterprise.api.sso"

urlpatterns = [
    re_path(r"^$", AdminAuditLogView.as_view(), name="list"),
]
