from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete
from django.dispatch import receiver

from baserow.core.models import GroupUser, Group
from baserow.core.registries import subject_type_registry
from baserow.core.signals import group_user_updated, permissions_updated
from baserow.core.types import Subject
from baserow.ws.tasks import broadcast_to_users
from baserow_enterprise.features import RBAC
from baserow_enterprise.signals import (
    role_assignment_created,
    role_assignment_deleted,
    role_assignment_updated,
)
from baserow_premium.license.handler import LicenseHandler

User = get_user_model()


@receiver(role_assignment_updated)
@receiver(role_assignment_created)
@receiver(role_assignment_deleted)
def send_permissions_updated_when_role_assignment_updated(
    sender, subject: Subject, group: Group, **kwargs
):
    permissions_updated.send(sender, subject=subject, group=group)


@receiver(group_user_updated)
def send_permissions_updated_when_group_user_updated(
    sender, group_user: GroupUser, **kwargs
):
    permissions_updated.send(sender, subject=group_user.user, group=group_user.group)


@receiver(permissions_updated)
def notify_users_about_updated_permissions(
    sender, subject: Subject, group: Group, **kwargs
):
    if not LicenseHandler.group_has_feature(RBAC, group):
        return

    subject_type = subject_type_registry.get_by_model(subject)
    associated_users = subject_type.get_associated_users(subject)
    associated_user_ids = [user.id for user in associated_users]

    broadcast_to_users.delay(associated_user_ids, {"type": "permissions_updated"})


def cascade_subject_delete(sender, instance, **kwargs):
    """
    Delete role assignments linked to deleted subjects.
    """

    from .models import RoleAssignment

    subject_ct = ContentType.objects.get_for_model(instance)
    RoleAssignment.objects.filter(
        subject_id=instance.id, subject_type=subject_ct
    ).delete()


def cascade_group_user_delete(sender, instance, **kwargs):
    """
    Delete role assignments linked user to deleted GroupUser.
    """

    from .models import RoleAssignment

    user_id = instance.user_id
    group_id = instance.group_id
    user_ct = ContentType.objects.get_for_model(User)
    RoleAssignment.objects.filter(
        subject_id=user_id, subject_type=user_ct, group_id=group_id
    ).delete()


def cascade_scope_delete(sender, instance, **kwargs):
    """
    Delete role assignments linked to deleted scope.
    """

    from .models import RoleAssignment

    scope_ct = ContentType.objects.get_for_model(instance)
    RoleAssignment.objects.filter(scope_id=instance.id, scope_type=scope_ct).delete()


def connect_to_post_delete_signals_to_cascade_deletion_to_role_assignments():
    """
    Connect to post_delete signal of all role_assignment generic foreign key to delete
    all related role_assignments.
    """

    from baserow.core.models import GroupUser
    from baserow.core.registries import (
        object_scope_type_registry,
        subject_type_registry,
    )
    from baserow_enterprise.role.constants import ROLE_ASSIGNABLE_OBJECT_MAP

    # Add the subject handler
    for subject_type in subject_type_registry.get_all():
        post_delete.connect(cascade_subject_delete, subject_type.model_class)

    # Add the GroupUser handler
    post_delete.connect(cascade_group_user_delete, GroupUser)

    # Add the scope handler
    for role_assignable_object_type in ROLE_ASSIGNABLE_OBJECT_MAP.keys():
        scope_type = object_scope_type_registry.get(role_assignable_object_type)
        post_delete.connect(cascade_scope_delete, scope_type.model_class)
