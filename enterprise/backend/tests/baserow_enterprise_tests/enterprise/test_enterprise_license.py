from unittest.mock import call, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext, override_settings

import pytest
import responses
from baserow_premium.api.user.user_data_types import ActiveLicensesDataType
from baserow_premium.license.exceptions import CantManuallyChangeSeatsError
from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from baserow_premium.license.registries import SeatUsageSummary
from freezegun import freeze_time
from responses import json_params_matcher

from baserow.api.user.registries import user_data_registry
from baserow.contrib.database.models import Database
from baserow.contrib.database.table.models import Table
from baserow.core.models import Application, Group, Settings
from baserow.core.registries import subject_type_registry
from baserow.core.trash.handler import TrashHandler
from baserow_enterprise.features import RBAC, SSO
from baserow_enterprise.license_types import EnterpriseLicenseType
from baserow_enterprise.role.default_roles import default_roles
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role, RoleAssignment
from baserow_enterprise.role.seat_usage_calculator import (
    RoleBasedSeatUsageSummaryCalculator,
)
from baserow_enterprise.teams.models import TeamSubject

PAID_COMMENTER_ROLE = "COMMENTER"

FREE_VIEWER_ROLE = "VIEWER"

VALID_ONE_SEAT_ENTERPRISE_LICENSE = (
    # id: "1", instance_id: "1"
    b"eyJ2ZXJzaW9uIjogMSwgImlkIjogIjUzODczYmVkLWJlNTQtNDEwZS04N2EzLTE2OTM2ODY2YjBiNiIsICJ2YWxpZF9mcm9tIjogIjIwMjItMTAtMDFUMDA6MDA6MDAiLCAidmFsaWRfdGhyb3VnaCI6ICIyMDY5LTA4LTA5VDIzOjU5OjU5IiwgInByb2R1Y3RfY29kZSI6ICJlbnRlcnByaXNlIiwgInNlYXRzIjogMSwgImlzc3VlZF9vbiI6ICIyMDIyLTEwLTI2VDE0OjQ4OjU0LjI1OTQyMyIsICJpc3N1ZWRfdG9fZW1haWwiOiAidGVzdEB0ZXN0LmNvbSIsICJpc3N1ZWRfdG9fbmFtZSI6ICJ0ZXN0QHRlc3QuY29tIiwgImluc3RhbmNlX2lkIjogIjEifQ==.B7aPXR0R4Fxr28AL7B5oopa2Yiz_MmEBZGdzSEHHLt4wECpnzjd_SF440KNLEZYA6WL1rhNkZ5znbjYIp6KdCqLdcm1XqNYOIKQvNTOtl9tUAYj_Qvhq1jhqSja-n3HFBjIh9Ve7a6T1PuaPLF1DoxSRGFZFXliMeJRBSzfTsiHiO22xRQ4GwafscYfUIWvIJJHGHtYEd9rk0tG6mfGEaQGB4e6KOsN-zw-bgLDBOKmKTGrVOkZnaGHBVVhUdpBn25r3CFWqHIApzUCo81zAA96fECHPlx_fBHhvIJXLsN5i3LdeJlwysg5SBO15Vt-tsdPmdcsec-fOzik-k3ib0A== "
)


