from django.utils import translation
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.jobs.errors import ERROR_MAX_JOB_COUNT_EXCEEDED
from baserow.api.jobs.serializers import JobSerializer
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.core.jobs.exceptions import MaxJobCountExceeded
from baserow.core.jobs.handler import JobHandler
from baserow.core.jobs.registries import job_type_registry
from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from baserow_enterprise.audit_log.job_types import AuditLogExportJobType

from baserow_premium.api.admin.views import AdminListingView
from baserow_enterprise.audit_log.models import AuditLogEntry
from baserow_enterprise.features import SSO

from .serializers import (
    AuditLogSerializer,
    AuditLogUserSerializer,
    AuditLogGroupSerializer,
    AuditLogEventTypeSerializer,
    AuditLogExportJobRequestSerializer,
)

AuditLogExportJobSerializerClass = job_type_registry.get(
    AuditLogExportJobType.type
).get_serializer_class(base_class=JobSerializer)


class AdminAuditLogView(AdminListingView):
    permission_classes = (IsAdminUser,)
    serializer_class = AuditLogSerializer
    search_fields = ["user_email", "group_name", "event_type"]
    filters_field_mapping = {
        "user_email": "user_email",
        "group_name": "group_name",
        "event_type": "event_type",
        "from_date": "timestamp__date__gte",
        "to_date": "timestamp__date__lte",
    }
    sort_field_mapping = {
        "user_email": "user_email",
        "group_name": "group_name",
        "event_type": "event_type",
        "timestamp": "timestamp",
    }
    default_order_by = "-timestamp"

    def get_queryset(self, request):
        return AuditLogEntry.objects.all()

    def get_serializer(self, request, *args, **kwargs):
        return super().get_serializer(
            request, *args, context={"request": request}, **kwargs
        )

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_audit_log",
        description="",
        **AdminListingView.get_extend_schema_parameters(
            "audit_log_entries", serializer_class, search_fields, sort_field_mapping
        ),
    )
    def get(self, request):
        # LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
        #     SSO, request.user
        # )
        with translation.override(request.user.profile.language):
            return super().get(request)


class AdminAuditLogUserFilterView(AdminListingView):
    permission_classes = (IsAdminUser,)
    serializer_class = AuditLogUserSerializer
    search_fields = ["user_email"]
    default_order_by = "user_email"

    def get_queryset(self, request):
        return AuditLogEntry.objects.only(self.default_order_by).distinct(
            self.default_order_by
        )

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_audit_log_users",
        description="",
        **AdminListingView.get_extend_schema_parameters(
            "users", serializer_class, search_fields, {}
        ),
    )
    def get(self, request):
        # LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
        #     SSO, request.user
        # )
        return super().get(request)


class AdminAuditLogGroupFilterView(AdminListingView):
    permission_classes = (IsAdminUser,)
    serializer_class = AuditLogGroupSerializer
    search_fields = ["group_name"]
    default_order_by = "group_name"

    def get_queryset(self, request):
        return AuditLogEntry.objects.only(self.default_order_by).distinct(
            self.default_order_by
        )

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_audit_log_groups",
        description="",
        **AdminListingView.get_extend_schema_parameters(
            "groups", serializer_class, search_fields, {}
        ),
    )
    def get(self, request):
        # LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
        #     SSO, request.user
        # )
        return super().get(request)


class AdminAuditLogEventTypeFilterView(AdminListingView):
    permission_classes = (IsAdminUser,)
    serializer_class = AuditLogEventTypeSerializer
    search_fields = ["event_type"]
    default_order_by = "event_type"

    def get_queryset(self, request):
        return AuditLogEntry.objects.only(self.default_order_by).distinct(
            self.default_order_by
        )

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_audit_log_types",
        description="",
        **AdminListingView.get_extend_schema_parameters(
            "event_types", serializer_class, search_fields, {}
        ),
    )
    def get(self, request):
        # LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
        #     SSO, request.user
        # )

        with translation.override(request.user.profile.language):
            return super().get(request)


class AsyncAuditLogExportView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        parameters=[CLIENT_SESSION_ID_SCHEMA_PARAMETER],
        tags=["Audit log export"],
        operation_id="export_audit_log",
        description=("Creates a job to export the filtered audit log to a CSV file."),
        request=AuditLogExportJobRequestSerializer,
        responses={
            202: AuditLogExportJobSerializerClass,
            400: get_error_schema(
                ["ERROR_REQUEST_BODY_VALIDATION", "ERROR_MAX_JOB_COUNT_EXCEEDED"]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions({MaxJobCountExceeded: ERROR_MAX_JOB_COUNT_EXCEEDED})
    @validate_body(AuditLogExportJobRequestSerializer)
    def post(self, request, data):
        """Creates a job to export the filtered audit log entries to a CSV file."""

        csv_export_job = JobHandler().create_and_start_job(
            request.user, "audit_log_export", **data
        )

        serializer = job_type_registry.get_serializer(csv_export_job, JobSerializer)
        return Response(serializer.data)
