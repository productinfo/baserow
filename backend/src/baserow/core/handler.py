import hashlib
import json
import os
from io import BytesIO
from pathlib import Path
from typing import IO, Any, Dict, List, NewType, Optional, Tuple, TypedDict, cast
from urllib.parse import urljoin, urlparse
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.files.storage import Storage, default_storage
from django.db import transaction
from django.db.models import Count, Prefetch, Q, QuerySet
from django.utils import translation

from itsdangerous import URLSafeSerializer
from rest_framework.exceptions import NotAuthenticated
from tqdm import tqdm

from baserow.core.user.utils import normalize_email_address

from .emails import GroupInvitationEmail
from .exceptions import (
    ApplicationDoesNotExist,
    ApplicationNotInGroup,
    BaseURLHostnameNotAllowed,
    CannotDeleteYourselfFromGroup,
    GroupDoesNotExist,
    GroupInvitationDoesNotExist,
    GroupInvitationEmailMismatch,
    GroupUserAlreadyExists,
    GroupUserDoesNotExist,
    GroupUserIsLastAdmin,
    InvalidPermissionContext,
    PermissionDenied,
    PermissionException,
    TemplateDoesNotExist,
    TemplateFileDoesNotExist,
    UserNotInGroup,
)
from .models import (
    GROUP_USER_PERMISSION_ADMIN,
    GROUP_USER_PERMISSION_MEMBER,
    Application,
    Group,
    GroupInvitation,
    GroupUser,
    Settings,
    Template,
    TemplateCategory,
)
from .operations import (
    CreateApplicationsGroupOperationType,
    CreateGroupOperationType,
    CreateInvitationsGroupOperationType,
    DeleteApplicationOperationType,
    DeleteGroupInvitationOperationType,
    DeleteGroupOperationType,
    DeleteGroupUserOperationType,
    DuplicateApplicationOperationType,
    OrderApplicationsOperationType,
    ReadApplicationOperationType,
    UpdateApplicationOperationType,
    UpdateGroupInvitationType,
    UpdateGroupOperationType,
    UpdateGroupUserOperationType,
    UpdateSettingsOperationType,
)
from .registries import (
    application_type_registry,
    object_scope_type_registry,
    operation_type_registry,
    permission_manager_type_registry,
)
from .signals import (
    application_created,
    application_deleted,
    application_updated,
    applications_reordered,
    before_group_deleted,
    before_group_user_deleted,
    before_group_user_updated,
    group_created,
    group_deleted,
    group_updated,
    group_user_added,
    group_user_deleted,
    group_user_updated,
    groups_reordered,
)
from .trash.handler import TrashHandler
from .types import ContextObject
from .utils import ChildProgressBuilder, find_unused_name, set_allowed_attrs

User = get_user_model()

GroupForUpdate = NewType("GroupForUpdate", Group)


class PermissionObjectResult(TypedDict):
    name: str
    permissions: Any


