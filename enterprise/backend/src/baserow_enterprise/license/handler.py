from django.core.exceptions import MultipleObjectsReturned

from baserow_enterprise.license.exceptions import NoEnterpriseLicenseError
from baserow_premium.license.models import License


def raise_if_instance_does_not_have_active_enterprise_license():
    """
    Raises a NoEnterpriseLicenseError if the current instance has does not have an
    active enterprise license.
    """

    try:
        current_license = License.objects.get()
    except MultipleObjectsReturned:
        raise NoEnterpriseLicenseError()

    if current_license.product_code != "enterprise" or not current_license.is_active:
        raise NoEnterpriseLicenseError()
