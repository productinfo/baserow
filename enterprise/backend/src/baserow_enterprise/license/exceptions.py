from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_402_PAYMENT_REQUIRED


class NoEnterpriseLicenseError(APIException):
    """
    Raised when the instance does not have a valid enterprise license installed.
    """

    def __init__(self):
        super().__init__(
            {
                "error": "ERROR_NO_ACTIVE_ENTERPRISE_LICENSE",
                "detail": "Your Baserow instance does not have a valid enterprise "
                "license.",
            },
            code=HTTP_402_PAYMENT_REQUIRED,
        )
        self.status_code = HTTP_402_PAYMENT_REQUIRED
