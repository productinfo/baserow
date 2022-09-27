import pytest
from django.test.utils import override_settings

from baserow_premium.license.registries import LicenseType


# @pytest.fixture()
# def mutable_license_type_registry():
#     from baserow_premium.license.registries import license_type_registry
#
#     before = license_type_registry.registry.copy()
#     yield license_type_registry
#     license_type_registry.registry = before
#


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_run_per_existing_license_hook_when_new_license_installed(data_fixture):
    user_in_license = data_fixture.create_user()

    class StubLicenseType(LicenseType):
        pass

    # mutable_license_type_registry.register(StubLicenseType())
