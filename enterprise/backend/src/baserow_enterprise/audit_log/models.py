from django.db import models
from baserow.contrib.database.api.export.serializers import (
    SUPPORTED_CSV_COLUMN_SEPARATORS,
    SUPPORTED_EXPORT_CHARSETS,
)

from baserow.core.jobs.models import Job
from baserow_enterprise.registries import audit_log_type_registry

# If you ever change the return value of this function please duplicate the old
# version into migration enterprise.0010 and change that migration to use the duplicate
# to ensure this old migration doesn't logically change.
def file_import_directory_path(instance, filename):
    return f"user_{instance.user.id}/audit_log_export/job__{instance.id}.json"


class AuditLogEntry(models.Model):
    event_type = models.CharField(max_length=32, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    ip_address = models.GenericIPAddressField(null=True)

    user_id = models.PositiveIntegerField(db_index=True, null=True)
    user_email = models.CharField(max_length=150, db_index=True, null=True, blank=True)

    group_id = models.PositiveIntegerField(db_index=True, null=True)
    group_name = models.CharField(max_length=160, db_index=True, null=True, blank=True)

    data = models.JSONField(null=True)

    def get_type_description(self):
        event_type = audit_log_type_registry.get(self.event_type)
        return event_type.get_type_description(self)

    def get_event_description(self):
        event_type = audit_log_type_registry.get(self.event_type)
        return event_type.get_event_description(self)

    class Meta:
        ordering = ["-timestamp"]


class AuditLogExportJob(Job):
    export_charset = models.CharField(
        max_length=32,
        choices=SUPPORTED_EXPORT_CHARSETS,
        default="utf-8",
        help_text="The character set to use when creating the export file.",
    )
    # For ease of use we expect the JSON to contain human typeable forms of each
    # different separator instead of the unicode character itself. By using the
    # DisplayChoiceField we can then map this to the actual separator character by
    # having those be the second value of each choice tuple.
    csv_column_separator = models.CharField(
        max_length=32,
        choices=SUPPORTED_CSV_COLUMN_SEPARATORS,
        default=",",
        help_text="The value used to separate columns in the resulting csv file.",
    )
    csv_include_header = models.BooleanField(
        default=True,
        help_text="Whether or not to generate a header row at the top of the csv file.",
    )
    filter_user_email = models.CharField(
        max_length=150,
        null=True,
        help_text="Optional: The user to filter the audit log by.",
    )
    filter_group_name = models.CharField(
        max_length=160,
        null=True,
        help_text="Optional: The group to filter the audit log by.",
    )
    filter_event_type = models.CharField(
        max_length=32,
        null=True,
        help_text="Optional: The event type to filter the audit log by.",
    )
    filter_start_date = models.DateField(
        null=True,
        help_text="Optional: The start date to filter the audit log by.",
    )
    filter_end_date = models.DateField(
        null=True,
        help_text="Optional: The end date to filter the audit log by.",
    )
    exported_file = models.FileField(
        upload_to=file_import_directory_path,
        null=True,
        help_text="The CSV file containing the filtered audit log entries.",
    )
    status = models.CharField(
        max_length=32,
        default="complete",
        help_text="The status of the export job.",
    )
