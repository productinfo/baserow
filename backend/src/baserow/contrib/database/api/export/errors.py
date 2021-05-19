from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

ERROR_EXPORT_JOB_DOES_NOT_EXIST = (
    "ERROR_EXPORT_JOB_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "That export job does not exist.",
)

ERROR_VIEW_UNSUPPORTED_FOR_EXPORT_TYPE = (
    "ERROR_VIEW_UNSUPPORTED_FOR_EXPORT_TYPE",
    HTTP_400_BAD_REQUEST,
    "You cannot export this view using that exporter type.",
)

TABLE_ONLY_EXPORT_UNSUPPORTED = (
    "TABLE_ONLY_EXPORT_UNSUPPORTED",
    HTTP_400_BAD_REQUEST,
    "This exporter type does not support exporting just the table.",
)


class ExportJobDoesNotExistException(Exception):
    pass
