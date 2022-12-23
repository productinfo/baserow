"""
This file tests the link row field in combination with RBAC enabled
"""
import pytest

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.core.exceptions import PermissionDenied
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role


@pytest.fixture(autouse=True)
def enable_enterprise_and_roles_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db
def test_link_row_field_linked_to_table_with_no_access(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table_with_access = data_fixture.create_database_table(user, database=database)
    table_with_no_access = data_fixture.create_database_table(user, database=database)
    no_access_role = Role.objects.get(uid="NO_ACCESS")

    RoleAssignmentHandler().assign_role(
        user, group, role=no_access_role, scope=table_with_no_access
    )

    with pytest.raises(PermissionDenied):
        FieldHandler().create_field(
            user=user,
            table=table_with_access,
            type_name="link_row",
            name="link row",
            link_row_table=table_with_no_access,
        )

    with pytest.raises(PermissionDenied):
        FieldHandler().create_field(
            user=user,
            table=table_with_access,
            type_name="link_row",
            name="link row",
            link_row_table=table_with_no_access,
            has_related_field=False,
        )
