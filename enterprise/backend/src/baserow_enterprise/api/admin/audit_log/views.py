from baserow_premium.api.admin.views import AdminListingView
from baserow_premium.license.handler import LicenseHandler
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser

from baserow_enterprise.audit_log.models import AuditLog
from baserow_enterprise.features import SSO

from .serializers import AuditLogSerializer


class AdminAuditLogView(AdminListingView):
    permission_classes = (IsAdminUser,)
    serializer_class = AuditLogSerializer
    search_fields = ["initial_user_email", "event_type"]
    sort_field_mapping = {
        "initial_user_email": "initial_user_email",
        "event_type": "event_type",
        "timestamp": "timestamp",
    }

    def get_queryset(self, request):
        return AuditLog.objects.only(
            "initial_user_email", "event_type", "timestamp", "description"
        )

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_audit_log",
        description="",
        **AdminListingView.get_extend_schema_parameters(
            "entries", serializer_class, search_fields, sort_field_mapping
        ),
    )
    def get(self, request):
        LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
            SSO, request.user
        )
        return super().get(request)
