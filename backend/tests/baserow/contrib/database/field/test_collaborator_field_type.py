import pytest

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import (
    CollaboratorField,
)
from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
@pytest.mark.field_collaborator
def test_collaborator_field_type_create(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    collaborator_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="collaborator",
        name="Collaborator 1",
    )
    field_id = collaborator_field.db_column

    assert CollaboratorField.objects.all().first().id == collaborator_field.id

    row = row_handler.create_row(
        user=user, table=table, values={field_id: [{"id": user.id}]}
    )
    assert row.id
    collaborator_field_list = getattr(row, field_id).all()
    assert len(collaborator_field_list) == 1
    assert collaborator_field_list[0].id == user.id


@pytest.mark.django_db
@pytest.mark.field_collaborator
def test_collaborator_field_type_update(data_fixture):
    group = data_fixture.create_group()
    user = data_fixture.create_user(group=group)
    user2 = data_fixture.create_user(group=group)
    user3 = data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(
        user=user, name="Placeholder", group=group
    )
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    collaborator_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="collaborator",
        name="Collaborator 1",
    )
    field_id = collaborator_field.db_column

    assert CollaboratorField.objects.all().first().id == collaborator_field.id

    row = row_handler.create_row(user=user, table=table, values={field_id: []})

    row_handler.update_row(
        user, table, row, {field_id: [{"id": user2.id}, {"id": user3.id}]}
    )

    collaborator_field_list = getattr(row, field_id).all()
    assert len(collaborator_field_list) == 2
    # TODO: order is not kept?
    assert collaborator_field_list[0].id == user2.id
    assert collaborator_field_list[1].id == user3.id
