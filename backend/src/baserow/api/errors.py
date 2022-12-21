from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_GROUP_DOES_NOT_EXIST = (
    "ERROR_GROUP_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested group does not exist.",
)
ERROR_USER_INVALID_GROUP_PERMISSIONS = (
    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
    HTTP_400_BAD_REQUEST,
    "You need {e.permissions} permissions.",
)
ERROR_USER_NOT_IN_GROUP = "ERROR_USER_NOT_IN_GROUP"
# These are not passwords
BAD_TOKEN_SIGNATURE = "BAD_TOKEN_SIGNATURE"  # nosec
EXPIRED_TOKEN_SIGNATURE = "EXPIRED_TOKEN_SIGNATURE"  # nosec
ERROR_HOSTNAME_IS_NOT_ALLOWED = (
    "ERROR_HOSTNAME_IS_NOT_ALLOWED",
    HTTP_400_BAD_REQUEST,
    "Only the hostname of the web frontend is allowed.",
)
ERROR_INVALID_SORT_DIRECTION = (
    "ERROR_INVALID_SORT_DIRECTION",
    HTTP_400_BAD_REQUEST,
    "Attributes to sort by must be prefixed with one of '-' or '+'.",
)
ERROR_INVALID_SORT_ATTRIBUTE = (
    "ERROR_INVALID_SORT_ATTRIBUTE",
    HTTP_400_BAD_REQUEST,
    "Invalid attribute name provided to sort by.",
)

ERROR_INVALID_FILTER_ATTRIBUTE = (
    "ERROR_INVALID_FILTER_ATTRIBUTE",
    HTTP_400_BAD_REQUEST,
    "Invalid attribute name provided to filter by.",
)
