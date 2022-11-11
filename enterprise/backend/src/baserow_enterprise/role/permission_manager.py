from collections import defaultdict
from functools import cached_property, cmp_to_key
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict, Union

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType

from baserow_premium.license.handler import LicenseHandler
from rest_framework.exceptions import NotAuthenticated

from baserow.contrib.database.object_scopes import DatabaseObjectScopeType
from baserow.contrib.database.table.object_scopes import DatabaseTableObjectScopeType
from baserow.core.exceptions import PermissionDenied
from baserow.core.models import Group, Operation
from baserow.core.object_scopes import GroupObjectScopeType
from baserow.core.registries import (
    OperationType,
    PermissionManagerType,
    object_scope_type_registry,
    operation_type_registry,
)
from baserow_enterprise.features import RBAC
from baserow_enterprise.models import Team
from baserow_enterprise.role.handler import RoleAssignmentHandler

from .models import RoleAssignment
from .operations import (
    AssignRoleGroupOperationType,
    ReadRoleDatabaseOperationType,
    ReadRoleGroupOperationType,
    ReadRoleTableOperationType,
    UpdateRoleDatabaseOperationType,
    UpdateRoleTableOperationType,
)

User = get_user_model()


def compare_scopes(a, b):
    a_includes_b = object_scope_type_registry.scope_includes_scope(a[0], b[0])
    b_includes_a = object_scope_type_registry.scope_includes_scope(b[0], a[0])

    if a_includes_b and b_includes_a:
        return 0
    if a_includes_b:
        return -1
    if b_includes_a:
        return 1


class OperationPermissionContent(TypedDict):
    default: bool
    exceptions: List[int]


