from django.urls import re_path

from .views import (
    AdminAuditLogView,
    AdminAuditLogUserFilterView,
    AdminAuditLogGroupFilterView,
    AdminAuditLogEventTypeFilterView,
)

app_name = "baserow_enterprise.api.audit_log"

urlpatterns = [
    re_path(r"^$", AdminAuditLogView.as_view(), name="list"),
    re_path(r"users/$", AdminAuditLogUserFilterView.as_view(), name="users"),
    re_path(r"groups/$", AdminAuditLogGroupFilterView.as_view(), name="groups"),
    re_path(
        r"event-types/$", AdminAuditLogEventTypeFilterView.as_view(), name="event_types"
    ),
]
