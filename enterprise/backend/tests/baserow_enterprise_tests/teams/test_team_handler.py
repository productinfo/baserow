from unittest.mock import patch

from django.contrib.auth.models import User

import pytest

from baserow_enterprise.role.models import Role
from baserow_enterprise.teams.exceptions import (
    TeamNameNotUnique,
    TeamSubjectBulkDoesNotExist,
    TeamSubjectDoesNotExist,
    TeamSubjectNotInGroup,
    TeamSubjectTypeUnsupported,
)
from baserow_enterprise.teams.handler import SUBJECT_TYPE_USER, TeamHandler


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise):
    pass


@pytest.mark.django_db
def test_create_team(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    role = Role.objects.get(uid="BUILDER")
    team = TeamHandler().create_team(user, "Engineering", group, default_role=role)
    assert team.name == "Engineering"
    assert team.default_role_uid == "BUILDER"


@pytest.mark.django_db
def test_bulk_create_subjects(data_fixture):
    group = data_fixture.create_group()
    groupuser_a = data_fixture.create_user_group(group=group)
    groupuser_b = data_fixture.create_user_group(group=group)
    groupuser_c = data_fixture.create_user_group(group=group)
    team = TeamHandler().create_team(groupuser_a.user, "Engineering", group)
    subjects = TeamHandler().bulk_create_subjects(
        team,
        [
            {"subject_id": groupuser_a.id, "subject_type": SUBJECT_TYPE_USER},
            {"subject_id": groupuser_b.id, "subject_type": SUBJECT_TYPE_USER},
            {"subject_id": groupuser_c.id, "subject_type": SUBJECT_TYPE_USER},
        ],
    )
    assert len(subjects) == 3


@pytest.mark.django_db
def test_bulk_create_subjects_specific_pk(data_fixture):
    group = data_fixture.create_group()
    groupuser = data_fixture.create_user_group(group=group)
    team = TeamHandler().create_team(groupuser.user, "Engineering", group)
    subjects = TeamHandler().bulk_create_subjects(
        team,
        [
            {"pk": 5, "subject_id": groupuser.id, "subject_type": SUBJECT_TYPE_USER},
        ],
    )
    assert len(subjects) == 1
    subject = subjects[0]
    assert subject.id == 5


@pytest.mark.django_db
def test_bulk_create_subjects_raise_on_missing_does_not_exist(data_fixture):
    group = data_fixture.create_group()
    groupuser = data_fixture.create_user_group(group=group)
    team = TeamHandler().create_team(groupuser.user, "Engineering", group)
    with pytest.raises(TeamSubjectBulkDoesNotExist) as exc_info:
        TeamHandler().bulk_create_subjects(
            team,
            [
                {"subject_id": groupuser.id, "subject_type": SUBJECT_TYPE_USER},
                {"subject_id": 100000001, "subject_type": SUBJECT_TYPE_USER},
            ],
        )
    assert exc_info.value.missing_subjects == [
        {"subject_id": 100000001, "subject_type": SUBJECT_TYPE_USER}
    ]


@pytest.mark.django_db
def test_bulk_create_subjects_raise_on_missing_not_group_member(data_fixture):
    group = data_fixture.create_group()
    groupuser_a = data_fixture.create_user_group(group=group)
    groupuser_b = data_fixture.create_user_group(group=group)
    groupuser_c = data_fixture.create_user_group()  # Not a group member!
    team = TeamHandler().create_team(groupuser_a.user, "Engineering", group)
    with pytest.raises(TeamSubjectBulkDoesNotExist) as exc_info:
        TeamHandler().bulk_create_subjects(
            team,
            [
                {"subject_id": groupuser_a.id, "subject_type": SUBJECT_TYPE_USER},
                {"subject_id": groupuser_b.id, "subject_type": SUBJECT_TYPE_USER},
                {"subject_id": groupuser_c.id, "subject_type": SUBJECT_TYPE_USER},
            ],
        )
    assert exc_info.value.missing_subjects == [
        {"subject_id": groupuser_c.id, "subject_type": SUBJECT_TYPE_USER}
    ]


@pytest.mark.django_db
def test_create_team_non_unique_name(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    TeamHandler().create_team(user, "Engineering", group)
    with pytest.raises(TeamNameNotUnique):
        TeamHandler().create_team(user, "Engineering", group)


@pytest.mark.django_db
def test_create_team_with_subjects(data_fixture):
    group = data_fixture.create_group()
    groupuser = data_fixture.create_user_group(group=group)
    team = TeamHandler().create_team(
        groupuser.user,
        "Engineering",
        group,
        [{"subject_id": groupuser.id, "subject_type": SUBJECT_TYPE_USER}],
    )
    subject = team.subjects.all()[0]
    assert subject.subject_id == groupuser.id


@pytest.mark.django_db
def test_list_teams_in_group(data_fixture, enterprise_data_fixture):
    group = data_fixture.create_group()
    groupuser = data_fixture.create_user_group(group=group)
    sales = enterprise_data_fixture.create_team(group=group)
    engineering = enterprise_data_fixture.create_team(group=group)
    sales_subj = enterprise_data_fixture.create_subject(team=sales, subject=groupuser)
    teams_qs = (
        TeamHandler().list_teams_in_group(groupuser.user, group.id).order_by("id")
    )
    assert teams_qs[0].id == sales.id
    assert teams_qs[0].subject_count == 1
    assert teams_qs[0].subject_sample == [
        {
            "team_subject_id": sales_subj.id,
            "subject_id": sales_subj.subject_id,
            "subject_type": sales_subj.subject_type_natural_key,
            "subject_label": groupuser.user.get_full_name().strip(),
        }
    ]
    assert teams_qs[1].id == engineering.id
    assert teams_qs[1].subject_count == 0
    assert teams_qs[1].subject_sample == []


@pytest.mark.django_db
def test_update_team(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    role_viewer = Role.objects.get(uid="VIEWER")
    role_builder = Role.objects.get(uid="BUILDER")
    team = TeamHandler().create_team(
        user, "Engineering", group, default_role=role_viewer
    )
    assert team.default_role_uid == "VIEWER"
    team = TeamHandler().update_team(user, team, "Sales", default_role=role_builder)
    assert team.name == "Sales"
    assert team.default_role_uid == "BUILDER"


@pytest.mark.django_db
def test_update_team_non_unique_name(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    TeamHandler().create_team(user, "Engineering", group)
    team = TeamHandler().create_team(user, "Sales", group)
    with pytest.raises(TeamNameNotUnique):
        TeamHandler().update_team(user, team, "Engineering")


@pytest.mark.django_db
def test_update_team_subjects(data_fixture, enterprise_data_fixture):
    group = data_fixture.create_group()
    groupuser_a = data_fixture.create_user_group(group=group)
    groupuser_b = data_fixture.create_user_group(group=group)
    groupuser_c = data_fixture.create_user_group(group=group)
    team = enterprise_data_fixture.create_team(group=group)
    assert team.subjects.count() == 0

    # Add `groupuser_a`
    team = TeamHandler().update_team(
        groupuser_a.user,
        team,
        "Sales",
        [{"subject_id": groupuser_a.id, "subject_type": SUBJECT_TYPE_USER}],
    )
    assert team.subject_count == 1

    # Add `groupuser_b`
    team = TeamHandler().update_team(
        groupuser_a.user,
        team,
        "Sales",
        [
            {"subject_id": groupuser_a.id, "subject_type": SUBJECT_TYPE_USER},
            {"subject_id": groupuser_b.id, "subject_type": SUBJECT_TYPE_USER},
        ],
    )
    assert team.subject_count == 2

    # Remove `groupuser_b`, add `groupuser_c`
    team = TeamHandler().update_team(
        groupuser_a.user,
        team,
        "Sales",
        [
            {"subject_id": groupuser_a.id, "subject_type": SUBJECT_TYPE_USER},
            {"subject_id": groupuser_c.id, "subject_type": SUBJECT_TYPE_USER},
        ],
    )
    assert team.subject_count == 2

    # Remove everyone
    team = TeamHandler().update_team(groupuser_a.user, team, "Sales", [])
    assert team.subject_count == 0


@pytest.mark.django_db
def test_delete_team(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group()
    data_fixture.create_user_group(group=group, user=user, permissions="ADMIN")
    team = enterprise_data_fixture.create_team(name="Engineering", group=group)
    TeamHandler().delete_team(user, team)


@patch(
    "baserow_enterprise.teams.handler.TeamHandler.is_supported_subject_type",
    return_value=False,
)
def test_create_subject_unsupported_type(
    is_supported_subject_type, enterprise_data_fixture
):
    team = enterprise_data_fixture.create_team()
    with pytest.raises(TeamSubjectTypeUnsupported):
        TeamHandler().create_subject(User(), 123, "foo_bar", team)


@pytest.mark.django_db
def test_create_subject_unknown_subject(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    team = enterprise_data_fixture.create_team()
    assert not User.objects.filter(pk=123).exists()
    with pytest.raises(TeamSubjectDoesNotExist):
        TeamHandler().create_subject(user, 123, SUBJECT_TYPE_USER, team)


@pytest.mark.django_db
def test_create_subject_from_different_group_to_team(
    data_fixture, enterprise_data_fixture
):
    group_a = data_fixture.create_group()
    groupuser = data_fixture.create_user_group(group=group_a)
    group_b = data_fixture.create_group()
    team = enterprise_data_fixture.create_team(group=group_b)
    with pytest.raises(TeamSubjectNotInGroup):
        TeamHandler().create_subject(
            groupuser.user, groupuser.id, SUBJECT_TYPE_USER, team
        )


@pytest.mark.django_db
def test_create_subject_by_id(data_fixture, enterprise_data_fixture):
    group = data_fixture.create_group()
    groupuser = data_fixture.create_user_group(group=group)
    team = enterprise_data_fixture.create_team(group=group)
    subject = TeamHandler().create_subject(
        groupuser.user, groupuser.id, SUBJECT_TYPE_USER, team
    )
    assert subject.team_id == team.id
    assert subject.subject_id == groupuser.id
    assert isinstance(groupuser, subject.subject_type.model_class())


@pytest.mark.django_db
def test_list_subjects_in_team(data_fixture, enterprise_data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    sales = enterprise_data_fixture.create_team(group=group)
    engineering = enterprise_data_fixture.create_team(group=group)
    enterprise_data_fixture.create_subject(team=engineering)
    sales_subject_1 = enterprise_data_fixture.create_subject(team=sales)
    sales_subject_2 = enterprise_data_fixture.create_subject(team=sales)
    qs = TeamHandler().list_subjects_in_team(sales.id)
    assert qs.count() == 2
    assert sales_subject_1 in qs
    assert sales_subject_2 in qs