class CoreHandler:
    def get_settings(self):
        """
        Returns a settings model instance containing all the admin configured settings.

        :return: The settings instance.
        :rtype: Settings
        """

        try:
            return Settings.objects.all()[:1].get()
        except Settings.DoesNotExist:
            return Settings.objects.create()

    def update_settings(self, user, settings_instance=None, **kwargs):
        """
        Updates one or more setting values if the user has staff permissions.

        :param user: The user on whose behalf the settings are updated.
        :type user: User
        :param settings_instance: If already fetched, the settings instance can be
            provided to avoid fetching the values for a second time.
        :type settings_instance: Settings
        :param kwargs: An dict containing the settings that need to be updated.
        :type kwargs: dict
        :return: The update settings instance.
        :rtype: Settings
        """

        CoreHandler().check_permissions(
            user, UpdateSettingsOperationType.type, context=settings_instance
        )

        if not settings_instance:
            settings_instance = self.get_settings()

        settings_instance = set_allowed_attrs(
            kwargs,
            [
                "allow_new_signups",
                "allow_signups_via_group_invitations",
                "allow_reset_password",
                "allow_global_group_creation",
                "account_deletion_grace_delay",
            ],
            settings_instance,
        )

        settings_instance.save()
        return settings_instance

    def check_permissions(
        self,
        actor: AbstractUser,
        operation_name: str,
        group: Optional[Group] = None,
        context: Optional[ContextObject] = None,
        include_trash: bool = False,
        raise_error: bool = True,
        allow_if_template: bool = False,
    ) -> bool:
        """
        Checks whether a specific Actor has the Permission to execute an Operation
        on the given Context.

        When we check a permission, all permission managers listed in
        `settings.PERMISSION_MANAGERS` are called successively until one
        gives a final answer (permitted or disallowed).

        Each permission manager can answer with `True` if the operation is permitted,
        raise a PermissionDenied subclass exception if the operation is disallowed and
        return `None` if it can't take a definitive answer.

        If None of the permission manager replied with a final answer, the operation is
        denied by default.

        :param actor: The actor who wants to execute the operation. Generally a `User`,
            but can be a `Token`.
        :param operation_name: The operation name the actor wants to execute.
        :param group: The optional group in which  the operation takes place.
        :param context: The optional object affected by the operation. For instance
            if you are updating a `Table` object, the context is this `Table` object.
        :param include_trash: If true then also checks if the given group has been
            trashed instead of raising a DoesNotExist exception.
        :param raise_error: Raise an exception when the permission is disallowed when
            `True`. Return `False` instead when `False`. `True` by default.
        :raise PermissionDenied: If the operation is disallowed a PermissionDenied is
            raised.
        :param allow_if_template: If true and if the group is related to a template,
            then True is always returned and no exception will be raised.
        :raise PermissionDenied: If the operation is disallowed and raise_error is
            `True` a PermissionDenied is raised.
        :return: `True` if the operation is permitted or `False` if the operation is
            disallowed AND raise_error is `False`.
        """

        if settings.DEBUG or settings.TESTS:
            self._ensure_context_matches_operation(context, operation_name)

        if allow_if_template and group and group.has_template():
            return True

        for permission_manager_name in settings.PERMISSION_MANAGERS:
            permission_manager_type = permission_manager_type_registry.get(
                permission_manager_name
            )
            try:
                allowed = permission_manager_type.check_permissions(
                    actor,
                    operation_name,
                    group=group,
                    context=context,
                    include_trash=include_trash,
                )
            except (PermissionException, NotAuthenticated):
                if raise_error:
                    raise
                else:
                    return False
            else:
                if allowed is True:
                    return True

        # Here none af the permission managers has allowed the operation so the
        # operation is denied by default.
        if raise_error:
            raise PermissionDenied(actor=actor)
        else:
            return False

    def _ensure_context_matches_operation(self, context, operation_name):
        context_types = {
            t.type
            for t in object_scope_type_registry.get_all_by_model_isinstance(context)
        }
        expected_operation_context_type = operation_type_registry.get(
            operation_name
        ).context_scope_name
        if expected_operation_context_type not in context_types:
            raise InvalidPermissionContext(
                f"Incorrect context object matching {context_types} provided to "
                f" check_permissions call. Was expected instead one of type "
                f"{expected_operation_context_type} based on the operation type of "
                f"{operation_name}."
            )

    def get_permissions(
        self, actor: AbstractUser, group: Optional[Group] = None
    ) -> List[PermissionObjectResult]:
        """
        Generates the object sent to a client to easily check the actor permissions over
        the given group.

        This object is generated by going over all permission managers listed in
        `settings.PERMISSION_MANAGERS` and aggregating the results in a list of dict
        containing permission manager type name and the value returned from the
        permission manager. For example:

        ```python
        [
            {
                "name": "core",
                "permissions": ["perm1", "perm2"]
            },
            {
                "name": "staff"
                "permissions": {
                    "staff_only_permissions": ["perm3", "perm4"],
                    "is_staff": True
                }
            },
            ...
        ]
        ```

        If the permission manager return value is None, it's ignored and not included
        in the final result.

        :param actor: The actor whom we want to compute the permission object for.
        :param group: The optional group into which we want to compute the permission
            object.
        :return: The full permission object.
        """

        result = []
        for permission_manager_name in settings.PERMISSION_MANAGERS:
            permission_manager_type = permission_manager_type_registry.get(
                permission_manager_name
            )

            perms = permission_manager_type.get_permissions_object(actor, group=group)
            if perms is not None:
                result.append(
                    PermissionObjectResult(
                        name=permission_manager_name, permissions=perms
                    )
                )

        return result

    def filter_queryset(
        self,
        actor: AbstractUser,
        operation_name: str,
        queryset: QuerySet,
        group: Optional[Group] = None,
        context: Optional[ContextObject] = None,
        allow_if_template: Optional[bool] = False,
    ) -> QuerySet:
        """
        filters a given queryset accordingly to the actor permissions in the specified
        context.

        All permission managers listed in `settings.PERMISSION_MANAGERS` are called
        to let them the opportunity to filter the queryset if it's relevant for them.

        :param actor: The actor whom we want to filter the queryset for.
        :param operation_name: The list operation name we want the queryset to be
            filtered for.
        :param queryset: The queryset we want to filter. The queryset should contains
            object that are in the same `ObjectScopeType` as the one described in the
            `OperationType` corresponding to the given `operation_name`.
        :param group: An optional group into which the operation occurs.
        :param context: The optional context of the operation.
        :param allow_if_template: If true and if the group is related to a template,
            then we don't want to filter on the queryset.
        :return: The queryset, potentially filtered.
        """

        if allow_if_template and group and group.has_template():
            return queryset

        for permission_manager_name in settings.PERMISSION_MANAGERS:
            permission_manager_type = permission_manager_type_registry.get(
                permission_manager_name
            )
            queryset = permission_manager_type.filter_queryset(
                actor, operation_name, queryset, group=group, context=context
            )

        return queryset

    def get_group_for_update(self, group_id: int) -> GroupForUpdate:
        return cast(
            GroupForUpdate,
            self.get_group(
                group_id, base_queryset=Group.objects.select_for_update(of=("self",))
            ),
        )

    def get_group(self, group_id, base_queryset=None) -> Group:
        """
        Selects a group with a given id from the database.

        :param group_id: The identifier of the group that must be returned.
        :type group_id: int
        :param base_queryset: The base queryset from where to select the group
            object. This can for example be used to do a `prefetch_related`.
        :type base_queryset: Queryset
        :raises GroupDoesNotExist: When the group with the provided id does not exist.
        :return: The requested group instance of the provided id.
        :rtype: Group
        """

        if base_queryset is None:
            base_queryset = Group.objects

        try:
            group = base_queryset.get(id=group_id)
        except Group.DoesNotExist:
            raise GroupDoesNotExist(f"The group with id {group_id} does not exist.")

        return group

    def get_groupuser_group_queryset(self) -> QuerySet[GroupUser]:
        """
        Returns GroupUser queryset that will prefetch groups and their users.
        """

        groupusers_with_user_and_profile = GroupUser.objects.select_related(
            "user"
        ).select_related("user__profile")
        groupuser_groups = GroupUser.objects.select_related("group").prefetch_related(
            Prefetch(
                "group__groupuser_set",
                queryset=groupusers_with_user_and_profile,
            )
        )
        return groupuser_groups

    def create_group(self, user: User, name: str) -> GroupUser:
        """
        Creates a new group for an existing user.

        :param user: The user that must be in the group.
        :param name: The name of the group.
        :return: The newly created GroupUser object
        """

        CoreHandler().check_permissions(user, CreateGroupOperationType.type)

        group = Group.objects.create(name=name)

        last_order = GroupUser.get_last_order(user)
        group_user = GroupUser.objects.create(
            group=group,
            user=user,
            order=last_order,
            permissions=GROUP_USER_PERMISSION_ADMIN,
        )

        group_created.send(self, group=group, user=user)

        return group_user

    def update_group(
        self, user: AbstractUser, group: GroupForUpdate, name: str
    ) -> Group:
        """
        Updates the values of a group if the user has admin permissions to the group.

        :param user: The user on whose behalf the change is made.
        :param group: The group instance that must be updated.
        :param name: The new name to give the group.
        :raises ValueError: If one of the provided parameters is invalid.
        :return: The updated group
        """

        if not isinstance(group, Group):
            raise ValueError("The group is not an instance of Group.")

        CoreHandler().check_permissions(
            user, UpdateGroupOperationType.type, group=group, context=group
        )

        group.name = name
        group.save()

        group_updated.send(self, group=group, user=user)

        return group

    def leave_group(self, user, group):
        """
        Called when a user of group wants to leave a group.

        :param user: The user that wants to leave the group.
        :type user: User
        :param group: The group that the user wants to leave.
        :type group: Group
        """

        if not isinstance(group, Group):
            raise ValueError("The group is not an instance of Group.")

        try:
            group_user = GroupUser.objects.get(user=user, group=group)
        except GroupUser.DoesNotExist:
            raise UserNotInGroup(user, self)

        # If the current user is an admin and he is the last admin left, he is not
        # allowed to leave the group otherwise no one will have control over it. He
        # needs to give someone else admin permissions first or he must leave the group.
        if (
            group_user.permissions == GROUP_USER_PERMISSION_ADMIN
            and GroupUser.objects.filter(
                group=group, permissions=GROUP_USER_PERMISSION_ADMIN
            )
            .exclude(user__profile__to_be_deleted=True)
            .count()
            == 1
        ):
            raise GroupUserIsLastAdmin(
                "The user is the last admin left in the group and can therefore not "
                "leave it."
            )

        before_group_user_deleted.send(
            self, user=user, group=group, group_user=group_user
        )

        # If the user is not the last admin, we can safely delete the user from the
        # group.
        group_user_id = group_user.id
        group_user.delete()
        group_user_deleted.send(
            self,
            group_user_id=group_user_id,
            group_user=group_user,
            user=user,
        )

    def delete_group_by_id(self, user: AbstractUser, group_id: int):
        """
        Deletes a group by id and it's related applications instead of using an
        instance. Only if the user has admin permissions for the group.

        :param user: The user on whose behalf the delete is done.
        :param group_id: The group id that must be deleted.
        :raises ValueError: If one of the provided parameters is invalid.
        """

        locked_group = self.get_group_for_update(group_id)
        self.delete_group(user, locked_group)

    def delete_group(self, user: AbstractUser, group: GroupForUpdate):
        """
        Deletes an existing group and related applications if the user has admin
        permissions for the group. The group can be restored after deletion using the
        trash handler.

        :param user: The user on whose behalf the delete is done.
        :type: user: User
        :param group: The group instance that must be deleted.
        :type: group: Group
        :raises ValueError: If one of the provided parameters is invalid.
        """

        if not isinstance(group, Group):
            raise ValueError("The group is not an instance of Group.")

        CoreHandler().check_permissions(
            user, DeleteGroupOperationType.type, group=group, context=group
        )

        # Load the group users before the group is deleted so that we can pass those
        # along with the signal.
        group_id = group.id
        group_users = list(group.users.all())

        before_group_deleted.send(
            self, group_id=group_id, group=group, group_users=group_users, user=user
        )

        TrashHandler.trash(user, group, None, group)

        group_deleted.send(
            self, group_id=group_id, group=group, group_users=group_users, user=user
        )

    def order_groups(self, user: AbstractUser, group_ids: List[int]):
        """
        Changes the order of groups for a user.

        :param user: The user on whose behalf the ordering is done.
        :param group_ids: A list of group ids ordered the way they need to be ordered.
        """

        for index, group_id in enumerate(group_ids):
            GroupUser.objects.filter(user=user, group_id=group_id).update(
                order=index + 1
            )
        groups_reordered.send(self, user=user, group_ids=group_ids)

    def get_groups_order(self, user: AbstractUser) -> List[int]:
        """
        Returns the order of groups for a user.

        :param user: The user on whose behalf the ordering is done.
        :return: A list of group ids ordered the way they need to be ordered.
        """

        return [
            group_user.group_id
            for group_user in GroupUser.objects.filter(user=user).order_by("order")
        ]

    def get_group_user(self, group_user_id, base_queryset=None):
        """
        Fetches a group user object related to the provided id from the database.

        :param group_user_id: The identifier of the group user that must be returned.
        :type group_user_id: int
        :param base_queryset: The base queryset from where to select the group user
            object. This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises GroupDoesNotExist: When the group with the provided id does not exist.
        :return: The requested group user instance of the provided group_id.
        :rtype: GroupUser
        """

        if base_queryset is None:
            base_queryset = GroupUser.objects

        try:
            group_user = base_queryset.select_related("group").get(id=group_user_id)
        except GroupUser.DoesNotExist:
            raise GroupUserDoesNotExist(
                f"The group user with id {group_user_id} does " f"not exist."
            )

        return group_user

    def update_group_user(
        self,
        user: AbstractUser,
        group_user: GroupUser,
        **kwargs,
    ) -> GroupUser:
        """
        Updates the values of an existing group user.

        :param user: The user on whose behalf the group user is deleted.
        :param group_user: The group user that must be updated.
        :return: The updated group user instance.
        """

        if not isinstance(group_user, GroupUser):
            raise ValueError("The group user is not an instance of GroupUser.")

        CoreHandler().check_permissions(
            user,
            UpdateGroupUserOperationType.type,
            group=group_user.group,
            context=group_user,
        )

        return self.force_update_group_user(user, group_user, **kwargs)

    def force_update_group_user(
        self, user: Optional[AbstractUser], group_user: GroupUser, **kwargs
    ) -> GroupUser:
        """
        Forcibly updates the group users attributes without checking permissions whilst
        sending all the appropriate signals that an update has been done.
        """

        before_group_user_updated.send(self, group_user=group_user, **kwargs)
        group_user = set_allowed_attrs(kwargs, ["permissions"], group_user)
        group_user.save()
        group_user_updated.send(self, group_user=group_user, user=user)
        return group_user

    def delete_group_user(self, user, group_user):
        """
        Deletes the provided group user.

        :param user: The user on whose behalf the group user is deleted.
        :type user: User
        :param group_user: The group user that must be deleted.
        :type group_user: GroupUser
        :raises CannotDeleteYourselfFromGroup; If the user tries to delete himself
            from the group.
        """

        if not isinstance(group_user, GroupUser):
            raise ValueError("The group user is not an instance of GroupUser.")

        CoreHandler().check_permissions(
            user,
            DeleteGroupUserOperationType.type,
            group=group_user.group,
            context=group_user,
        )

        if user.id == group_user.user_id:
            raise CannotDeleteYourselfFromGroup("Cannot delete yourself from group.")

        before_group_user_deleted.send(
            self, user=group_user.user, group=group_user.group, group_user=group_user
        )

        group_user_id = group_user.id
        group_user.delete()

        group_user_deleted.send(
            self,
            group_user_id=group_user_id,
            group_user=group_user,
            user=user,
        )

    def get_group_invitation_signer(self):
        """
        Returns the group invitation signer. This is for example used to create a url
        safe signed version of the invitation id which is used when sending a public
        accept link to the user.

        :return: The itsdangerous serializer.
        :rtype: URLSafeSerializer
        """

        return URLSafeSerializer(settings.SECRET_KEY, "group-invite")

    def send_group_invitation_email(self, invitation, base_url):
        """
        Sends out a group invitation email to the user based on the provided
        invitation instance.

        :param invitation: The invitation instance for which the email must be send.
        :type invitation: GroupInvitation
        :param base_url: The base url of the frontend, where the user can accept his
            invitation. The signed invitation id is appended to the URL (base_url +
            '/TOKEN'). Only the PUBLIC_WEB_FRONTEND_HOSTNAME is allowed as domain name.
        :type base_url: str
        :raises BaseURLHostnameNotAllowed: When the host name of the base_url is not
            allowed.
        """

        parsed_base_url = urlparse(base_url)
        if parsed_base_url.hostname != settings.PUBLIC_WEB_FRONTEND_HOSTNAME:
            raise BaseURLHostnameNotAllowed(
                f"The hostname {parsed_base_url.netloc} is not allowed."
            )

        signer = self.get_group_invitation_signer()
        signed_invitation_id = signer.dumps(invitation.id)

        if not base_url.endswith("/"):
            base_url += "/"

        public_accept_url = urljoin(base_url, signed_invitation_id)

        # Send the email in the language of the user that has send the invitation.
        with translation.override(invitation.invited_by.profile.language):
            email = GroupInvitationEmail(
                invitation, public_accept_url, to=[invitation.email]
            )
            email.send()

    def get_group_invitation_by_token(self, token, base_queryset=None):
        """
        Returns the group invitation instance if a valid signed token of the id is
        provided. It can be signed using the signer returned by the
        `get_group_invitation_signer` method.

        :param token: The signed invitation id of related to the group invitation
            that must be fetched. Must be signed using the signer returned by the
            `get_group_invitation_signer`.
        :type token: str
        :param base_queryset: The base queryset from where to select the invitation.
            This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises BadSignature: When the provided token has a bad signature.
        :raises GroupInvitationDoesNotExist: If the invitation does not exist.
        :return: The requested group invitation instance related to the provided token.
        :rtype: GroupInvitation
        """

        signer = self.get_group_invitation_signer()
        group_invitation_id = signer.loads(token)

        if base_queryset is None:
            base_queryset = GroupInvitation.objects

        try:
            group_invitation = base_queryset.select_related("group", "invited_by").get(
                id=group_invitation_id
            )
        except GroupInvitation.DoesNotExist:
            raise GroupInvitationDoesNotExist(
                f"The group invitation with id {group_invitation_id} does not exist."
            )

        return group_invitation

    def get_group_invitation(self, group_invitation_id, base_queryset=None):
        """
        Selects a group invitation with a given id from the database.

        :param group_invitation_id: The identifier of the invitation that must be
            returned.
        :type group_invitation_id: int
        :param base_queryset: The base queryset from where to select the invitation.
            This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises GroupInvitationDoesNotExist: If the invitation does not exist.
        :return: The requested field instance of the provided id.
        :rtype: GroupInvitation
        """

        if base_queryset is None:
            base_queryset = GroupInvitation.objects

        try:
            group_invitation = base_queryset.select_related("group", "invited_by").get(
                id=group_invitation_id
            )
        except GroupInvitation.DoesNotExist:
            raise GroupInvitationDoesNotExist(
                f"The group invitation with id {group_invitation_id} does not exist."
            )

        return group_invitation

    def create_group_invitation(
        self, user, group, email, permissions, base_url, message=""
    ):
        """
        Creates a new group invitation for the given email address and sends out an
        email containing the invitation.

        :param user: The user on whose behalf the invitation is created.
        :type user: User
        :param group: The group for which the user is invited.
        :type group: Group
        :param email: The email address of the person that is invited to the group.
            Can be an existing or not existing user.
        :type email: str
        :param permissions: The group permissions that the user will get once he has
            accepted the invitation.
        :type permissions: str
        :param base_url: The base url of the frontend, where the user can accept his
            invitation. The signed invitation id is appended to the URL (base_url +
            '/TOKEN'). Only the PUBLIC_WEB_FRONTEND_HOSTNAME is allowed as domain name.
        :type base_url: str
        :param message: A custom message that will be included in the invitation email.
        :type message: Optional[str]
        :raises ValueError: If the provided permissions are not allowed.
        :raises UserInvalidGroupPermissionsError: If the user does not belong to the
            group or doesn't have right permissions in the group.
        :return: The created group invitation.
        :rtype: GroupInvitation
        """

        CoreHandler().check_permissions(
            user, CreateInvitationsGroupOperationType.type, group=group, context=group
        )

        email = normalize_email_address(email)

        if GroupUser.objects.filter(group=group, user__email=email).exists():
            raise GroupUserAlreadyExists(
                f"The user {email} is already part of the " f"group."
            )

        invitation, _ = GroupInvitation.objects.update_or_create(
            group=group,
            email=email,
            defaults={
                "message": message,
                "permissions": permissions,
                "invited_by": user,
            },
        )

        self.send_group_invitation_email(invitation, base_url)

        return invitation

    def update_group_invitation(self, user, invitation, permissions):
        """
        Updates the permissions of an existing invitation if the user has ADMIN
        permissions to the related group.

        :param user: The user on whose behalf the invitation is updated.
        :type user: User
        :param invitation: The invitation that must be updated.
        :type invitation: GroupInvitation
        :param permissions: The new permissions of the invitation that the user must
            has after accepting.
        :type permissions: str
        :raises ValueError: If the provided permissions is not allowed.
        :raises UserInvalidGroupPermissionsError: If the user does not belong to the
            group or doesn't have right permissions in the group.
        :return: The updated group permissions instance.
        :rtype: GroupInvitation
        """

        CoreHandler().check_permissions(
            user,
            UpdateGroupInvitationType.type,
            group=invitation.group,
            context=invitation,
        )

        invitation.permissions = permissions
        invitation.save()

        return invitation

    def delete_group_invitation(self, user, invitation):
        """
        Deletes an existing group invitation if the user has ADMIN permissions to the
        related group.

        :param user: The user on whose behalf the invitation is deleted.
        :type user: User
        :param invitation: The invitation that must be deleted.
        :type invitation: GroupInvitation
        :raises UserInvalidGroupPermissionsError: If the user does not belong to the
            group or doesn't have right permissions in the group.
        """

        CoreHandler().check_permissions(
            user,
            DeleteGroupInvitationOperationType.type,
            group=invitation.group,
            context=invitation,
        )

        invitation.delete()

    def reject_group_invitation(self, user, invitation):
        """
        Rejects a group invitation by deleting the invitation so that can't be reused
        again. It can only be rejected if the invitation was addressed to the email
        address of the user.

        :param user: The user who wants to reject the invitation.
        :type user: User
        :param invitation: The invitation that must be rejected.
        :type invitation: GroupInvitation
        :raises GroupInvitationEmailMismatch: If the invitation email does not match
            the one of the user.
        """

        if user.username != invitation.email:
            raise GroupInvitationEmailMismatch(
                "The email address of the invitation does not match the one of the "
                "user."
            )

        invitation.delete()

    def add_user_to_group(
        self,
        group: Group,
        user: AbstractUser,
        permissions: str = GROUP_USER_PERMISSION_MEMBER,
    ) -> GroupUser:
        """
        Adds a user to the group by creating the appropriate `GroupUser`. If the user
        is already in the group, the permissions field is updated.

        :param group: the group in which we want to add the user.
        :param user: the user we want to add.
        :param permissions: the permissions of the user in this group. 'member' by
            default if not specified.
        :return: The created `GroupUser` object.
        """

        group_user, _ = GroupUser.objects.update_or_create(
            user=user,
            group=group,
            defaults={
                "order": GroupUser.get_last_order(user),
                "permissions": permissions,
            },
        )

        group_user_added.send(
            self, group_user_id=group_user.id, group_user=group_user, user=user
        )

        return group_user

    def accept_group_invitation(
        self, user: User, invitation: GroupInvitation
    ) -> GroupUser:
        """
        Accepts a group invitation by adding the user to the correct group with the
        right permissions. It can only be accepted if the invitation was addressed to
        the email address of the user. Because the invitation has been accepted it
        can then be deleted. If the user is already a member of the group then the
        permissions are updated.

        :param user: The user who has accepted the invitation.
        :param invitation: The invitation that must be accepted.
        :raises GroupInvitationEmailMismatch: If the invitation email does not match
            the one of the user.
        :return: The group user relationship related to the invite.
        """

        if user.username != invitation.email:
            raise GroupInvitationEmailMismatch(
                "The email address of the invitation does not match the one of the "
                "user."
            )

        group_user = self.add_user_to_group(
            invitation.group, user, permissions=invitation.permissions
        )

        invitation.delete()

        return group_user

    def get_user_application(
        self,
        user: AbstractUser,
        application_id: int,
        base_queryset: Optional[QuerySet] = None,
    ) -> Application:
        """
        Returns the application with the given id if the user has the right permissions.
        :param user: The user on whose behalf the application is requested.
        :param application_id: The identifier of the application that must be returned.
        :param base_queryset: The base queryset from where to select the application
            object. This can for example be used to do a `select_related`.
        :raises UserNotInGroup: If the user does not belong to the group of the
            application.
        :return: The requested application instance of the provided id.
        """

        application = self.get_application(application_id, base_queryset=base_queryset)

        CoreHandler().check_permissions(
            user,
            ReadApplicationOperationType.type,
            group=application.group,
            context=application,
        )

        return application

    def get_application(
        self, application_id: int, base_queryset: Optional[QuerySet] = None
    ) -> Application:
        """
        Selects an application with a given id from the database.

        :param application_id: The identifier of the application that must be returned.
        :param base_queryset: The base queryset from where to select the application
            object. This can for example be used to do a `select_related`.
        :raises ApplicationDoesNotExist: When the application with the provided id
            does not exist.
        :return: The requested application instance of the provided id.
        """

        if base_queryset is None:
            base_queryset = Application.objects

        try:
            application = base_queryset.select_related("group", "content_type").get(
                id=application_id
            )
        except Application.DoesNotExist:
            raise ApplicationDoesNotExist(
                f"The application with id {application_id} does not exist."
            )

        if TrashHandler.item_has_a_trashed_parent(application):
            raise ApplicationDoesNotExist(
                f"The application with id {application_id} does not exist."
            )

        return application

    def list_applications_in_group(
        self, group_id: int, base_queryset: Optional[QuerySet] = None
    ) -> QuerySet:
        """
        Return a list of applications in a group.

        :param group: The group to list the applications from.
        :param base_queryset: The base queryset from where to select the application
        :return: A list of applications in the group.
        """

        if base_queryset is None:
            base_queryset = Application.objects

        return base_queryset.filter(group_id=group_id, group__trashed=False)

    def create_application(
        self,
        user: AbstractUser,
        group: Group,
        type_name: str,
        name: str,
        init_with_data: bool = False,
    ) -> Application:
        """
        Creates a new application based on the provided type.

        :param user: The user on whose behalf the application is created.
        :param group: The group that the application instance belongs to.
        :param type_name: The type name of the application. ApplicationType can be
            registered via the ApplicationTypeRegistry.
        :param name: The name of the application.
        :param init_with_data: Whether the application should be initialized with
            some default data. Defaults to False.
        :return: The created application instance.
        """

        CoreHandler().check_permissions(
            user, CreateApplicationsGroupOperationType.type, group=group, context=group
        )

        application_type = application_type_registry.get(type_name)
        application = application_type.create_application(
            user, group, name, init_with_data
        )

        application_created.send(self, application=application, user=user)
        return application

    def find_unused_application_name(self, group_id: int, proposed_name: str) -> str:
        """
        Finds an unused name for an application.

        :param group_id: The group id that the application belongs to.
        :param proposed_name: The name that is proposed to be used.
        :return: A unique name to use.
        """

        existing_applications_names = self.list_applications_in_group(
            group_id
        ).values_list("name", flat=True)
        return find_unused_name(
            [proposed_name], existing_applications_names, max_length=255
        )

    def update_application(
        self, user: AbstractUser, application: Application, name: str
    ) -> Application:
        """
        Updates an existing application instance.

        :param user: The user on whose behalf the application is updated.
        :param application: The application instance that needs to be updated.
        :param name: The new name of the application.
        :return: The updated application instance.
        """

        CoreHandler().check_permissions(
            user,
            UpdateApplicationOperationType.type,
            group=application.group,
            context=application,
        )

        application.name = name
        application.save()

        application_updated.send(self, application=application, user=user)

        return application

    def duplicate_application(
        self,
        user: AbstractUser,
        application: Application,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> Application:
        """
        Duplicates an existing application instance.

        :param user: The user on whose behalf the application is duplicated.
        :param application: The application instance that needs to be duplicated.
        :return: The new (duplicated) application instance.
        """

        group = application.group

        CoreHandler().check_permissions(
            user,
            DuplicateApplicationOperationType.type,
            group=application.group,
            context=application,
        )

        start_progress, export_progress, import_progress = 10, 30, 60
        progress = ChildProgressBuilder.build(progress_builder, child_total=100)
        progress.increment(by=start_progress)

        # export the application
        specific_application = application.specific
        application_type = application_type_registry.get_by_model(specific_application)
        serialized = application_type.export_serialized(specific_application)
        progress.increment(by=export_progress)

        # Set a new unique name for the new application
        serialized["name"] = self.find_unused_application_name(
            group.id, serialized["name"]
        )
        serialized["order"] = application_type.model_class.get_last_order(group)

        # import it back as a new application
        id_mapping: Dict[str, Any] = {}
        new_application_clone = application_type.import_serialized(
            group,
            serialized,
            id_mapping,
            progress_builder=progress.create_child_builder(
                represents_progress=import_progress
            ),
        )

        # broadcast the application_created signal
        application_created.send(
            self,
            application=new_application_clone,
            user=user,
            type_name=application_type.type,
        )

        return new_application_clone

    def order_applications(
        self, user: AbstractUser, group: Group, order: List[int]
    ) -> List[int]:
        """
        Updates the order of the applications in the given group. The order of the
        applications that are not in the `order` parameter set to `0`.

        :param user: The user on whose behalf the tables are ordered.
        :param group: The group of which the applications must be updated.
        :param order: A list containing the application ids in the desired order.
        :raises ApplicationNotInGroup: If one of the applications ids in the order does
            not belong to the database.
        :return: The old order of application ids.
        """

        CoreHandler().check_permissions(
            user, OrderApplicationsOperationType.type, group=group, context=group
        )

        all_applications = Application.objects.filter(group_id=group.id).order_by(
            "order"
        )

        users_applications = CoreHandler().filter_queryset(
            user,
            OrderApplicationsOperationType.type,
            all_applications,
            group=group,
            context=group,
        )

        users_application_ids = users_applications.values_list("id", flat=True)

        # Check that all ordered ids can be ordered by the user
        for application_id in order:
            if application_id not in users_application_ids:
                raise ApplicationNotInGroup(application_id)

        new_order = Application.order_objects(all_applications, order)

        applications_reordered.send(self, group=group, order=new_order, user=user)

        return users_application_ids

    def delete_application(self, user: AbstractUser, application: Application):
        """
        Deletes an existing application instance if the user has access to the
        related group. The `application_deleted` signal is also called.

        :param user: The user on whose behalf the application is deleted.
        :param application: The application instance that needs to be deleted.
        :raises ValueError: If one of the provided parameters is invalid.
        """

        if not isinstance(application, Application):
            raise ValueError("The application is not an instance of Application")

        CoreHandler().check_permissions(
            user,
            DeleteApplicationOperationType.type,
            group=application.group,
            context=application,
        )

        application_id = application.id
        TrashHandler.trash(user, application.group, application, application)

        application_deleted.send(
            self, application_id=application_id, application=application, user=user
        )

    def export_group_applications(self, group, files_buffer, storage=None):
        """
        Exports the applications of a group to a list. They can later be imported via
        the `import_applications_to_group` method. The result can be serialized to JSON.

        @TODO look into speed optimizations by streaming to a JSON file instead of
            generating the entire file in memory.

        :param group: The group of which the applications must be exported.
        :type group: Group
        :param files_buffer: A file buffer where the files must be written to in ZIP
            format.
        :type files_buffer: IOBase
        :param storage: The storage where the files can be loaded from.
        :type storage: Storage or None
        :return: A list containing the exported applications.
        :rtype: list
        """

        if not storage:
            storage = default_storage

        with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
            exported_applications = []
            applications = group.application_set.all()
            for a in applications:
                application = a.specific
                application_type = application_type_registry.get_by_model(application)
                with application_type.export_safe_transaction_context(application):
                    exported_application = application_type.export_serialized(
                        application, files_zip, storage
                    )
                exported_applications.append(exported_application)

        return exported_applications

    def import_applications_to_group(
        self,
        group: Group,
        exported_applications: List[Dict[str, Any]],
        files_buffer: IO[bytes],
        storage: Optional[Storage] = None,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> Tuple[List[Application], Dict[str, Any]]:
        """
        Imports multiple exported applications into the given group. It is compatible
        with an export of the `export_group_applications` method.

        @TODO look into speed optimizations by streaming from a JSON file instead of
            loading the entire file into memory.

        :param group: The group that the applications must be imported to.
        :param exported_applications: A list containing the applications generated by
            the `export_group_applications` method.
        :param files_buffer: A file buffer containing the exported files in ZIP format.
        :param storage: The storage where the files can be copied to.
        :param progress_builder: If provided will be used to build a child progress bar
            and report on this methods progress to the parent of the progress_builder.
        :return: The newly created applications based on the import and a dict
            containing a mapping of old ids to new ids.
        """

        progress = ChildProgressBuilder.build(
            progress_builder, len(exported_applications) * 1000
        )

        if not storage:
            storage = default_storage

        with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
            id_mapping: Dict[str, Any] = {}
            imported_applications = []
            next_application_order_value = Application.get_last_order(group)
            for application in exported_applications:
                application_type = application_type_registry.get(application["type"])
                imported_application = application_type.import_serialized(
                    group,
                    application,
                    id_mapping,
                    files_zip,
                    storage,
                    progress_builder=progress.create_child_builder(
                        represents_progress=1000
                    ),
                )
                imported_application.order = next_application_order_value
                next_application_order_value += 1
                imported_applications.append(imported_application)
            Application.objects.bulk_update(imported_applications, ["order"])

        return imported_applications, id_mapping

    def get_template(self, template_id, base_queryset=None):
        """
        Selects a template with the given id from the database.

        :param template_id: The identifier of the template that must be returned.
        :type template_id: int
        :param base_queryset: The base queryset from where to select the group
            object. This can for example be used to do a `prefetch_related`.
        :type base_queryset: Queryset
        :raises TemplateDoesNotExist: When the group with the provided id does not
            exist.
        :return: The requested template instance related to the provided id.
        :rtype: Template
        """

        if base_queryset is None:
            base_queryset = Template.objects

        try:
            template = base_queryset.get(id=template_id)
        except Template.DoesNotExist:
            raise TemplateDoesNotExist(
                f"The template with id {template_id} does not " f"exist."
            )

        return template

    @transaction.atomic
    def sync_templates(self, storage=None):
        """
        Synchronizes the JSON template files with the templates stored in the database.
        We need to have a copy in the database so that the user can live preview a
        template before installing. It will also make sure that the right categories
        exist and that old ones are deleted.

        If the template doesn't exist, a group can be created and we can import the
        export in that group. If the template already exists we check if the
        `export_hash` has changed, if so it means the export has changed. Because we
        don't have updating capability, we delete the old group and create a new one
        where we can import the export into.

        :param storage:
        :type storage:
        """

        installed_templates = (
            Template.objects.all()
            .prefetch_related("categories")
            .select_related("group")
        )
        installed_categories = list(TemplateCategory.objects.all())

        # Loop over the JSON template files in the directory to see which database
        # templates need to be created or updated.
        templates = list(Path(settings.APPLICATION_TEMPLATES_DIR).glob("*.json"))
        for template_file_path in tqdm(
            templates,
            desc="Syncing Baserow templates. Disable by setting "
            "BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION=false.",
        ):
            content = Path(template_file_path).read_text()
            parsed_json = json.loads(content)

            if "baserow_template_version" not in parsed_json:
                continue

            slug = ".".join(template_file_path.name.split(".")[:-1])
            installed_template = next(
                (t for t in installed_templates if t.slug == slug), None
            )
            hash_json = json.dumps(parsed_json["export"])
            export_hash = hashlib.sha256(hash_json.encode("utf-8")).hexdigest()
            keywords = (
                ",".join(parsed_json["keywords"]) if "keywords" in parsed_json else ""
            )

            # If the installed template and group exist, and if there is a hash
            # mismatch, we need to delete the old group and all the related
            # applications in it. This is because a new group will be created.
            if (
                installed_template
                and installed_template.group
                and installed_template.export_hash != export_hash
            ):
                TrashHandler.permanently_delete(installed_template.group)

            # If the installed template does not yet exist or if there is a export
            # hash mismatch, which means the group has already been deleted, we can
            # create a new group and import the exported applications into that group.
            if not installed_template or installed_template.export_hash != export_hash:
                # It is optionally possible for a template to have additional files.
                # They are stored in a ZIP file and are generated when the template
                # is exported. They for example contain file field files.
                try:
                    files_file_path = f"{os.path.splitext(template_file_path)[0]}.zip"
                    files_buffer = open(files_file_path, "rb")
                except FileNotFoundError:
                    # If the file is not found, we provide a BytesIO buffer to
                    # maintain backward compatibility and to not brake anything.
                    files_buffer = BytesIO()

                group = Group.objects.create(name=parsed_json["name"])
                self.import_applications_to_group(
                    group,
                    parsed_json["export"],
                    files_buffer=files_buffer,
                    storage=storage,
                )

                if files_buffer:
                    files_buffer.close()
            else:
                group = installed_template.group
                group.name = parsed_json["name"]
                group.save()

            kwargs = {
                "name": parsed_json["name"],
                "icon": parsed_json["icon"],
                "export_hash": export_hash,
                "keywords": keywords,
                "group": group,
            }

            if not installed_template:
                installed_template = Template.objects.create(slug=slug, **kwargs)
            else:
                # If the installed template already exists, we only need to update the
                # values to the latest version according to the JSON template.
                for key, value in kwargs.items():
                    setattr(installed_template, key, value)
                installed_template.save()

            # Loop over the categories related to the template and check which ones
            # already exist and which need to be created. Based on that we can create
            # a list of category ids that we can set for the template.
            template_category_ids = []
            for category_name in parsed_json["categories"]:
                installed_category = next(
                    (c for c in installed_categories if c.name == category_name), None
                )
                if not installed_category:
                    installed_category = TemplateCategory.objects.create(
                        name=category_name
                    )
                    installed_categories.append(installed_category)
                template_category_ids.append(installed_category.id)

            installed_template.categories.set(template_category_ids)

        # Delete all the installed templates that were installed, but don't exist in
        # the template directory anymore.
        slugs = [
            ".".join(template_file_path.name.split(".")[:-1])
            for template_file_path in templates
        ]
        for template in Template.objects.filter(~Q(slug__in=slugs)):
            TrashHandler.permanently_delete(template.group)
            template.delete()

        # Delete all the categories that don't have any templates anymore.
        TemplateCategory.objects.annotate(num_templates=Count("templates")).filter(
            num_templates=0
        ).delete()

    def get_valid_template_path_or_raise(self, template):

        file_name = f"{template.slug}.json"
        template_path = Path(
            os.path.join(settings.APPLICATION_TEMPLATES_DIR, file_name)
        )

        if not template_path.exists():
            raise TemplateFileDoesNotExist(
                f"The template with file name {file_name} does not exist. You might "
                f"need to run the `sync_templates` management command."
            )
        return template_path

    def install_template(
        self,
        user: AbstractUser,
        group: Group,
        template: Template,
        storage: Optional[Storage] = None,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> Tuple[List[Application], Dict[str, Any]]:
        """
        Installs the exported applications of a template into the given group if the
        provided user has access to that group.

        :param user: The user on whose behalf the template installed.
        :param group: The group where the template applications must be imported into.
        :param template: The template that must be installed.
        :param storage: The storage where the files can be copied to.
        :return: The imported applications.
        """

        CoreHandler().check_permissions(
            user, CreateApplicationsGroupOperationType.type, group=group, context=group
        )

        template_path = self.get_valid_template_path_or_raise(template)

        content = template_path.read_text()
        parsed_json = json.loads(content)

        # It is optionally possible for a template to have additional files. They are
        # stored in a ZIP file and are generated when the template is exported. They
        # for example contain file field files.
        try:
            files_path = f"{os.path.splitext(template_path)[0]}.zip"
            files_buffer = open(files_path, "rb")
        except FileNotFoundError:
            # If the file is not found, we provide a BytesIO buffer to
            # maintain backward compatibility and to not brake anything.
            files_buffer = BytesIO()

        applications, id_mapping = self.import_applications_to_group(
            group,
            parsed_json["export"],
            files_buffer=files_buffer,
            storage=storage,
            progress_builder=progress_builder,
        )

        if files_buffer:
            files_buffer.close()

        # Because a user has initiated the creation of applications, we need to
        # call the `application_created` signal for each created application.
        for application in applications:
            application_type = application_type_registry.get_by_model(application)
            application.installed_from_template = template
            application_created.send(
                self,
                application=application,
                user=user,
                type_name=application_type.type,
            )

        Application.objects.bulk_update(applications, ["installed_from_template"])

        return applications, id_mapping