@pytest.fixture(autouse=True)
def enable_roles_for_all_tests_here(synced_roles):
    pass


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_features_will_be_active_instance_wide_when_enterprise_active(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    assert LicenseHandler.instance_has_feature(RBAC)
    assert LicenseHandler.instance_has_feature(SSO)
    assert LicenseHandler.instance_has_feature(PREMIUM)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_users_not_assigned_a_seat_still_get_enterprise_features(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    assert LicenseHandler.user_has_feature_instance_wide(PREMIUM, user)
    assert LicenseHandler.user_has_feature_instance_wide(SSO, user)
    assert LicenseHandler.user_has_feature_instance_wide(RBAC, user)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_features_will_not_be_active_instance_wide_when_enterprise_not_active(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert not LicenseHandler.instance_has_feature(RBAC)
        assert not LicenseHandler.instance_has_feature(SSO)
        assert not LicenseHandler.instance_has_feature(PREMIUM)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_users_not_assigned_a_seat_dont_get_features_if_license_not_active(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert not LicenseHandler.user_has_feature_instance_wide(PREMIUM, user)
        assert not LicenseHandler.user_has_feature_instance_wide(SSO, user)
        assert not LicenseHandler.user_has_feature_instance_wide(RBAC, user)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_users_dont_get_features_if_license_inactive(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    license_object = LicenseHandler.register_license(
        user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
    )

    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert not LicenseHandler.user_has_feature_instance_wide(PREMIUM, user)
        assert not LicenseHandler.user_has_feature_instance_wide(SSO, user)
        assert not LicenseHandler.user_has_feature_instance_wide(RBAC, user)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_anonymous_user_data_has_no_enterprise_license_when_not_active(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert al.get_user_data(AnonymousUser(), None) == {
            "instance_wide": {},
            "per_group": {},
        }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_anonymous_user_data_enables_enterprise_features_instance_wide(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    assert al.get_user_data(AnonymousUser(), None) == {
        "instance_wide": {"enterprise": True},
        "per_group": {},
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_random_user_user_data_has_no_enterprise_license_when_not_active(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    random_user = data_fixture.create_user()
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert al.get_user_data(random_user, None) == {
            "instance_wide": {},
            "per_group": {},
        }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_random_user_data_enables_enterprise_features_instance_wide(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    random_user = data_fixture.create_user()
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    assert al.get_user_data(random_user, None) == {
        "instance_wide": {"enterprise": True},
        "per_group": {},
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_license_user_user_data_has_no_enterprise_license_when_not_active(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    license_obj = LicenseHandler.register_license(
        user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
    )

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert al.get_user_data(user, None) == {
            "instance_wide": {},
            "per_group": {},
        }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enabling_enterprise_user_data_gets_enterprise_features_instance_wide(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    license_obj = LicenseHandler.register_license(
        user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
    )

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    assert al.get_user_data(user, None) == {
        "instance_wide": {"enterprise": True},
        "per_group": {},
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_data_no_enterprise_features_instance_wide_not_active(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert al.get_user_data(user, None) == {
            "instance_wide": {},
            "per_group": {},
        }


@pytest.mark.django_db
@override_settings(DEBUG=True)
@responses.activate
def test_check_licenses_with_enterprise_license_sends_seat_data(
    enterprise_data_fixture,
):
    license_object = enterprise_data_fixture.enable_enterprise()

    with freeze_time("2021-07-01 12:00"):
        responses.add(
            responses.POST,
            "http://baserow-saas-backend:8000/api/saas/licenses/check/",
            json={
                VALID_ONE_SEAT_ENTERPRISE_LICENSE.decode(): {
                    "type": "ok",
                    "detail": "",
                },
            },
            match=[
                json_params_matcher(
                    {
                        "licenses": [VALID_ONE_SEAT_ENTERPRISE_LICENSE.decode()],
                        "instance_id": Settings.objects.get().instance_id,
                        "extra_license_info": [
                            {
                                "id": license_object.id,
                                "free_users_count": 0,
                                "seats_taken": 1,
                            }
                        ],
                    }
                )
            ],
            status=200,
        )

        LicenseHandler.check_licenses([license_object])

    responses.assert_call_count(
        "http://baserow-saas-backend:8000/api/saas/licenses/check/", 1
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_license_counts_viewers_as_free(
    enterprise_data_fixture, data_fixture
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    user3 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user2, user3])

    table = data_fixture.create_database_table(user=user)

    admin_role = Role.objects.get(uid="ADMIN")
    viewer_role = Role.objects.get(uid="VIEWER")

    role_assignment_handler = RoleAssignmentHandler()

    assert len(RoleAssignment.objects.all()) == 0

    role_assignment_handler.assign_role(user, group, admin_role)
    role_assignment_handler.assign_role(user2, group, viewer_role)
    role_assignment_handler.assign_role(user3, group, viewer_role)

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=2,
        num_users_with_highest_role={
            "ADMIN": 1,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 2,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_who_is_commenter_in_one_group_and_viewer_in_another_is_not_free(
    enterprise_data_fixture, data_fixture
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    group1 = data_fixture.create_group(user=user, members=[user2])
    group2 = data_fixture.create_group(user=user, members=[user2])

    admin_role = Role.objects.get(uid="ADMIN")
    commenter_role = Role.objects.get(uid="COMMENTER")
    viewer_role = Role.objects.get(uid="VIEWER")

    role_assignment_handler = RoleAssignmentHandler()

    role_assignment_handler.assign_role(user, group1, admin_role)
    role_assignment_handler.assign_role(user2, group1, viewer_role)
    role_assignment_handler.assign_role(user, group2, admin_role)
    role_assignment_handler.assign_role(user2, group2, commenter_role)

    assert len(RoleAssignment.objects.all()) == 0

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=2,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 1,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_marked_for_deletion_is_not_counted_as_a_paid_user(
    enterprise_data_fixture, data_fixture
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    group1 = data_fixture.create_group(user=user, members=[user2])
    group2 = data_fixture.create_group(user=user, members=[user2])

    admin_role = Role.objects.get(uid="ADMIN")
    commenter_role = Role.objects.get(uid="COMMENTER")
    viewer_role = Role.objects.get(uid="VIEWER")

    role_assignment_handler = RoleAssignmentHandler()

    role_assignment_handler.assign_role(user, group1, admin_role)
    role_assignment_handler.assign_role(user2, group1, viewer_role)
    role_assignment_handler.assign_role(user, group2, admin_role)
    role_assignment_handler.assign_role(user2, group2, commenter_role)

    assert len(RoleAssignment.objects.all()) == 0

    user2.profile.to_be_deleted = True
    user2.profile.save()

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 1,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_deactivated_user_is_not_counted_as_a_paid_user(
    enterprise_data_fixture, data_fixture
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    group1 = data_fixture.create_group(user=user, members=[user2])
    group2 = data_fixture.create_group(user=user, members=[user2])

    admin_role = Role.objects.get(uid="ADMIN")
    commenter_role = Role.objects.get(uid="COMMENTER")
    builder_role = Role.objects.get(uid="BUILDER")

    role_assignment_handler = RoleAssignmentHandler()

    role_assignment_handler.assign_role(user, group1, admin_role)
    role_assignment_handler.assign_role(user2, group1, builder_role)
    role_assignment_handler.assign_role(user, group2, admin_role)
    role_assignment_handler.assign_role(user2, group2, commenter_role)

    user2.is_active = False
    user2.save()

    assert len(RoleAssignment.objects.all()) == 0

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 1,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_manually_add_seats_to_enterprise_version(
    enterprise_data_fixture, data_fixture
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user(is_staff=True)
    user2 = data_fixture.create_user()
    data_fixture.create_group(user=user, members=[user2])
    with pytest.raises(CantManuallyChangeSeatsError):
        LicenseHandler.add_user_to_license(user, license_object, user2)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_manually_remove_seats_from_enterprise_version(
    enterprise_data_fixture, data_fixture
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user(is_staff=True)
    user2 = data_fixture.create_user()
    data_fixture.create_group(user=user, members=[user2])
    with pytest.raises(CantManuallyChangeSeatsError):
        LicenseHandler.remove_user_from_license(user, license_object, user2)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_manually_add_all_users_to_seats_in_enterprise_version(
    enterprise_data_fixture, data_fixture
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user(is_staff=True)
    user2 = data_fixture.create_user()
    data_fixture.create_group(user=user, members=[user2])
    with pytest.raises(CantManuallyChangeSeatsError):
        LicenseHandler.fill_remaining_seats_of_license(user, license_object)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_manually_remove_all_users_from_seats_in_enterprise_version(
    enterprise_data_fixture, data_fixture
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user(is_staff=True)
    user2 = data_fixture.create_user()
    data_fixture.create_group(user=user, members=[user2])
    with pytest.raises(CantManuallyChangeSeatsError):
        LicenseHandler.remove_all_users_from_license(user, license_object)


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow_premium.license.handler.broadcast_to_users")
def test_enterprise_license_being_registered_sends_signal_to_all(
    mock_broadcast_to_users, data_fixture, django_capture_on_commit_callbacks
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    with django_capture_on_commit_callbacks(execute=True):
        LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)
    mock_broadcast_to_users.delay.assert_called_once()
    args = mock_broadcast_to_users.delay.call_args
    assert args == call(
        send_to_all_users=True,
        user_ids=[],
        payload={
            "type": "user_data_updated",
            "user_data": {"active_licenses": {"instance_wide": {"enterprise": True}}},
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow_premium.license.handler.broadcast_to_users")
def test_enterprise_license_being_unregistered_sends_signal_to_all(
    mock_broadcast_to_users, data_fixture, django_capture_on_commit_callbacks
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    with django_capture_on_commit_callbacks(execute=True):
        license_obj = LicenseHandler.register_license(
            user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
        )
        LicenseHandler.remove_license(user, license_obj)
    args = mock_broadcast_to_users.delay.call_args
    assert mock_broadcast_to_users.delay.call_count == 2
    assert args == call(
        send_to_all_users=True,
        user_ids=[],
        payload={
            "type": "user_data_updated",
            "user_data": {"active_licenses": {"instance_wide": {"enterprise": False}}},
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_paid_table_role_is_not_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    RoleAssignmentHandler().assign_role(
        user, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=table
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_free_table_role_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    RoleAssignmentHandler().assign_role(
        user, group, role=Role.objects.get(uid=FREE_VIEWER_ROLE), scope=table
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_paid_database_role_is_not_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    RoleAssignmentHandler().assign_role(
        user, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=database
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_free_database_role_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    RoleAssignmentHandler().assign_role(
        user, group, role=Role.objects.get(uid=FREE_VIEWER_ROLE), scope=database
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_paid_table_role_is_not_free_from_team(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=table
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_free_table_role_is_free_from_team(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=FREE_VIEWER_ROLE), scope=table
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_paid_database_role_is_not_free_from_team(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=database
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_free_database_role_is_free_from_team(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=FREE_VIEWER_ROLE), scope=database
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_in_deleted_team_with_paid_role_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=database
    )

    TrashHandler().trash(user, group, None, team)

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_inactive_user_with_paid_role_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    RoleAssignmentHandler().assign_role(
        user, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=database
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )

    user.is_active = False
    user.save()

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_inactive_user_in_team_with_paid_role_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=database
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )

    user.is_active = False
    user.save()

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_to_be_deleted_with_paid_role_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    RoleAssignmentHandler().assign_role(
        user, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=database
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )

    user.profile.to_be_deleted = True
    user.profile.save()

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_to_be_deleted_in_team_with_paid_role_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=database
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )

    user.profile.to_be_deleted = True
    user.profile.save()

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_complex_free_vs_paid_scenario(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user1_paid_in_grp1 = data_fixture.create_user()
    user2_free_in_grp1_paid_grp2 = data_fixture.create_user()
    user3_free_both_grps = data_fixture.create_user()
    group1 = data_fixture.create_group()
    group2 = data_fixture.create_group()
    data_fixture.create_user_group(
        user=user1_paid_in_grp1, group=group1, permissions=PAID_COMMENTER_ROLE
    )
    data_fixture.create_user_group(
        user=user2_free_in_grp1_paid_grp2, group=group1, permissions=FREE_VIEWER_ROLE
    )
    data_fixture.create_user_group(
        user=user2_free_in_grp1_paid_grp2, group=group2, permissions=PAID_COMMENTER_ROLE
    )
    data_fixture.create_user_group(
        user=user3_free_both_grps, group=group1, permissions=FREE_VIEWER_ROLE
    )
    data_fixture.create_user_group(
        user=user3_free_both_grps, group=group2, permissions=FREE_VIEWER_ROLE
    )
    database1 = data_fixture.create_database_application(group=group1)
    table1 = data_fixture.create_database_table(database=database1)

    grp1_team_with_paid_role_on_db = enterprise_data_fixture.create_team(group=group1)
    grp1_team_with_no_roles = enterprise_data_fixture.create_team(group=group1)
    grp2_team_with_free_roles = enterprise_data_fixture.create_team(group=group2)

    enterprise_data_fixture.create_subject(
        team=grp1_team_with_paid_role_on_db, subject=user1_paid_in_grp1
    )
    enterprise_data_fixture.create_subject(
        team=grp1_team_with_paid_role_on_db, subject=user2_free_in_grp1_paid_grp2
    )
    enterprise_data_fixture.create_subject(
        team=grp1_team_with_no_roles, subject=user2_free_in_grp1_paid_grp2
    )
    enterprise_data_fixture.create_subject(
        team=grp2_team_with_free_roles, subject=user3_free_both_grps
    )

    RoleAssignmentHandler().assign_role(
        grp1_team_with_paid_role_on_db,
        group1,
        role=Role.objects.get(uid=FREE_VIEWER_ROLE),
        scope=database1,
    )
    RoleAssignmentHandler().assign_role(
        grp1_team_with_paid_role_on_db,
        group1,
        role=Role.objects.get(uid=PAID_COMMENTER_ROLE),
        scope=table1,
    )
    RoleAssignmentHandler().assign_role(
        grp2_team_with_free_roles,
        group2,
        role=Role.objects.get(uid=FREE_VIEWER_ROLE),
        scope=group2,
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=2,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 2,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_role_paid_on_trashed_database_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    RoleAssignmentHandler().assign_role(
        user, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=database
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )

    TrashHandler().trash(user, group, database, database)

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_role_paid_on_database_in_trashed_group_is_free(
    enterprise_data_fixture, data_fixture, synced_roles, django_assert_num_queries
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    RoleAssignmentHandler().assign_role(
        user, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=table
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )

    TrashHandler().trash(user, group, None, group)

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_role_paid_on_trashed_table_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    RoleAssignmentHandler().assign_role(
        user, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=table
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )

    TrashHandler().trash(user, group, database, table)

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_in_team_with_role_paid_on_trashed_database_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=database
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )

    TrashHandler().trash(user, group, database, database)

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_in_team_with_role_paid_on_trashed_table_is_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=table
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )

    TrashHandler().trash(user, group, database, table)

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_summary_calculation_for_enterprise_doesnt_do_n_plus_one_queries(
    enterprise_data_fixture, data_fixture, synced_roles, django_assert_num_queries
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()

    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)

    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=table
    )

    # Make sure the content type cached properties contain these models so we don't
    # count that query in the get_seat_usage_summary below
    ContentType.objects.get_for_models(Database, Application)

    with CaptureQueriesContext(connection) as first_query:
        assert EnterpriseLicenseType().get_seat_usage_summary(
            license_object
        ) == SeatUsageSummary(
            seats_taken=1,
            free_users_count=0,
            num_users_with_highest_role={
                "ADMIN": 0,
                "BUILDER": 0,
                "EDITOR": 0,
                "COMMENTER": 1,
                "VIEWER": 0,
                "NO_ACCESS": 0,
                "NO_ROLE_LOW_PRIORITY": 0,
            },
        )

    user2 = data_fixture.create_user()
    group2 = data_fixture.create_group()
    data_fixture.create_user_group(
        user=user2, group=group, permissions=FREE_VIEWER_ROLE
    )
    data_fixture.create_user_group(
        user=user2, group=group2, permissions=FREE_VIEWER_ROLE
    )
    data_fixture.create_user_group(
        user=user, group=group2, permissions=PAID_COMMENTER_ROLE
    )
    database2 = data_fixture.create_database_application(group=group2)
    table2 = data_fixture.create_database_table(database=database2)
    team2 = enterprise_data_fixture.create_team(group=group2)
    enterprise_data_fixture.create_subject(team=team2, subject=user2)
    enterprise_data_fixture.create_subject(team=team, subject=user)
    enterprise_data_fixture.create_subject(team=team2, subject=user)
    RoleAssignmentHandler().assign_role(
        team2, group2, role=Role.objects.get(uid="ADMIN"), scope=table2
    )

    with django_assert_num_queries(len(first_query.captured_queries)):
        assert EnterpriseLicenseType().get_seat_usage_summary(
            license_object
        ) == SeatUsageSummary(
            seats_taken=2,
            free_users_count=0,
            num_users_with_highest_role={
                "ADMIN": 2,
                "BUILDER": 0,
                "EDITOR": 0,
                "COMMENTER": 0,
                "VIEWER": 0,
                "NO_ACCESS": 0,
                "NO_ROLE_LOW_PRIORITY": 0,
            },
        )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_can_query_for_summary_per_group(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user1_paid_in_grp1 = data_fixture.create_user()
    user2_free_in_grp1_paid_grp2 = data_fixture.create_user()
    user3_free_both_grps = data_fixture.create_user()
    group1 = data_fixture.create_group()
    group2 = data_fixture.create_group()
    data_fixture.create_user_group(
        user=user1_paid_in_grp1, group=group1, permissions=PAID_COMMENTER_ROLE
    )
    data_fixture.create_user_group(
        user=user2_free_in_grp1_paid_grp2, group=group1, permissions=FREE_VIEWER_ROLE
    )
    data_fixture.create_user_group(
        user=user2_free_in_grp1_paid_grp2, group=group2, permissions=PAID_COMMENTER_ROLE
    )
    data_fixture.create_user_group(
        user=user3_free_both_grps, group=group1, permissions=FREE_VIEWER_ROLE
    )
    data_fixture.create_user_group(
        user=user3_free_both_grps, group=group2, permissions=FREE_VIEWER_ROLE
    )
    database1 = data_fixture.create_database_application(group=group1)
    table1 = data_fixture.create_database_table(database=database1)

    grp1_team_with_paid_role_on_db = enterprise_data_fixture.create_team(group=group1)
    grp1_team_with_no_roles = enterprise_data_fixture.create_team(group=group1)
    grp2_team_with_free_roles = enterprise_data_fixture.create_team(group=group2)

    enterprise_data_fixture.create_subject(
        team=grp1_team_with_paid_role_on_db, subject=user1_paid_in_grp1
    )
    enterprise_data_fixture.create_subject(
        team=grp1_team_with_paid_role_on_db, subject=user2_free_in_grp1_paid_grp2
    )
    enterprise_data_fixture.create_subject(
        team=grp1_team_with_no_roles, subject=user2_free_in_grp1_paid_grp2
    )
    enterprise_data_fixture.create_subject(
        team=grp2_team_with_free_roles, subject=user3_free_both_grps
    )

    RoleAssignmentHandler().assign_role(
        grp1_team_with_paid_role_on_db,
        group1,
        role=Role.objects.get(uid=FREE_VIEWER_ROLE),
        scope=database1,
    )
    RoleAssignmentHandler().assign_role(
        grp1_team_with_paid_role_on_db,
        group1,
        role=Role.objects.get(uid=PAID_COMMENTER_ROLE),
        scope=table1,
    )
    RoleAssignmentHandler().assign_role(
        grp2_team_with_free_roles,
        group2,
        role=Role.objects.get(uid=FREE_VIEWER_ROLE),
        scope=group2,
    )

    assert RoleBasedSeatUsageSummaryCalculator.get_seat_usage_for_group(
        group1
    ) == SeatUsageSummary(
        seats_taken=2,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 2,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )
    assert RoleBasedSeatUsageSummaryCalculator.get_seat_usage_for_group(
        group2
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_with_team_and_user_role_picks_highest_of_either(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    RoleAssignmentHandler().assign_role(
        team, group, role=Role.objects.get(uid=PAID_COMMENTER_ROLE), scope=table
    )
    RoleAssignmentHandler().assign_role(
        user, group, role=Role.objects.get(uid=FREE_VIEWER_ROLE), scope=table
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 1,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_order_of_roles_is_as_expected(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    # They are a free member of the group
    data_fixture.create_user_group(
        user=user, group=group, permissions="NO_ROLE_LOW_PRIORITY"
    )
    database = data_fixture.create_database_application(group=group)

    # A role lower in the list should be reported over a role lower in the list.
    expected_role_order = [
        "NO_ROLE_LOW_PRIORITY",
        "NO_ACCESS",
        "VIEWER",
        "COMMENTER",
        "EDITOR",
        "BUILDER",
        "ADMIN",
    ]
    assert set(expected_role_order) == set(default_roles.keys())
    for idx, uid in enumerate(expected_role_order):
        table = data_fixture.create_database_table(
            name=f"table{idx}", database=database
        )
        RoleAssignmentHandler().assign_role(
            user, group, role=Role.objects.get(uid=uid), scope=table
        )

        expected_report = {uid: 0 for uid in expected_role_order}
        expected_report[uid] = 1
        assert (
            EnterpriseLicenseType()
            .get_seat_usage_summary(license_object)
            .num_users_with_highest_role
            == expected_report
        )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_weird_group_user_permission_doesnt_break_usage_check(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    data_fixture.create_user_group(user=user, group=group, permissions="WEIRD_VALUE")

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=1,
        free_users_count=0,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
            "WEIRD_VALUE": 1,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_weird_ras_for_wrong_group_not_counted_when_querying_for_single_group_usage(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    group2 = data_fixture.create_group()
    database_in_other_group = data_fixture.create_database_application(group=group2)
    table_in_other_group = data_fixture.create_database_table(
        database=database_in_other_group
    )
    data_fixture.create_user_group(user=user, group=group, permissions=FREE_VIEWER_ROLE)

    team = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    team_in_other_group = enterprise_data_fixture.create_team(group=group2)
    enterprise_data_fixture.create_subject(team=team, subject=user)

    paid_role = Role.objects.get(uid=PAID_COMMENTER_ROLE)

    for scope in [group2, database_in_other_group, table_in_other_group]:
        RoleAssignment.objects.create(
            scope=scope,
            group=group,
            subject=team,
            role=paid_role,
        )
        RoleAssignment.objects.create(
            scope=scope,
            group=group,
            subject=user,
            role=paid_role,
        )

    assert RoleBasedSeatUsageSummaryCalculator().get_seat_usage_for_group(
        group
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "ADMIN": 0,
            "BUILDER": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 1,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_missing_roles_doesnt_cause_crash_and_members_admins_are_treated_as_non_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    admin_user = data_fixture.create_user()
    builder_user = data_fixture.create_user()
    group = data_fixture.create_group()
    data_fixture.create_user_group(user=admin_user, group=group, permissions="MEMBER")
    data_fixture.create_user_group(user=builder_user, group=group, permissions="ADMIN")
    Role.objects.all().delete()

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=2,
        free_users_count=0,
        num_users_with_highest_role={
            "BUILDER": 1,
            "ADMIN": 1,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 0,
            "NO_ACCESS": 0,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_orphaned_paid_role_assignments_dont_get_counted(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    data_fixture.create_user_group(user=user, group=group, permissions="NO_ACCESS")
    database = data_fixture.create_database_application(group=group)

    team = enterprise_data_fixture.create_team(group=group)

    scope_cts = ContentType.objects.get_for_models(
        Database, Application, Table, Group
    ).values()
    user_ct = ContentType.objects.get_for_model(get_user_model())
    paid_role = Role.objects.get(uid=PAID_COMMENTER_ROLE)

    # RA's on scopes that no longer exist
    for ct in scope_cts:
        RoleAssignment.objects.create(
            subject_id=user.id,
            group=group,
            subject_type=user_ct,
            scope_id=99999,
            scope_type=ct,
            role=paid_role,
        )

    subject_cts = ContentType.objects.get_for_models(
        *[t.model_class for t in subject_type_registry.get_all()]
    ).values()

    # RA's on subjects which no longer exist
    for ct in subject_cts:
        RoleAssignment.objects.create(
            subject_id=99999,
            group=group,
            subject_type=ct,
            scope_id=database.id,
            scope_type=ContentType.objects.get_for_model(database),
            role=paid_role,
        )

    # An RA on a non-existent subject and scope
    RoleAssignment.objects.create(
        subject_id=99999,
        group=group,
        subject_type=user_ct,
        scope_id=99999,
        scope_type=ContentType.objects.get_for_model(database),
        role=paid_role,
    )

    # A team with an orphaned subject for a nonsense user id
    TeamSubject.objects.create(team=team, subject_id=99999, subject_type=user_ct)
    RoleAssignment.objects.create(
        subject_id=team.id,
        group=group,
        subject_type=ContentType.objects.get_for_model(team),
        scope_id=database.id,
        scope_type=ContentType.objects.get_for_model(database),
        role=paid_role,
    )

    assert EnterpriseLicenseType().get_seat_usage_summary(
        license_object
    ) == SeatUsageSummary(
        seats_taken=0,
        free_users_count=1,
        num_users_with_highest_role={
            "BUILDER": 0,
            "ADMIN": 0,
            "EDITOR": 0,
            "COMMENTER": 0,
            "VIEWER": 0,
            "NO_ACCESS": 1,
            "NO_ROLE_LOW_PRIORITY": 0,
        },
    )
