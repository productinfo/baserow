from rest_framework import serializers
from baserow.contrib.database.api.export.serializers import (
    SUPPORTED_CSV_COLUMN_SEPARATORS,
    SUPPORTED_EXPORT_CHARSETS,
    DisplayChoiceField,
)
from baserow.contrib.database.db.atomic import read_committed_single_table_transaction
from baserow.core.db import IsolationLevel, transaction_atomic

from baserow.core.jobs.registries import JobType
from baserow.core.utils import ChildProgressBuilder

from .models import AuditLogExportJob

BATCH_SIZE = 1024


class AuditLogExportJobType(JobType):
    type = "audit_log_export"
    model_class = AuditLogExportJob
    max_count = 1
    request_serializer_field_names = []
    request_serializer_field_overrides = {}

    serializer_field_names = [
        "export_charset",
        "csv_column_separator",
        "csv_include_header",
        "filter_user_email",
        "filter_group_name",
        "filter_event_type",
        "filter_start_date",
        "filter_end_date",
        "status",
        "exported_file",
    ]
    serializer_field_overrides = {
        # Map to the python encoding aliases at the same time by using a
        # DisplayChoiceField
        "export_charset": DisplayChoiceField(
            choices=SUPPORTED_EXPORT_CHARSETS,
            default="utf-8",
            help_text="The character set to use when creating the export file.",
        ),
        # For ease of use we expect the JSON to contain human typeable forms of each
        # different separator instead of the unicode character itself. By using the
        # DisplayChoiceField we can then map this to the actual separator character by
        # having those be the second value of each choice tuple.
        "csv_column_separator": DisplayChoiceField(
            choices=SUPPORTED_CSV_COLUMN_SEPARATORS,
            default=",",
            help_text="The value used to separate columns in the resulting csv file.",
        ),
        "csv_include_header": serializers.BooleanField(
            default=True,
            help_text="Whether or not to generate a header row at the top of the csv file.",
        ),
        "filter_user_email": serializers.CharField(
            required=False,
            help_text="Optional: The user to filter the audit log by.",
        ),
        "filter_group_name": serializers.CharField(
            required=False,
            help_text="Optional: The group to filter the audit log by.",
        ),
        "filter_event_type": serializers.CharField(
            required=False,
            help_text="Optional: The event type to filter the audit log by.",
        ),
        "filter_start_date": serializers.DateField(
            required=False,
            help_text="Optional: The start date to filter the audit log by.",
        ),
        "filter_end_date": serializers.DateField(
            required=False,
            help_text="Optional: The end date to filter the audit log by.",
        ),
        "status": serializers.CharField(read_only=True),
    }

    def prepare_values(self, values, user):
        """
        Filter data from the values dict. Data are going to be added later as a file.
        See `.after_job_creation()`.
        """

        return {"status": "pending", **values}

    def before_delete(self, job):
        """
        Try to delete the data file of a job before deleting the job.
        """

        try:
            job.exported_file.delete()
        except ValueError:
            # File doesn't exist, that's ok
            pass

    def transaction_atomic_context(self, job: AuditLogExportJob):
        """
        Protects the table and the fields from modifications while import is in
        progress.
        """

        return transaction_atomic(isolation_level=IsolationLevel.REPEATABLE_READ)

    def run(self, job, progress):
        """
        Export the filtered audit log entries to a CSV file.

        :param job: The job that is currently being executed.
        :progress: The progress object that can be used to update the progress bar.
        """

        job.save()

        import time

        # with _create_storage_dir_if_missing_and_open(storage_location) as file:
        #     queryset_serializer_class = exporter.queryset_serializer_class
        #     if job.view is None:
        #         serializer = queryset_serializer_class.for_table(job.table)
        #     else:
        #         serializer = queryset_serializer_class.for_view(job.view)

        #     serializer.write_to_file(
        #         PaginatedExportJobFileWriter(file, job), **job.export_options
        #     )

        for i in range(10):
            job.progress_percentage = i * 0.1
            job.save()
            time.sleep(1)

        job.save()
