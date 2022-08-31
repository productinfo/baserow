from io import BytesIO
import pytest

from baserow.core.handler import CoreHandler
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import MultipleCollaboratorsField
from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
@pytest.mark.field_multiple_collaborators
def test_multiple_collaborators_field_type_create(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    collaborator_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_collaborators",
        name="Collaborator 1",
    )
    field_id = collaborator_field.db_column

    assert MultipleCollaboratorsField.objects.all().first().id == collaborator_field.id

    row = row_handler.create_row(
        user=user, table=table, values={field_id: [{"id": user.id}]}
    )
    assert row.id
    collaborator_field_list = getattr(row, field_id).all()
    assert len(collaborator_field_list) == 1
    assert collaborator_field_list[0].id == user.id


@pytest.mark.django_db
@pytest.mark.field_multiple_collaborators
def test_multiple_collaborators_field_type_update(data_fixture):
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
        type_name="multiple_collaborators",
        name="Collaborator 1",
    )
    field_id = collaborator_field.db_column

    assert MultipleCollaboratorsField.objects.all().first().id == collaborator_field.id

    row = row_handler.create_row(user=user, table=table, values={field_id: []})

    row_handler.update_row(
        user, table, row, {field_id: [{"id": user2.id}, {"id": user3.id}]}
    )

    collaborator_field_list = getattr(row, field_id).all()
    assert len(collaborator_field_list) == 2
    assert collaborator_field_list[0].id == user2.id
    assert collaborator_field_list[1].id == user3.id


@pytest.mark.django_db(transaction=True)
def test_get_set_export_serialized_value_multiple_collaborators_field(data_fixture):
    user = data_fixture.create_user(email="user1@baserow.io")
    user_2 = data_fixture.create_user(email="user2@baserow.io")
    user_3 = data_fixture.create_user(email="user3@baserow.io")
    group = data_fixture.create_group(user=user)
    data_fixture.create_user_group(group=group, user=user_2)
    data_fixture.create_user_group(group=group, user=user_3)

    imported_group = data_fixture.create_group(user=user)
    data_fixture.create_user_group(group=imported_group, user=user_2)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()
    core_handler = CoreHandler()

    multiple_collaborators__field = field_handler.create_field(
        user=user,
        table=table,
        name="Multiple collaborators",
        type_name="multiple_collaborators",
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={},
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{multiple_collaborators__field.id}": [
                {"id": user.id},
                {"id": user_2.id},
            ],
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{multiple_collaborators__field.id}": [
                {"id": user.id},
                {"id": user_3.id},
            ],
        },
    )

    exported_applications = core_handler.export_group_applications(group, BytesIO())
    imported_applications, id_mapping = core_handler.import_applications_to_group(
        imported_group, exported_applications, BytesIO(), None
    )
    imported_database = imported_applications[0]
    imported_table = imported_database.table_set.all()[0]
    imported_field = imported_table.field_set.all().first().specific

    assert imported_table.id != table.id
    assert imported_field.id != multiple_collaborators__field.id

    imported_model = imported_table.get_model()
    all = imported_model.objects.all()
    assert len(all) == 3
    imported_row_1 = all[0]
    imported_row_1_field = (
        getattr(imported_row_1, f"field_" f"{imported_field.id}").order_by("id").all()
    )
    imported_row_2 = all[1]
    imported_row_2_field = (
        getattr(imported_row_2, f"field_{imported_field.id}").order_by("id").all()
    )
    imported_row_3 = all[2]
    imported_row_3_field = (
        getattr(imported_row_3, f"field_{imported_field.id}").order_by("id").all()
    )

    assert len(imported_row_1_field) == 0
    assert len(imported_row_2_field) == 2
    assert imported_row_2_field[0].id == user.id
    assert imported_row_2_field[1].id == user_2.id
    assert len(imported_row_3_field) == 1
    assert imported_row_3_field[0].id == user.id
