import pytest
from unittest.mock import patch

from baserow.core.exceptions import PermissionDenied
from baserow.contrib.database.views.models import View
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import (
    GridView,
    OWNERSHIP_TYPE_COLLABORATIVE,
)
from baserow_premium.views.handler import get_rows_grouped_by_single_select_field

@pytest.mark.django_db
def test_get_rows_grouped_by_single_select_field(
    premium_data_fixture, django_assert_num_queries
):
    table = premium_data_fixture.create_database_table()
    view = View()
    view.table = table
    text_field = premium_data_fixture.create_text_field(table=table, primary=True)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    option_b = premium_data_fixture.create_select_option(
        field=single_select_field, value="B", color="red"
    )

    model = table.get_model()
    row_none1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row None 1",
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_none2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row None 2",
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_a1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row A1",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_a2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row A2",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_b1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row B1",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )
    row_b2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row B2",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )

    # The amount of queries including
    with django_assert_num_queries(4):
        rows = get_rows_grouped_by_single_select_field(
            view, single_select_field, model=model
        )

    assert len(rows) == 3
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 2
    assert rows["null"]["results"][0].id == row_none1.id
    assert rows["null"]["results"][1].id == row_none2.id

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 2
    assert rows[str(option_a.id)]["results"][0].id == row_a1.id
    assert rows[str(option_a.id)]["results"][1].id == row_a2.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 2
    assert rows[str(option_b.id)]["results"][0].id == row_b1.id
    assert rows[str(option_b.id)]["results"][1].id == row_b2.id

    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, default_limit=1
    )

    assert len(rows) == 3
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 1
    assert rows["null"]["results"][0].id == row_none1.id

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_a1.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 1
    assert rows[str(option_b.id)]["results"][0].id == row_b1.id

    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, default_limit=1, default_offset=1
    )

    assert len(rows) == 3
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 1
    assert rows["null"]["results"][0].id == row_none2.id

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_a2.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 1
    assert rows[str(option_b.id)]["results"][0].id == row_b2.id

    rows = get_rows_grouped_by_single_select_field(
        view,
        single_select_field,
        option_settings={"null": {"limit": 1, "offset": 1}},
    )

    assert len(rows) == 1
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 1
    assert rows["null"]["results"][0].id == row_none2.id

    rows = get_rows_grouped_by_single_select_field(
        view,
        single_select_field,
        option_settings={
            str(option_a.id): {"limit": 1, "offset": 0},
            str(option_b.id): {"limit": 1, "offset": 1},
        },
    )

    assert len(rows) == 2

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_a1.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 1
    assert rows[str(option_b.id)]["results"][0].id == row_b2.id

    rows = get_rows_grouped_by_single_select_field(
        view,
        single_select_field,
        option_settings={
            str(option_a.id): {"limit": 10, "offset": 10},
        },
    )

    assert len(rows) == 1
    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 0


@pytest.mark.django_db
def test_get_rows_grouped_by_single_select_field_not_existing_options_are_null(
    premium_data_fixture,
):
    table = premium_data_fixture.create_database_table()
    view = View()
    view.table = table
    text_field = premium_data_fixture.create_text_field(table=table, primary=True)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    option_b = premium_data_fixture.create_select_option(
        field=single_select_field, value="B", color="red"
    )

    model = table.get_model()
    row_1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row 1",
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row 2",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row 3",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )

    option_b.delete()
    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, model=model
    )

    assert len(rows) == 2
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 2
    assert rows["null"]["results"][0].id == row_1.id
    assert rows["null"]["results"][1].id == row_3.id
    assert rows[str(option_a.id)]["count"] == 1
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_2.id

    option_a.delete()
    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, model=model
    )

    assert len(rows) == 1
    assert rows["null"]["count"] == 3
    assert len(rows["null"]["results"]) == 3
    assert rows["null"]["results"][0].id == row_1.id
    assert rows["null"]["results"][1].id == row_2.id
    assert rows["null"]["results"][2].id == row_3.id


@pytest.mark.django_db
def test_get_rows_grouped_by_single_select_field_with_empty_table(
    premium_data_fixture,
):
    table = premium_data_fixture.create_database_table()
    view = View()
    view.table = table
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    rows = get_rows_grouped_by_single_select_field(view, single_select_field)
    assert len(rows) == 1
    assert rows["null"]["count"] == 0
    assert len(rows["null"]["results"]) == 0


@pytest.mark.django_db
def test_list_views_personal_ownership_type(data_fixture, premium_data_fixture, alternative_per_group_license_service):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(
        user, group.id
    )
    alternative_per_group_license_service.restrict_user_premium_to(
        user2, group.id
    )
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type=OWNERSHIP_TYPE_COLLABORATIVE,
    )
    view2 = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    user_views = handler.list_views(user, table, "grid", None, None, None, 10)
    assert len(user_views) == 2

    user2_views = handler.list_views(user2, table, "grid", None, None, None, 10)
    assert len(user2_views) == 1
    assert user2_views[0].id == view.id


@pytest.mark.django_db
def test_get_view_personal_ownership_type(data_fixture, premium_data_fixture, alternative_per_group_license_service):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(
        user, group.id
    )
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    handler.get_view(user, view.id)

    with pytest.raises(PermissionDenied):
        handler.get_view(user2, view.id)


@pytest.mark.django_db
@patch("baserow.contrib.database.views.signals.view_created.send")
def test_create_view_personal_ownership_type(send_mock, data_fixture, premium_data_fixture, alternative_per_group_license_service):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(
        user, group.id
    )

    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    grid = GridView.objects.all().first()
    assert grid.created_by == user
    assert grid.ownership_type == "personal"


@pytest.mark.django_db
def test_duplicate_view_personal_ownership_type(data_fixture, premium_data_fixture, alternative_per_group_license_service):
    group = data_fixture.create_group(name="Group 1")
    user = premium_data_fixture.create_user(group=group)
    user2 = premium_data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_group_license_service.restrict_user_premium_to(
        user, group.id
    )
    alternative_per_group_license_service.restrict_user_premium_to(
        user2, group.id
    )

    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    duplicated_view = handler.duplicate_view(user, view)
    assert duplicated_view.ownership_type == "personal"
    assert duplicated_view.created_by == user

    with pytest.raises(PermissionDenied):
        handler.get_view(user2, duplicated_view.id)

    with pytest.raises(PermissionDenied):
        duplicated_view = handler.duplicate_view(user2, view)