class RolePermissionManagerType(PermissionManagerType):
    type = "role"
    _role_cache: Dict[int, List[str]] = {}
    role_assignable_object_map = {
        GroupObjectScopeType.type: {
            "READ": ReadRoleGroupOperationType,
            "UPDATE": AssignRoleGroupOperationType,
        },
        DatabaseObjectScopeType.type: {
            "READ": ReadRoleDatabaseOperationType,
            "UPDATE": UpdateRoleDatabaseOperationType,
        },
        DatabaseTableObjectScopeType.type: {
            "READ": ReadRoleTableOperationType,
            "UPDATE": UpdateRoleTableOperationType,
        },
    }

    def is_enabled(self, group: Group):
        """
        Checks whether this permission manager should be enabled or not for a
        particular group.

        :param group: The group in which we want to use this permission manager.
        """

        return LicenseHandler.group_has_feature(RBAC, group)

    def get_user_role_assignments(
        self, group: Group, actor: Union[AbstractUser, Team]
    ) -> List[Tuple[Any, List[str]]]:
        """
        Returns the RoleAssignments for the given actor in the given group.

        :param group: The group the RoleAssignments belong to.
        :param actor: The subject for whom we want the RoleAssignments
        :param operation: An optional Operation to select only roles containing this
            operation.
        :return: A list of tuple containing the role_id and the scope ordered by scope.
            The higher a scope is high in the object hierarchy, the higher the tuple in
            the list.
        """

        roles = RoleAssignment.objects.filter(
            group=group,
            subject_type=ContentType.objects.get_for_model(User),
            subject_id=actor.id,
        )
        # TODO: query for roles within teams.

        # TODO n-queries here.
        result = [(r.scope, self.get_role_operations(r.role_id)) for r in roles]

        # Get the group level role by reading the GroupUser permissions property
        group_level_role = RoleAssignmentHandler().get_role(
            group.get_group_user(actor).permissions
        )

        result += [
            (
                group,
                self.get_role_operations(group_level_role.id),
            )
        ]

        result_as_dict = defaultdict(set)

        # Merge multiple permission sets at same scope level useful for team
        for (scope, op) in result:
            result_as_dict[scope] |= set(op)

        result = list(result_as_dict.items())

        # TODO Potentially doing n-queries.
        # Roles are ordered by scope size. The higher in the hierarchy, the higher
        # in the list.
        result.sort(key=cmp_to_key(compare_scopes))

        return result

    def get_role_operations(self, role_id: int) -> List[str]:
        """
        Return the operation list for the role with the given role_id. This method is
        memoized.

        :param role_id: The role ID we want the operations for.
        :return: A list of role operation name.
        """

        if role_id not in self._role_cache:
            self._role_cache[role_id] = list(
                Operation.objects.filter(roles=role_id).values_list("name", flat=True)
            )

        return self._role_cache[role_id]

    @cached_property
    def read_operations(self) -> List[str]:
        """
        Return the read operation list.
        """

        return set(
            Operation.objects.filter(roles__uid="VIEWER").values_list("name", flat=True)
        )

    def check_permissions(
        self,
        actor: AbstractUser,
        operation_name: str,
        group: Optional[Group] = None,
        context: Optional[Any] = None,
        include_trash: bool = False,
    ):
        """
        Checks the permissions given the roles assigned to the actor.
        """

        if group is None or not self.is_enabled(group):
            return

        if hasattr(actor, "is_authenticated"):

            user = actor
            if not user.is_authenticated:
                raise NotAuthenticated()

            if (
                group.get_group_user(user, include_trash=include_trash).permissions
                == "ADMIN"
            ):
                return True

            operation_type = operation_type_registry.get(operation_name)

            # Get all role assignments for this user into this group
            role_assignments = self.get_user_role_assignments(group, user)

            most_precise_role = set()

            for (scope, allowed_operations) in role_assignments:
                # Check if this scope include the context. As the role assignments are
                # Sorted, the new scope is more precise than the previous one. So
                # we keep this new role.
                if object_scope_type_registry.scope_includes_context(scope, context):
                    most_precise_role = allowed_operations
                elif (
                    object_scope_type_registry.scope_includes_context(context, scope)
                    and allowed_operations
                ):
                    most_precise_role |= self.read_operations

            if operation_type.type in most_precise_role:
                return True

            raise PermissionDenied()

    def get_operation_policy(
        self,
        role_assignments: List[Tuple[Any, List[str]]],
        operation_type: OperationType,
        use_object_scope: bool = False,
    ) -> Tuple[bool, Set[Any]]:
        """
        Compute the default policy and exceptions for an operation given the
        role assignments.

        :param role_assignments: The role assignments used to compute the policy.
        :param operation_type: The operation type we want the policy for.
        :param use_object_scope: Use the `object_scope` instead of the `context_scope`
            of the scope_type. This change the type of returned objects.
        :return: A tuple. The first element is the default policy. The second element
            is a set of context or object that are exceptions to the default policy.
        """

        default = False
        exceptions = set([])

        base_scope = (
            operation_type.object_scope
            if use_object_scope
            else operation_type.context_scope
        )

        for (scope, allowed_operations) in role_assignments:

            scope_type = object_scope_type_registry.get_by_model(scope)

            if object_scope_type_registry.scope_includes_scope(scope_type, base_scope):

                # Default permission at the group level
                if scope_type.type == GroupObjectScopeType.type:
                    if operation_type.type in allowed_operations:
                        default = True
                    continue

                context_exceptions = list(
                    base_scope.get_all_context_objects_in_scope(scope)
                )

                # Remove or add exceptions to the exception list according to the
                # default policy for the group

                if operation_type.type not in allowed_operations:
                    if default:
                        exceptions |= set(context_exceptions)
                    else:
                        exceptions = exceptions.difference(context_exceptions)
                else:
                    if default:
                        exceptions = exceptions.difference(context_exceptions)
                    else:
                        exceptions |= set(context_exceptions)
            elif (
                operation_type.type in self.read_operations
                and allowed_operations
                and object_scope_type_registry.scope_includes_scope(
                    base_scope, scope_type
                )
            ):
                # - It's a read operation and
                # - we have a children that have at least one allowed operation
                # -> we should then allow all read operations for all ancestors of
                # this scope object.
                found_object = scope
                while not base_scope.contains(found_object):
                    found_object = object_scope_type_registry.get_parent(found_object)

                if default:
                    if found_object in exceptions:
                        exceptions.remove(found_object)
                else:
                    exceptions.add(found_object)

        return default, exceptions

    # Probably needs a cache?
    def get_permissions_object(
        self, actor: AbstractUser, group: Optional[Group] = None
    ) -> List[Dict[str, OperationPermissionContent]]:
        """
        Returns the permission object for this permission manager. The permission object
        looks like this:
        ```
        {
            "operation_name1": {"default": True, "exceptions": [3, 5]},
            "operation_name2": {"default": False, "exceptions": [12, 18]},
            ...
        }
        ```
        where `permission_name1` is the name of an operation and for each operation, if
        the operation is permitted by default or not and `exceptions` contains the list
        of context IDs that are an exception to the default rule.
        """

        if group is None or not self.is_enabled(group):
            return None

        if group.get_group_user(actor).permissions == "ADMIN":
            return {
                op.type: {"default": True, "exceptions": []}
                for op in operation_type_registry.get_all()
            }

        # Get all role assignments for this actor into this group
        role_assignments = self.get_user_role_assignments(group, actor)

        result = defaultdict(lambda: {"default": False, "exceptions": []})

        for operation_type in operation_type_registry.get_all():

            default, exceptions = self.get_operation_policy(
                role_assignments, operation_type
            )

            if default or exceptions:
                result[operation_type.type]["default"] = default
                result[operation_type.type]["exceptions"] = [e.id for e in exceptions]

        return result

    def filter_queryset(
        self, actor, operation_name, queryset, group=None, context=None
    ):
        """
        Filter the given queryset according to the role given for the specified
        operation.
        """

        if group is None or not self.is_enabled(group):
            return queryset

        # Admin bypass
        if group.get_group_user(actor).permissions == "ADMIN":
            return queryset

        # Get all role assignments for this user into this group
        role_assignments = self.get_user_role_assignments(group, actor)

        operation_type = operation_type_registry.get(operation_name)

        default, exceptions = self.get_operation_policy(
            role_assignments, operation_type, True
        )

        exceptions = [e.id for e in exceptions]

        # Finally filter the queryset with the exception list.
        if default:
            if exceptions:
                queryset = queryset.exclude(id__in=list(exceptions))
        else:
            if exceptions:
                queryset = queryset.filter(id__in=list(exceptions))
            else:
                queryset = queryset.none()

        return queryset
