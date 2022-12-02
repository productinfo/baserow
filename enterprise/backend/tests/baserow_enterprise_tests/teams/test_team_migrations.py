from django.db import connection
from django.db.migrations.executor import MigrationExecutor

import pytest


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state


@pytest.mark.django_db
def test_0010_delete_all_user_teamsubjects():
    """
    Tests that 0010_delete_all_user_teamsubjects correctly deletes
    all `User` type `TeamSubject` as we are moving to `GroupUser`
    type `TeamSubject` instead.
    """

    migrate_from = [
        ("baserow_enterprise", "0009_roleassignment_subject_and_scope_uniqueness"),
        ("database", "0092_alter_token_name"),
    ]
    migrate_to = [
        ("baserow_enterprise", "0010_delete_all_user_teamsubjects"),
    ]

    old_state = migrate(migrate_from)

    # The subject types.
    User = old_state.apps.get_model("auth", "User")
    Token = old_state.apps.get_model("database", "Token")

    ContentType = old_state.apps.get_model("contenttypes", "ContentType")

    user_ct = ContentType.objects.get_for_model(User)
    token_ct = ContentType.objects.get_for_model(Token)

    Group = old_state.apps.get_model("core", "Group")
    Team = old_state.apps.get_model("baserow_enterprise", "Team")
    TeamSubject = old_state.apps.get_model("baserow_enterprise", "TeamSubject")

    user = User.objects.create()
    group = Group.objects.create()
    token = Token.objects.create(group=group, user=user)
    team = Team.objects.create(group=group)
    TeamSubject.objects.create(team=team, subject_id=user.id, subject_type=user_ct)
    TeamSubject.objects.create(team=team, subject_id=token.id, subject_type=token_ct)

    assert TeamSubject.objects.filter(subject_type=user_ct).count() == 1
    assert TeamSubject.objects.filter(subject_type=token_ct).count() == 1

    new_state = migrate(migrate_to)

    TeamSubject = new_state.apps.get_model("baserow_enterprise", "TeamSubject")
    ContentType = new_state.apps.get_model("contenttypes", "ContentType")

    user_ct = ContentType.objects.get_for_model(User)
    token_ct = ContentType.objects.get_for_model(Token)

    assert TeamSubject.objects.filter(subject_type=user_ct).count() == 0
    assert TeamSubject.objects.filter(subject_type=token_ct).count() == 1
